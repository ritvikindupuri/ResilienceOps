"""Runtime configuration for the incident bridge. Loaded entirely from env vars."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _auth_scheme() -> str:
    # Present-but-empty must stay empty so operators can send a bare header value.
    if "GROK_WEBHOOK_AUTH_SCHEME" in os.environ:
        return os.environ["GROK_WEBHOOK_AUTH_SCHEME"]
    return "Bearer"


@dataclass(frozen=True)
class Settings:
    grok_webhook_url: str
    grok_webhook_key: str
    grok_webhook_auth_header: str
    grok_webhook_auth_scheme: str
    prometheus_url: str
    agent_activity_log: str
    evidence_window_seconds: int
    payload_max_bytes: int
    dedupe_ttl_seconds: int
    webhook_timeout_seconds: float
    webhook_max_retries: int
    log_tail_lines: int
    k8s_enabled: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            grok_webhook_url=os.getenv("GROK_WEBHOOK_URL", "").strip(),
            grok_webhook_key=os.getenv("GROK_WEBHOOK_KEY", ""),
            grok_webhook_auth_header=os.getenv("GROK_WEBHOOK_AUTH_HEADER", "Authorization") or "Authorization",
            grok_webhook_auth_scheme=_auth_scheme(),
            prometheus_url=os.getenv("PROMETHEUS_URL", "http://prometheus:9090").rstrip("/"),
            agent_activity_log=os.getenv("AGENT_ACTIVITY_LOG", "/app/logs/agent_activity.jsonl"),
            evidence_window_seconds=_env_int("EVIDENCE_WINDOW_SECONDS", 600),
            payload_max_bytes=_env_int("PAYLOAD_MAX_BYTES", 100 * 1024),
            dedupe_ttl_seconds=_env_int("DEDUPE_TTL_SECONDS", 300),
            webhook_timeout_seconds=_env_float("WEBHOOK_TIMEOUT_SECONDS", 10.0),
            webhook_max_retries=_env_int("WEBHOOK_MAX_RETRIES", 3),
            log_tail_lines=_env_int("LOG_TAIL_LINES", 40),
            k8s_enabled=os.getenv("K8S_EVIDENCE_ENABLED", "true").lower() not in {"0", "false", "no"},
        )

    def webhook_configured(self) -> bool:
        return bool(self.grok_webhook_url)
