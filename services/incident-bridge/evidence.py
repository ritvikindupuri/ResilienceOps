"""Build a compact, secret-free evidence bundle for an Alertmanager webhook."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import httpx

logger = logging.getLogger("incident_bridge")

SECRET_KEY_RE = re.compile(
    r"(password|passwd|secret|token|authorization|api[_-]?key|private[_-]?key|credential|cookie)",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*\S+"),
)

# Summarized PromQL snapshots covering SLO + chaos-fault signals (last ~10 minutes).
DEFAULT_QUERIES: Tuple[Tuple[str, str], ...] = (
    ("up", "up"),
    (
        "api_gw_rps",
        'sum(rate(http_requests_total{job="api-gw"}[1m]))',
    ),
    (
        "api_gw_error_rate_pct",
        '(sum(rate(http_requests_total{job="api-gw",status=~"5.."}[1m])) / clamp_min(sum(rate(http_requests_total{job="api-gw"}[1m])), 1e-9)) * 100',
    ),
    (
        "api_gw_p99_seconds",
        'histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket{job="api-gw"}[1m])))',
    ),
    (
        "order_error_rate_pct",
        '(sum(rate(orders_processed_total{status!="success"}[1m])) / clamp_min(sum(rate(orders_processed_total[1m])), 1e-9)) * 100',
    ),
    (
        "order_p99_seconds",
        "histogram_quantile(0.99, sum by (le) (rate(order_processing_duration_seconds_bucket[1m])))",
    ),
    ("memory_leak_bytes", "active_memory_leak_bytes"),
    ("order_rss_bytes", 'process_resident_memory_bytes{job="order-service"}'),
    ("redis_active_connections", "redis_active_connections_count"),
    (
        "payment_error_rate_pct",
        '(sum(rate(payments_processed_total{status!="success"}[1m])) / clamp_min(sum(rate(payments_processed_total[1m])), 1e-9)) * 100',
    ),
    (
        "payment_p99_seconds",
        "histogram_quantile(0.99, sum by (le) (rate(payment_processing_duration_seconds_bucket[1m])))",
    ),
    (
        "payment_outage_rps",
        'sum(rate(payments_processed_total{status="503_outage"}[1m]))',
    ),
)


def redact_secrets(value: Any) -> Any:
    """Recursively strip secret-looking keys and patterns from evidence structures."""
    if isinstance(value, dict):
        cleaned: Dict[str, Any] = {}
        for key, item in value.items():
            if SECRET_KEY_RE.search(str(key)):
                cleaned[str(key)] = "***"
            else:
                cleaned[str(key)] = redact_secrets(item)
        return cleaned
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, str):
        redacted = value
        for pattern in SECRET_VALUE_PATTERNS:
            redacted = pattern.sub("***", redacted)
        return redacted
    return value


def _to_float(raw: Any) -> Optional[float]:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def summarize_matrix(result: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Collapse a Prometheus matrix into min/max/avg/last. No raw sample floods."""
    summaries: List[Dict[str, Any]] = []
    for series in result:
        values = series.get("values") or []
        samples = [_to_float(point[1]) for point in values if isinstance(point, (list, tuple)) and len(point) >= 2]
        samples = [item for item in samples if item is not None]
        if not samples:
            summaries.append(
                {
                    "labels": series.get("metric") or {},
                    "samples": 0,
                }
            )
            continue
        summaries.append(
            {
                "labels": series.get("metric") or {},
                "samples": len(samples),
                "min": min(samples),
                "max": max(samples),
                "avg": sum(samples) / len(samples),
                "last": samples[-1],
            }
        )
    return summaries


def query_prometheus_range(
    prometheus_url: str,
    query: str,
    window_seconds: int = 600,
    step: str = "30s",
    client: Optional[httpx.Client] = None,
    now: Optional[float] = None,
) -> List[Dict[str, Any]]:
    end = now if now is not None else datetime.now(timezone.utc).timestamp()
    start = end - window_seconds
    params = {"query": query, "start": start, "end": end, "step": step}
    url = f"{prometheus_url.rstrip('/')}/api/v1/query_range"
    owns_client = client is None
    http = client or httpx.Client()
    try:
        response = http.get(url, params=params, timeout=2.0)
        response.raise_for_status()
        body = response.json()
        if body.get("status") != "success":
            raise RuntimeError(body.get("error") or "prometheus query failed")
        return summarize_matrix(body.get("data", {}).get("result") or [])
    finally:
        if owns_client:
            http.close()


def collect_prometheus_snapshots(
    prometheus_url: str,
    queries: Sequence[Tuple[str, str]] = DEFAULT_QUERIES,
    window_seconds: int = 600,
    client: Optional[httpx.Client] = None,
) -> List[Dict[str, Any]]:
    snapshots: List[Dict[str, Any]] = []
    for name, query in queries:
        try:
            snapshots.append(
                {
                    "name": name,
                    "query": query,
                    "series": query_prometheus_range(
                        prometheus_url,
                        query,
                        window_seconds=window_seconds,
                        client=client,
                    ),
                }
            )
        except Exception as exc:
            logger.warning("prometheus query %s failed: %s", name, type(exc).__name__)
            snapshots.append({"name": name, "query": query, "error": type(exc).__name__})
    return snapshots


def _tail_lines(path: Path, max_lines: int) -> List[str]:
    if max_lines <= 0 or not path.is_file():
        return []
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size > 256 * 1024:
                handle.seek(-256 * 1024, os.SEEK_END)
            data = handle.read()
        text = data.decode("utf-8", errors="replace")
        lines = text.splitlines()
        return lines[-max_lines:]
    except OSError as exc:
        logger.warning("failed to read activity log: %s", type(exc).__name__)
        return []


def collect_agent_activity(log_path: str, max_lines: int = 40) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for line in _tail_lines(Path(log_path), max_lines):
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            records.append({"raw": redact_secrets(line[:500])})
            continue
        records.append(redact_secrets(parsed))
    return records


def collect_k8s_events(limit: int = 15) -> Optional[List[Dict[str, Any]]]:
    """Best-effort Kubernetes events. Optional: returns None when the API is unavailable."""
    try:
        from kubernetes import client, config as kube_config
    except ImportError:
        return None
    try:
        try:
            kube_config.load_incluster_config()
        except Exception:
            kube_config.load_kube_config()
        core = client.CoreV1Api()
        events: List[Any] = []
        for namespace in ("sre-target-apps", "sre-agent-sandbox"):
            try:
                listed = core.list_namespaced_event(namespace, limit=limit, _request_timeout=2)
                events.extend(listed.items or [])
            except Exception:
                continue
        if not events:
            listed = core.list_event_for_all_namespaces(limit=limit, _request_timeout=2)
            events.extend(listed.items or [])
        events.sort(key=lambda item: getattr(item.metadata, "creation_timestamp", None) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        compact: List[Dict[str, Any]] = []
        for item in events[:limit]:
            compact.append(
                redact_secrets(
                    {
                        "namespace": getattr(item.metadata, "namespace", None),
                        "name": getattr(item.metadata, "name", None),
                        "reason": getattr(item, "reason", None),
                        "type": getattr(item, "type", None),
                        "message": (getattr(item, "message", None) or "")[:300],
                        "count": getattr(item, "count", None),
                    }
                )
            )
        return compact
    except Exception as exc:
        logger.info("k8s events unavailable: %s", type(exc).__name__)
        return None


def collect_evidence(
    *,
    prometheus_url: str,
    agent_activity_log: str,
    window_seconds: int = 600,
    log_tail_lines: int = 40,
    k8s_enabled: bool = True,
    prometheus_client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    owns_client = prometheus_client is None
    http = prometheus_client or httpx.Client()
    try:
        bundle: Dict[str, Any] = {
            "window_seconds": window_seconds,
            "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "prometheus": collect_prometheus_snapshots(
                prometheus_url,
                window_seconds=window_seconds,
                client=http,
            ),
            "agent_activity": collect_agent_activity(agent_activity_log, max_lines=log_tail_lines),
        }
    finally:
        if owns_client:
            http.close()
    if k8s_enabled:
        k8s_events = collect_k8s_events()
        if k8s_events is not None:
            bundle["k8s_events"] = k8s_events
    return redact_secrets(bundle)
