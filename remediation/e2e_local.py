#!/usr/bin/env python3
"""Local Compose E2E for the remediator allowlist (no live GitHub required).

Injects Redis starvation, builds a proposal, simulates /approve, runs the
allowlisted reset, and checks Prometheus. Writes logs under logs/ and
examples/remediation_e2e/.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from remediation.actions import Proposal, execute, parse_proposal, verify_recovery
from remediation.approval import evaluate_approval
from remediation.envload import load_remediation_env
from remediation.logutil import emit

OUT = ROOT / "examples" / "remediation_e2e"
ORDER = os.getenv("ORDER_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/")
PROM = os.getenv("PROMETHEUS_URL", "http://127.0.0.1:9090").rstrip("/")


def _http(method: str, url: str, timeout: float = 8.0) -> tuple[int, str]:
    req = Request(url, method=method)
    with urlopen(req, timeout=timeout) as resp:
        return getattr(resp, "status", 200), resp.read().decode("utf-8", errors="replace")


def _stack_up() -> bool:
    try:
        _http("GET", f"{ORDER}/ready")
        _http("GET", f"{PROM}/-/healthy")
        return True
    except (URLError, TimeoutError, OSError):
        return False


def main() -> int:
    load_remediation_env()
    OUT.mkdir(parents=True, exist_ok=True)
    report: dict = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": [],
    }
    if shutil.which("docker") is None:
        report["ok"] = False
        report["error"] = "docker is not available in this environment"
        (OUT / "e2e_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(report["error"])
        return 2
    if not _stack_up():
        report["ok"] = False
        report["error"] = "Compose stack is not reachable on :8001 / :9090"
        (OUT / "e2e_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(report["error"])
        return 2

    before = execute(Proposal("reset_fault", "both"), dry_run=False)
    report["steps"].append({"pre_reset": before.as_dict()})

    status, body = _http("POST", f"{ORDER}/fault/redis-starvation")
    report["steps"].append({"inject": {"status": status, "body": body[:400]}})
    emit({"event": "e2e_inject", "status": status})

    firing = False
    for _ in range(30):
        time.sleep(1)
        try:
            raw = urlopen(f"{PROM}/api/v1/alerts", timeout=5).read().decode("utf-8")
            alerts = json.loads(raw).get("data", {}).get("alerts") or []
            names = [
                (a.get("labels") or {}).get("alertname")
                for a in alerts
                if a.get("state") == "firing"
            ]
            if "RedisConnectionSaturation" in names:
                firing = True
                report["steps"].append({"firing": names})
                break
        except (URLError, TimeoutError, json.JSONDecodeError):
            continue
    report["steps"].append({"alert_seen": firing})

    proposal_text = Proposal("reset_fault", "order-service").render()
    parsed = parse_proposal(proposal_text)
    decision = evaluate_approval(
        comment_body="/approve",
        commenter_login="ritvikindupuri",
        commenter_type="User",
        author_association="OWNER",
        permission="admin",
        issue_labels=[{"name": "incident"}],
        issue_is_pull_request=False,
        proposal_comments=[proposal_text],
        owner_login="ritvikindupuri",
    )
    report["steps"].append({"proposal": parsed.as_dict(), "approval": decision.as_dict()})
    if not decision.ok:
        report["ok"] = False
        (OUT / "e2e_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 3

    result = execute(parsed, dry_run=False)
    report["steps"].append({"fix": result.as_dict()})
    recovered = False
    last = None
    for _ in range(25):
        time.sleep(2)
        try:
            last = verify_recovery(parsed)
        except Exception as exc:  # noqa: BLE001 — E2E records the failure
            last = {"ok": False, "error": str(exc)}
        if last.get("ok"):
            recovered = True
            break
    report["steps"].append({"verify": last})
    report["ok"] = bool(result.ok and recovered)
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    (OUT / "e2e_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "e2e_bridge_like.log").write_text(
        json.dumps({"event": "e2e", "ok": report["ok"], "alert_seen": firing}, indent=2) + "\n",
        encoding="utf-8",
    )
    emit({"event": "e2e_done", "ok": report["ok"], "alert_seen": firing})
    print(json.dumps({"ok": report["ok"], "alert_seen": firing, "recovered": recovered}, indent=2))
    return 0 if report["ok"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
