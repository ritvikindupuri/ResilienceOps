"""logutil state dir, --via-ssm forwarding, poller failure comments, .env load."""

from __future__ import annotations

import os

from remediation import envload, logutil, poll_and_apply, remediate
from remediation.actions import Proposal


def test_emit_writes_under_remediation_state_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("REMEDIATION_STATE_DIR", str(tmp_path))
    logutil.emit({"event": "unit-test"})
    dest = tmp_path / "remediation.jsonl"
    assert dest.is_file()
    assert "unit-test" in dest.read_text(encoding="utf-8")


def test_via_ssm_forwards_verify_timeout(monkeypatch):
    captured: list[str] = []

    def fake_via(argv: list[str]) -> int:
        captured.extend(argv)
        return 0

    monkeypatch.setattr(remediate, "_via_ssm", fake_via)
    code = remediate.main(
        [
            "--via-ssm",
            "--action",
            "reset_fault",
            "--target",
            "both",
            "--verify-timeout",
            "12",
        ]
    )
    assert code == 0
    assert captured[captured.index("--verify-timeout") + 1] == "12"


def test_via_ssm_returns_2_when_send_and_wait_fails(monkeypatch):
    monkeypatch.setattr(remediate, "emit", lambda *_a, **_k: None)

    def boom(*_a, **_k):
        raise SystemExit("SSM command abc ended with status=Failed")

    class FakeBoto:
        def client(self, *_a, **_k):
            return object()

    monkeypatch.setitem(__import__("sys").modules, "boto3", FakeBoto())
    monkeypatch.setattr("agents.config.require_ec2_instance_id", lambda: "i-test")
    monkeypatch.setattr("deploy_remote.resolve_region", lambda _x: "us-east-1")
    monkeypatch.setattr("deploy_remote.send_and_wait", boom)
    assert remediate._via_ssm(["--action", "reset_fault", "--target", "both"]) == 2


def test_poller_posts_failure_comment_when_ssm_raises(monkeypatch):
    comments: list[str] = []

    monkeypatch.setattr(poll_and_apply, "github_repository", lambda: "owner/repo")
    monkeypatch.setattr(
        poll_and_apply,
        "list_issue_comments",
        lambda *_a, **_k: [
            {
                "body": (
                    "<!-- resilienceops-approval:v1 -->\n"
                    "action: reset_fault\n"
                    "target: order-service\n"
                    "actor: owner\n"
                    "<!-- /resilienceops-approval -->\n"
                )
            }
        ],
    )
    monkeypatch.setattr(
        poll_and_apply,
        "parse_recorded_approval",
        lambda _body: {"action": "reset_fault", "target": "order-service"},
    )
    monkeypatch.setattr(
        poll_and_apply,
        "validate_proposal_fields",
        lambda action, target: Proposal(action, target),
    )
    monkeypatch.setattr(poll_and_apply, "emit", lambda *_a, **_k: None)

    def boom(_argv):
        raise SystemExit("SSM command abc ended with status=Failed")

    monkeypatch.setattr(poll_and_apply, "remediate_main", boom)
    monkeypatch.setattr(
        poll_and_apply, "add_issue_comment", lambda _repo, _n, body: comments.append(body)
    )
    monkeypatch.setattr(poll_and_apply, "add_issue_labels", lambda *_a, **_k: None)
    poll_and_apply._apply_one(
        {"number": 9}, dry_run=False, via_ssm=True, verify_timeout=45
    )
    assert comments
    assert "ok: false" in comments[0]
    assert "reset_fault" in comments[0]


def test_load_remediation_env_reads_repo_dotenv(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    (tmp_path / ".env").write_text(
        "GITHUB_TOKEN=from-dotenv\nGITHUB_REPOSITORY=owner/from-dotenv\n",
        encoding="utf-8",
    )
    loaded = envload.load_remediation_env(root=tmp_path)
    assert loaded
    assert os.getenv("GITHUB_TOKEN") == "from-dotenv"
    assert os.getenv("GITHUB_REPOSITORY") == "owner/from-dotenv"


def test_load_remediation_env_does_not_override(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "already-set")
    (tmp_path / ".env").write_text("GITHUB_TOKEN=from-dotenv\n", encoding="utf-8")
    envload.load_remediation_env(root=tmp_path)
    assert os.getenv("GITHUB_TOKEN") == "already-set"


def test_load_remediation_env_reads_host_path(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    host = tmp_path / "host.env"
    host.write_text("GITHUB_REPOSITORY=ec2/lab\n", encoding="utf-8")
    envload.load_remediation_env(root=tmp_path / "missing", extra=[host])
    assert os.getenv("GITHUB_REPOSITORY") == "ec2/lab"


def test_poller_main_loads_dotenv(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    (tmp_path / ".env").write_text("GITHUB_REPOSITORY=owner/from-poller\n", encoding="utf-8")
    monkeypatch.setattr(poll_and_apply, "load_remediation_env", lambda: envload.load_remediation_env(root=tmp_path))
    monkeypatch.setattr(poll_and_apply, "github_repository", lambda: os.environ["GITHUB_REPOSITORY"])
    monkeypatch.setattr(poll_and_apply, "list_labeled_issues", lambda *_a, **_k: [])
    assert poll_and_apply.main(["--once"]) == 0
    assert os.getenv("GITHUB_REPOSITORY") == "owner/from-poller"
