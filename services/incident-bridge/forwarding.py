"""Auth header construction, payload size cap, dedupe, and outbound POST with retries."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Deque, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import httpx

logger = logging.getLogger("incident_bridge")

DEFAULT_MAX_BYTES = 100 * 1024
DEFAULT_DEDUPE_TTL = 300
RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504}


def build_auth_headers(
    key: str,
    header_name: str = "Authorization",
    scheme: str = "Bearer",
) -> Dict[str, str]:
    """Build the outbound auth header. Empty scheme sends the raw key as the header value."""
    if not key:
        return {}
    name = (header_name or "Authorization").strip() or "Authorization"
    value = f"{scheme} {key}".strip() if (scheme or "").strip() else key
    return {name: value}


def redact_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """Return a copy of headers with credential values removed. Never logs the key."""
    redacted: Dict[str, str] = {}
    for name, value in headers.items():
        lowered = name.lower()
        if lowered in {"authorization", "proxy-authorization"} or "key" in lowered or "token" in lowered or "secret" in lowered:
            redacted[name] = "***"
        else:
            redacted[name] = value
    return redacted


def alert_fingerprint(alert: Mapping[str, Any]) -> str:
    existing = str(alert.get("fingerprint") or "").strip()
    if existing:
        return existing
    labels = alert.get("labels") or {}
    blob = json.dumps(labels, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


class DedupeCache:
    """Drop identical fingerprint+status pairs seen within ttl_seconds (default 5 minutes)."""

    def __init__(self, ttl_seconds: int = DEFAULT_DEDUPE_TTL, clock: Callable[[], float] = time.monotonic):
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._seen: Dict[Tuple[str, str], float] = {}
        self._lock = threading.Lock()

    def _purge_locked(self, now: float) -> None:
        expired = [key for key, ts in self._seen.items() if now - ts >= self.ttl_seconds]
        for key in expired:
            del self._seen[key]

    def should_drop(self, fingerprint: str, status: str) -> bool:
        if not fingerprint:
            return False
        key = (fingerprint, status)
        now = self._clock()
        with self._lock:
            self._purge_locked(now)
            last = self._seen.get(key)
            return last is not None and (now - last) < self.ttl_seconds

    def remember(self, fingerprint: str, status: str) -> None:
        if not fingerprint:
            return
        now = self._clock()
        with self._lock:
            self._purge_locked(now)
            self._seen[(fingerprint, status)] = now

    def filter_new(self, alerts: Iterable[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
        kept: List[Mapping[str, Any]] = []
        for alert in alerts:
            status = str(alert.get("status") or "firing")
            fp = alert_fingerprint(alert)
            if self.should_drop(fp, status):
                logger.info("dropping duplicate alert fingerprint=%s status=%s", fp, status)
                continue
            kept.append(alert)
        return kept

    def remember_alerts(self, alerts: Iterable[Mapping[str, Any]]) -> None:
        for alert in alerts:
            self.remember(alert_fingerprint(alert), str(alert.get("status") or "firing"))


def _json_size(payload: Mapping[str, Any]) -> int:
    return len(json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))


def cap_payload(payload: MutableMapping[str, Any], max_bytes: int = DEFAULT_MAX_BYTES) -> Dict[str, Any]:
    """Shrink evidence (then annotations) until the JSON payload is under max_bytes (~100KB)."""
    working: Dict[str, Any] = json.loads(json.dumps(payload))
    if _json_size(working) <= max_bytes:
        return working

    evidence = working.get("evidence")
    if isinstance(evidence, dict):
        evidence["_truncated"] = True
        for key in ("k8s_events", "agent_activity", "prometheus"):
            if _json_size(working) <= max_bytes:
                break
            if key == "prometheus" and isinstance(evidence.get("prometheus"), list):
                trimmed = []
                for series in evidence["prometheus"]:
                    if isinstance(series, dict):
                        series = dict(series)
                        series.pop("query", None)
                    trimmed.append(series)
                evidence["prometheus"] = trimmed
            else:
                evidence.pop(key, None)
                evidence.setdefault("_dropped_fields", []).append(key)
        if _json_size(working) > max_bytes:
            working["evidence"] = {
                "_truncated": True,
                "note": "evidence omitted because the payload exceeded the size cap",
            }

    if _json_size(working) > max_bytes:
        for alert in working.get("alerts") or []:
            if not isinstance(alert, dict):
                continue
            annotations = alert.get("annotations")
            if isinstance(annotations, dict):
                for name in list(annotations):
                    value = annotations[name]
                    if isinstance(value, str) and len(value) > 200:
                        annotations[name] = value[:200] + "...[truncated]"
            if _json_size(working) <= max_bytes:
                break

    if _json_size(working) > max_bytes:
        alerts = working.get("alerts") or []
        while len(alerts) > 1 and _json_size(working) > max_bytes:
            alerts.pop()
        working["alerts"] = alerts
        working.setdefault("evidence", {})
        if isinstance(working["evidence"], dict):
            working["evidence"]["_truncated"] = True
            working["evidence"]["_alert_count_capped"] = True

    if _json_size(working) > max_bytes:
        working = {
            "status": working.get("status", "firing"),
            "alerts": [
                {
                    "status": (working.get("alerts") or [{}])[0].get("status", "firing") if working.get("alerts") else "firing",
                    "labels": (working.get("alerts") or [{}])[0].get("labels", {}) if working.get("alerts") else {},
                    "annotations": {"summary": "payload truncated to size cap"},
                    "fingerprint": (working.get("alerts") or [{}])[0].get("fingerprint", "") if working.get("alerts") else "",
                    "startsAt": (working.get("alerts") or [{}])[0].get("startsAt") if working.get("alerts") else None,
                    "endsAt": (working.get("alerts") or [{}])[0].get("endsAt") if working.get("alerts") else None,
                }
            ],
            "evidence": {"_truncated": True, "note": "hard size cap applied"},
            "source": "resilienceops",
        }
    return working


def post_with_retry(
    url: str,
    payload: Mapping[str, Any],
    headers: Optional[Mapping[str, str]] = None,
    timeout_seconds: float = 10.0,
    max_retries: int = 3,
    client: Optional[httpx.Client] = None,
    sleep: Callable[[float], None] = time.sleep,
) -> httpx.Response:
    """POST JSON with exponential backoff. Does not log Authorization or the webhook key."""
    delays = [0.5, 1.0, 2.0, 4.0]
    attempts = max(1, max_retries)
    last_error: Optional[BaseException] = None
    owns_client = client is None
    http = client or httpx.Client()
    safe_headers = redact_headers(headers or {})
    try:
        for attempt in range(attempts):
            try:
                response = http.post(
                    url,
                    json=payload,
                    headers=dict(headers or {}),
                    timeout=timeout_seconds,
                )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                logger.warning(
                    "webhook attempt %s/%s failed: %s (headers=%s)",
                    attempt + 1,
                    attempts,
                    type(exc).__name__,
                    safe_headers,
                )
            else:
                if 200 <= response.status_code < 300:
                    return response
                if response.status_code not in RETRYABLE_STATUS:
                    response.raise_for_status()
                last_error = httpx.HTTPStatusError(
                    f"retryable status {response.status_code}",
                    request=response.request,
                    response=response,
                )
                logger.warning(
                    "webhook attempt %s/%s got %s (headers=%s)",
                    attempt + 1,
                    attempts,
                    response.status_code,
                    safe_headers,
                )
            if attempt < attempts - 1:
                sleep(delays[min(attempt, len(delays) - 1)])
        if last_error:
            raise last_error
        raise RuntimeError("webhook forward failed with no recorded error")
    finally:
        if owns_client:
            http.close()


class FailedForwardQueue:
    """Bounded in-memory retry list for webhook POSTs that exhausted post_with_retry.

    Oldest entries drop first. Payloads must already be secret-stripped; the
    webhook key is never stored.
    """

    def __init__(self, max_items: int = 16):
        self.max_items = max_items
        self._items: Deque[Dict[str, Any]] = deque()
        self._lock = threading.Lock()

    def push(self, payload: Mapping[str, Any], error_name: str) -> None:
        item = {
            "payload": json.loads(json.dumps(payload)),
            "error": error_name,
            "queued_at": time.time(),
        }
        with self._lock:
            if len(self._items) >= self.max_items:
                self._items.popleft()
            self._items.append(item)

    def pop(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if not self._items:
                return None
            return self._items.popleft()

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)


def dead_letter_path(agent_activity_log: str) -> Path:
    parent = Path(agent_activity_log).expanduser().resolve().parent
    return parent / "bridge_deadletter.jsonl"


def write_dead_letter(
    agent_activity_log: str,
    payload: Mapping[str, Any],
    error_name: str,
    attempts: int,
) -> Optional[Path]:
    """Append a key-free JSONL record. Never write Authorization or GROK_WEBHOOK_KEY."""
    path = dead_letter_path(agent_activity_log)
    record = {
        "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "error": error_name,
        "attempts": attempts,
        "status": payload.get("status"),
        "alerts": payload.get("alerts"),
        "source": payload.get("source"),
        "evidence": payload.get("evidence"),
    }
    blob = json.dumps(record, separators=(",", ":"), ensure_ascii=True)
    if "GROK_WEBHOOK" in blob or "Bearer " in blob:
        logger.warning("refusing to write dead-letter record that looks like it contains a secret")
        return None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(blob + "\n")
        return path
    except OSError as exc:
        logger.warning("dead-letter write failed: %s", type(exc).__name__)
        return None


def alert_ids(alerts: Iterable[Mapping[str, Any]]) -> Tuple[str, str]:
    names: List[str] = []
    fingerprints: List[str] = []
    for alert in alerts:
        labels = alert.get("labels") or {}
        names.append(str(labels.get("alertname") or "?"))
        fingerprints.append(alert_fingerprint(alert))
    return ",".join(names) or "?", ",".join(fingerprints) or "?"
