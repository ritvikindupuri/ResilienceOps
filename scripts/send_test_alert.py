#!/usr/bin/env python3
"""Send a synthetic alert through Alertmanager or directly to the incident bridge.

Examples:
  python scripts/send_test_alert.py
  python scripts/send_test_alert.py --target alertmanager
  python scripts/send_test_alert.py --target bridge --bridge-url http://127.0.0.1:8088/webhook
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

import httpx


def rfc3339_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_am_alert() -> list:
    return [
        {
            "labels": {
                "alertname": "SyntheticTestAlert",
                "severity": "warning",
                "service": "api-gw",
                "cluster": "resilienceops",
            },
            "annotations": {
                "summary": "Synthetic ResilienceOps test alert",
                "description": "Fired by scripts/send_test_alert.py to verify Alertmanager -> incident-bridge -> Grok webhook.",
            },
            "startsAt": rfc3339_now(),
            "generatorURL": "http://127.0.0.1:9090/graph",
        }
    ]


def build_bridge_payload() -> dict:
    return {
        "version": "4",
        "status": "firing",
        "receiver": "incident-bridge",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "SyntheticTestAlert",
                    "severity": "warning",
                    "service": "api-gw",
                },
                "annotations": {
                    "summary": "Synthetic ResilienceOps test alert",
                    "description": "Fired by scripts/send_test_alert.py directly at the incident bridge.",
                },
                "startsAt": rfc3339_now(),
                "endsAt": "0001-01-01T00:00:00Z",
                "fingerprint": "synthetic-test",
                "generatorURL": "http://127.0.0.1:9090/graph",
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fire a synthetic ResilienceOps alert")
    parser.add_argument("--target", choices=("alertmanager", "bridge"), default="alertmanager")
    parser.add_argument("--alertmanager-url", default="http://127.0.0.1:9093/api/v2/alerts")
    parser.add_argument("--bridge-url", default="http://127.0.0.1:8088/webhook")
    args = parser.parse_args()

    if args.target == "alertmanager":
        url = args.alertmanager_url
        body: object = build_am_alert()
    else:
        url = args.bridge_url
        body = build_bridge_payload()

    try:
        response = httpx.post(url, json=body, timeout=10.0)
    except httpx.HTTPError as exc:
        print(f"request failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    body = (response.text or "").strip()
    print(f"{response.status_code}{(' ' + body[:500]) if body else ''}")
    return 0 if response.is_success or response.status_code in {200, 202, 204} else 1


if __name__ == "__main__":
    raise SystemExit(main())
