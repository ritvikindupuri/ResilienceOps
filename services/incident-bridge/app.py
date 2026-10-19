"""Incident bridge: Alertmanager webhook -> enriched payload -> Grok diagnosis webhook."""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Mapping, Optional

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse

from evidence import collect_evidence
from forwarding import (
    DedupeCache,
    FailedForwardQueue,
    alert_ids,
    build_auth_headers,
    cap_payload,
    post_with_retry,
    write_dead_letter,
)
from settings import Settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("incident_bridge")
# httpx INFO logs the full request URL. Do not print GROK_WEBHOOK_URL.
logging.getLogger("httpx").setLevel(logging.WARNING)

settings = Settings.from_env()
dedupe = DedupeCache(ttl_seconds=settings.dedupe_ttl_seconds)
failed_queue = FailedForwardQueue(max_items=16)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Do not print the webhook key or a settings dump.
    logger.info(
        "incident-bridge starting webhook_configured=%s auth_header=%s auth_scheme_set=%s prometheus=%s",
        settings.webhook_configured(),
        settings.grok_webhook_auth_header,
        bool(settings.grok_webhook_auth_scheme),
        settings.prometheus_url,
    )
    yield


app = FastAPI(title="ResilienceOps-Incident-Bridge", version="1.0.0", lifespan=lifespan)


def _slim_alerts(alerts: List[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    slim: List[Dict[str, Any]] = []
    for alert in alerts:
        slim.append(
            {
                "status": alert.get("status", "firing"),
                "labels": alert.get("labels") or {},
                "annotations": alert.get("annotations") or {},
                "fingerprint": alert.get("fingerprint") or "",
                "startsAt": alert.get("startsAt"),
                "endsAt": alert.get("endsAt"),
            }
        )
    return slim


def _forward_headers(cfg: Settings) -> Dict[str, str]:
    return build_auth_headers(
        cfg.grok_webhook_key,
        header_name=cfg.grok_webhook_auth_header,
        scheme=cfg.grok_webhook_auth_scheme,
    )


def _drain_retry_queue(
    cfg: Settings,
    forward,
    queue: FailedForwardQueue,
) -> None:
    item = queue.pop()
    if not item:
        return
    payload = item.get("payload") or {}
    names, fingerprints = alert_ids(payload.get("alerts") or [])
    try:
        forward(
            cfg.grok_webhook_url,
            payload,
            headers=_forward_headers(cfg),
            timeout_seconds=cfg.webhook_timeout_seconds,
            max_retries=cfg.webhook_max_retries,
        )
        logger.info(
            "retry queue forwarded previously failed payload alertname=%s fingerprint=%s",
            names,
            fingerprints,
        )
    except Exception as exc:
        queue.push(payload, type(exc).__name__)
        logger.error(
            "forward FAILED after %s attempts alertname=%s fingerprint=%s error=%s",
            cfg.webhook_max_retries,
            names,
            fingerprints,
            type(exc).__name__,
        )


def process_webhook(
    payload: Mapping[str, Any],
    *,
    settings_obj: Optional[Settings] = None,
    dedupe_cache: Optional[DedupeCache] = None,
    forward=post_with_retry,
    evidence_fn=collect_evidence,
    retry_queue: Optional[FailedForwardQueue] = None,
) -> str:
    """Enrich and forward. Returns a short outcome token. Never logs GROK_WEBHOOK_KEY.

    Outbound POST failures are logged, dead-lettered, and queued for a later
    retry. They do not raise into the ASGI app.
    """
    cfg = settings_obj or settings
    cache = dedupe_cache or dedupe
    queue = retry_queue if retry_queue is not None else failed_queue
    if not cfg.webhook_configured():
        logger.warning("GROK_WEBHOOK_URL is unset; dropping alert payload")
        return "dropped_unconfigured"

    if cfg.webhook_configured():
        _drain_retry_queue(cfg, forward, queue)

    raw_alerts = list(payload.get("alerts") or [])
    new_alerts = cache.filter_new(raw_alerts)
    if not new_alerts:
        logger.info("all alerts in webhook were duplicates; dropping")
        return "dropped_duplicate"

    try:
        evidence_bundle = evidence_fn(
            prometheus_url=cfg.prometheus_url,
            agent_activity_log=cfg.agent_activity_log,
            window_seconds=cfg.evidence_window_seconds,
            log_tail_lines=cfg.log_tail_lines,
            k8s_enabled=cfg.k8s_enabled,
        )
    except Exception as exc:
        logger.warning("evidence collection failed: %s", type(exc).__name__)
        evidence_bundle = {"error": type(exc).__name__, "note": "forwarding alert without full evidence"}

    outbound = {
        "status": payload.get("status", "firing"),
        "alerts": _slim_alerts(new_alerts),
        "evidence": evidence_bundle,
        "source": "resilienceops",
    }
    outbound = cap_payload(outbound, max_bytes=cfg.payload_max_bytes)
    headers = _forward_headers(cfg)
    names, fingerprints = alert_ids(outbound.get("alerts") or [])
    try:
        forward(
            cfg.grok_webhook_url,
            outbound,
            headers=headers,
            timeout_seconds=cfg.webhook_timeout_seconds,
            max_retries=cfg.webhook_max_retries,
        )
    except Exception as exc:
        logger.error(
            "forward FAILED after %s attempts alertname=%s fingerprint=%s error=%s",
            cfg.webhook_max_retries,
            names,
            fingerprints,
            type(exc).__name__,
        )
        write_dead_letter(
            cfg.agent_activity_log,
            outbound,
            type(exc).__name__,
            cfg.webhook_max_retries,
        )
        queue.push(outbound, type(exc).__name__)
        return "forward_failed"

    cache.remember_alerts(new_alerts)
    logger.info(
        "forwarded %s alert(s) status=%s source=resilienceops",
        len(outbound.get("alerts") or []),
        outbound.get("status"),
    )
    return "forwarded"


@app.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {
        "status": "ok",
        "webhook_configured": settings.webhook_configured(),
    }


@app.post("/webhook")
async def alertmanager_webhook(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid json"}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"error": "payload must be an object"}, status_code=400)
    def _run(body: Mapping[str, Any]) -> None:
        try:
            process_webhook(body)
        except Exception as exc:
            logger.error("unhandled webhook processing error: %s", type(exc).__name__)

    background_tasks.add_task(_run, payload)
    return JSONResponse({"accepted": True}, status_code=200)
