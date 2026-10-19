"""Unit tests for incident-bridge enrichment, dedupe, size cap, and auth headers."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx
import pytest

from evidence import collect_agent_activity, redact_secrets, summarize_matrix
from forwarding import (
    DedupeCache,
    FailedForwardQueue,
    build_auth_headers,
    cap_payload,
    post_with_retry,
    redact_headers,
    write_dead_letter,
)
from settings import Settings

import app as bridge


def _settings(**overrides) -> Settings:
    base = dict(
        grok_webhook_url="https://example.invalid/diagnose",
        grok_webhook_key="test-webhook-key",
        grok_webhook_auth_header="Authorization",
        grok_webhook_auth_scheme="Bearer",
        prometheus_url="http://prometheus:9090",
        agent_activity_log="/tmp/missing-agent-activity.jsonl",
        evidence_window_seconds=600,
        payload_max_bytes=100 * 1024,
        dedupe_ttl_seconds=300,
        webhook_timeout_seconds=2.0,
        webhook_max_retries=3,
        log_tail_lines=20,
        k8s_enabled=False,
    )
    base.update(overrides)
    return Settings(**base)


def test_auth_header_bearer_and_empty_scheme():
    assert build_auth_headers("abc", "Authorization", "Bearer") == {"Authorization": "Bearer abc"}
    assert build_auth_headers("abc", "X-Api-Key", "") == {"X-Api-Key": "abc"}
    assert build_auth_headers("abc", "X-Api-Key", "   ") == {"X-Api-Key": "abc"}
    assert build_auth_headers("", "Authorization", "Bearer") == {}


def test_auth_scheme_env_allows_empty(monkeypatch):
    monkeypatch.setenv("GROK_WEBHOOK_AUTH_SCHEME", "")
    monkeypatch.setenv("GROK_WEBHOOK_AUTH_HEADER", "X-Bot-Key")
    monkeypatch.setenv("GROK_WEBHOOK_KEY", "raw-key")
    cfg = Settings.from_env()
    assert cfg.grok_webhook_auth_scheme == ""
    assert build_auth_headers(cfg.grok_webhook_key, cfg.grok_webhook_auth_header, cfg.grok_webhook_auth_scheme) == {
        "X-Bot-Key": "raw-key"
    }


def test_auth_scheme_defaults_to_bearer_when_unset(monkeypatch):
    monkeypatch.delenv("GROK_WEBHOOK_AUTH_SCHEME", raising=False)
    cfg = Settings.from_env()
    assert cfg.grok_webhook_auth_scheme == "Bearer"


def test_dedupe_same_fingerprint_and_status():
    clock = {"t": 0.0}

    def now():
        return clock["t"]

    cache = DedupeCache(ttl_seconds=300, clock=now)
    alert = {"fingerprint": "fp1", "status": "firing", "labels": {"alertname": "ServiceDown"}}
    assert cache.filter_new([alert]) == [alert]
    cache.remember_alerts([alert])
    assert cache.filter_new([alert]) == []

    clock["t"] = 299
    assert cache.filter_new([alert]) == []

    resolved = dict(alert, status="resolved")
    assert cache.filter_new([resolved]) == [resolved]

    clock["t"] = 300
    assert cache.filter_new([alert]) == [alert]


def test_payload_size_cap_strips_evidence():
    huge_logs = [{"line": "x" * 5000} for _ in range(80)]
    payload = {
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "ServiceDown", "service": "api-gw"},
                "annotations": {"description": "d" * 5000},
                "fingerprint": "fp",
                "startsAt": "2026-10-18T00:00:00Z",
                "endsAt": None,
            }
        ],
        "evidence": {
            "prometheus": [{"name": "up", "query": "up", "series": [{"labels": {}, "samples": 20}]}],
            "agent_activity": huge_logs,
            "k8s_events": [{"message": "m" * 4000} for _ in range(20)],
        },
        "source": "resilienceops",
    }
    capped = cap_payload(payload, max_bytes=8 * 1024)
    raw = json.dumps(capped, separators=(",", ":")).encode("utf-8")
    assert len(raw) <= 8 * 1024
    assert capped["source"] == "resilienceops"
    assert capped["alerts"]
    evidence = capped.get("evidence") or {}
    assert evidence.get("_truncated") is True


def test_redact_secrets_from_evidence_and_headers():
    dirty = {
        "ANTHROPIC_API_KEY": "sk-ant-testdata-value",
        "note": "Authorization: Bearer super-secret-token",
        "nested": {"password": "hunter2", "ok": "value"},
    }
    cleaned = redact_secrets(dirty)
    blob = json.dumps(cleaned)
    assert "sk-ant-testdata-value" not in blob
    assert "super-secret-token" not in blob
    assert "hunter2" not in blob
    assert cleaned["nested"]["password"] == "***"
    assert cleaned["nested"]["ok"] == "value"
    assert redact_headers({"Authorization": "Bearer abc", "X-Request-Id": "1"}) == {
        "Authorization": "***",
        "X-Request-Id": "1",
    }


def test_summarize_matrix_has_no_raw_values():
    raw = [
        {
            "metric": {"job": "api-gw"},
            "values": [[1, "1.0"], [2, "3.0"], [3, "2.0"]],
        }
    ]
    summary = summarize_matrix(raw)
    assert summary[0]["samples"] == 3
    assert summary[0]["min"] == 1.0
    assert summary[0]["max"] == 3.0
    assert summary[0]["last"] == 2.0
    assert "values" not in summary[0]


def test_agent_activity_tail_redacts(tmp_path: Path):
    log = tmp_path / "agent_activity.jsonl"
    log.write_text(
        json.dumps({"action": "inject", "token": "should-hide", "ok": True}) + "\n"
        + json.dumps({"action": "heal", "note": "Bearer abcdefghijklmnopqrstuv"}) + "\n",
        encoding="utf-8",
    )
    records = collect_agent_activity(str(log), max_lines=10)
    blob = json.dumps(records)
    assert "should-hide" not in blob
    assert "abcdefghijklmnopqrstuv" not in blob
    assert any(item.get("action") == "heal" for item in records)


def test_process_webhook_forwards_enriched_payload(monkeypatch):
    captured = {}

    def fake_evidence(**kwargs):
        return {"prometheus": [{"name": "up", "series": [{"samples": 1, "last": 1}]}], "agent_activity": []}

    def fake_forward(url, payload, headers=None, **kwargs):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        return httpx.Response(200, request=httpx.Request("POST", url))

    cache = DedupeCache(ttl_seconds=300)
    payload = {
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "ServiceDown", "service": "api-gw", "severity": "critical"},
                "annotations": {"summary": "down"},
                "fingerprint": "abcd",
                "startsAt": "2026-10-18T00:00:00Z",
                "endsAt": "0001-01-01T00:00:00Z",
            }
        ],
    }
    result = bridge.process_webhook(
        payload,
        settings_obj=_settings(),
        dedupe_cache=cache,
        forward=fake_forward,
        evidence_fn=fake_evidence,
        retry_queue=FailedForwardQueue(),
    )
    assert result == "forwarded"
    assert captured["url"] == "https://example.invalid/diagnose"
    assert captured["headers"] == {"Authorization": "Bearer test-webhook-key"}
    body = captured["payload"]
    assert body["source"] == "resilienceops"
    assert body["status"] == "firing"
    assert body["alerts"][0]["fingerprint"] == "abcd"
    assert "labels" in body["alerts"][0]
    assert "evidence" in body
    assert cache.filter_new(payload["alerts"]) == []

    again = bridge.process_webhook(
        payload,
        settings_obj=_settings(),
        dedupe_cache=cache,
        forward=fake_forward,
        evidence_fn=fake_evidence,
        retry_queue=FailedForwardQueue(),
    )
    assert again == "dropped_duplicate"


def test_process_webhook_drops_when_url_unset():
    called = {"n": 0}

    def boom(*args, **kwargs):
        called["n"] += 1
        raise AssertionError("should not forward")

    result = bridge.process_webhook(
        {"status": "firing", "alerts": [{"status": "firing", "fingerprint": "x"}]},
        settings_obj=_settings(grok_webhook_url=""),
        dedupe_cache=DedupeCache(),
        forward=boom,
        evidence_fn=lambda **kwargs: {},
        retry_queue=FailedForwardQueue(),
    )
    assert result == "dropped_unconfigured"
    assert called["n"] == 0


def test_process_webhook_never_logs_key(caplog):
    caplog.set_level(logging.INFO)

    def fake_forward(url, payload, headers=None, **kwargs):
        return httpx.Response(200, request=httpx.Request("POST", url))

    bridge.process_webhook(
        {"status": "firing", "alerts": [{"status": "firing", "fingerprint": "z", "labels": {}}]},
        settings_obj=_settings(grok_webhook_key="test-webhook-key"),
        dedupe_cache=DedupeCache(),
        forward=fake_forward,
        evidence_fn=lambda **kwargs: {"agent_activity": [{"note": "ok"}]},
        retry_queue=FailedForwardQueue(),
    )
    joined = "\n".join(record.getMessage() for record in caplog.records)
    assert "test-webhook-key" not in joined
    assert "Bearer test-webhook-key" not in joined


def test_post_with_retry_backoff(monkeypatch):
    sleeps = []
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] < 3:
            return httpx.Response(503, request=request)
        return httpx.Response(200, request=request)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    response = post_with_retry(
        "https://example.invalid/hook",
        {"ok": True},
        headers={"Authorization": "Bearer test-webhook-key"},
        timeout_seconds=1.0,
        max_retries=3,
        client=client,
        sleep=sleeps.append,
    )
    assert response.status_code == 200
    assert attempts["n"] == 3
    assert sleeps == [0.5, 1.0]


def test_post_with_retry_does_not_retry_client_errors():
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        return httpx.Response(401, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        post_with_retry(
            "https://example.invalid/hook",
            {"ok": True},
            timeout_seconds=1.0,
            max_retries=3,
            client=client,
            sleep=lambda _delay: None,
        )
    assert attempts["n"] == 1


def test_healthz_and_webhook_accept(monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(bridge, "process_webhook", lambda payload: "forwarded")
    client = TestClient(bridge.app)
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    posted = client.post("/webhook", json={"status": "firing", "alerts": []})
    assert posted.status_code == 200
    assert posted.json()["accepted"] is True


def test_process_webhook_logs_forward_failed_and_does_not_raise(tmp_path: Path, caplog):
    caplog.set_level(logging.ERROR)
    attempts = {"n": 0}

    def boom(url, payload, headers=None, **kwargs):
        attempts["n"] += 1
        raise httpx.ConnectTimeout("timed out", request=httpx.Request("POST", url))

    queue = FailedForwardQueue(max_items=4)
    log_path = tmp_path / "agent_activity.jsonl"
    payload = {
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "RedisConnectionSaturation", "service": "order-service"},
                "annotations": {"summary": "pool full"},
                "fingerprint": "fp-fail",
            }
        ],
    }
    result = bridge.process_webhook(
        payload,
        settings_obj=_settings(agent_activity_log=str(log_path)),
        dedupe_cache=DedupeCache(),
        forward=boom,
        evidence_fn=lambda **kwargs: {"agent_activity": []},
        retry_queue=queue,
    )
    assert result == "forward_failed"
    assert attempts["n"] == 1
    assert len(queue) == 1
    joined = "\n".join(record.getMessage() for record in caplog.records)
    assert "forward FAILED after 3 attempts" in joined
    assert "alertname=RedisConnectionSaturation" in joined
    assert "fingerprint=fp-fail" in joined
    assert "test-webhook-key" not in joined
    dead = tmp_path / "bridge_deadletter.jsonl"
    assert dead.is_file()
    body = dead.read_text(encoding="utf-8")
    assert "test-webhook-key" not in body
    assert "RedisConnectionSaturation" in body
    assert "Bearer " not in body


def test_failed_forward_queue_is_bounded_and_retried(tmp_path: Path):
    queue = FailedForwardQueue(max_items=2)
    for i in range(5):
        queue.push({"alerts": [{"fingerprint": str(i), "labels": {"alertname": f"A{i}"}}], "source": "resilienceops"}, "ConnectTimeout")
    assert len(queue) == 2
    first = queue.pop()
    assert first["payload"]["alerts"][0]["fingerprint"] == "3"

    forwarded = []

    def succeed_then_noop(url, payload, headers=None, **kwargs):
        forwarded.append(payload)
        return httpx.Response(200, request=httpx.Request("POST", url))

    # Next inbound webhook should drain the remaining queued item first.
    result = bridge.process_webhook(
        {
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "ServiceDown", "service": "api-gw"},
                    "fingerprint": "fresh",
                }
            ],
        },
        settings_obj=_settings(agent_activity_log=str(tmp_path / "agent_activity.jsonl")),
        dedupe_cache=DedupeCache(),
        forward=succeed_then_noop,
        evidence_fn=lambda **kwargs: {},
        retry_queue=queue,
    )
    assert result == "forwarded"
    assert any(item.get("alerts", [{}])[0].get("fingerprint") == "4" for item in forwarded)
    assert any(item.get("alerts", [{}])[0].get("fingerprint") == "fresh" for item in forwarded)
    assert len(queue) == 0


def test_write_dead_letter_omits_webhook_key(tmp_path: Path):
    path = write_dead_letter(
        str(tmp_path / "agent_activity.jsonl"),
        {
            "status": "firing",
            "alerts": [{"labels": {"alertname": "ServiceDown"}, "fingerprint": "x"}],
            "evidence": {"note": "ok"},
            "source": "resilienceops",
        },
        "ConnectTimeout",
        3,
    )
    assert path is not None
    text = path.read_text(encoding="utf-8")
    assert "GROK_WEBHOOK" not in text
    assert "Authorization" not in text
    assert "ConnectTimeout" in text
