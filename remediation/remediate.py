#!/usr/bin/env python3
"""Run one allowlisted remediator action (local Compose, or via existing SSM).

Examples:

    python3 remediation/remediate.py --dry-run --action reset_fault --target order-service
    python3 remediation/remediate.py --action restart_service --target payment-service
    python3 remediation/remediate.py record-last-good
    python3 remediation/remediate.py --via-ssm --action reset_fault --target both
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from remediation.actions import (  # noqa: E402
    ACTIONS,
    APP_SERVICES,
    Proposal,
    RemediationError,
    execute,
    parse_proposal,
    record_last_good,
    validate_proposal_fields,
    verify_recovery,
)
from remediation.envload import load_remediation_env  # noqa: E402
from remediation.logutil import emit  # noqa: E402


def _load_proposal(args: argparse.Namespace) -> Proposal:
    if args.proposal_file:
        text = Path(args.proposal_file).read_text(encoding="utf-8")
        return parse_proposal(text)
    if args.proposal_text:
        return parse_proposal(args.proposal_text)
    if not args.action or not args.target:
        raise SystemExit("provide --action and --target, or --proposal-file / --proposal-text")
    return validate_proposal_fields(args.action, args.target)


def _via_ssm(argv: list[str]) -> int:
    """Re-run this CLI on the EC2 host using deploy_remote.send_and_wait."""
    # Import here so unit tests do not need boto3 for local dry-runs.
    import boto3

    from agents.config import require_ec2_instance_id
    from deploy_remote import resolve_region, send_and_wait

    region = resolve_region(None)
    instance_id = require_ec2_instance_id()
    # Reconstruct a safe argv (already allowlisted tokens only).
    remote = [
        "set -euo pipefail",
        "cd /opt/resilienceops",
        "python3 remediation/remediate.py " + shlex.join(argv),
    ]
    ssm = boto3.client("ssm", region_name=region)
    emit(
        {
            "event": "ssm_dispatch",
            "region": region,
            "instance_id": instance_id,
            "argv": argv,
        }
    )
    try:
        send_and_wait(
            ssm,
            instance_id,
            remote,
            timeout_s=300,
            comment="resilienceops-remediate",
        )
    except SystemExit as exc:
        emit({"event": "ssm_failed", "error": str(exc), "argv": argv})
        return 2
    except Exception as exc:
        emit({"event": "ssm_failed", "error": str(exc), "argv": argv})
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    load_remediation_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=["run", "record-last-good"], default="run")
    parser.add_argument("--action", choices=sorted(ACTIONS))
    parser.add_argument("--target")
    parser.add_argument("--proposal-file")
    parser.add_argument("--proposal-text")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--via-ssm",
        action="store_true",
        help="Run the same CLI on the EC2 host via existing SSM SendCommand (no new IAM).",
    )
    parser.add_argument("--skip-verify", action="store_true")
    parser.add_argument(
        "--verify-timeout",
        type=int,
        default=45,
        help="Seconds to poll Prometheus after the action (default 45).",
    )
    args = parser.parse_args(argv)

    if args.command == "record-last-good":
        if args.via_ssm:
            return _via_ssm(["record-last-good"])
        payload = record_last_good(sorted(APP_SERVICES))
        emit({"event": "record_last_good", "services": list(payload["services"])})
        print(json.dumps({"ok": True, "services": list(payload["services"])}, indent=2))
        return 0

    proposal = _load_proposal(args)
    if args.via_ssm:
        remote_argv = ["--action", proposal.action, "--target", proposal.target]
        if args.dry_run:
            remote_argv.append("--dry-run")
        if args.skip_verify:
            remote_argv.append("--skip-verify")
        remote_argv.extend(["--verify-timeout", str(args.verify_timeout)])
        return _via_ssm(remote_argv)

    result = execute(proposal, dry_run=args.dry_run)
    payload = result.as_dict()
    payload["event"] = "remediate"
    emit(payload)
    if not result.ok:
        print(json.dumps(payload, indent=2))
        return 2

    if args.dry_run or args.skip_verify:
        print(json.dumps(payload, indent=2))
        return 0

    deadline = time.time() + max(1, args.verify_timeout)
    last_verify = None
    while time.time() < deadline:
        try:
            last_verify = verify_recovery(proposal)
        except RemediationError as exc:
            last_verify = {"ok": False, "error": str(exc)}
        if last_verify.get("ok"):
            break
        time.sleep(2)
    payload["verify"] = last_verify
    emit({"event": "verify", "verify": last_verify, "action": proposal.action, "target": proposal.target})
    print(json.dumps(payload, indent=2))
    return 0 if last_verify and last_verify.get("ok") else 3


if __name__ == "__main__":
    # Avoid unused-import lint on os when running as a module.
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    raise SystemExit(main())
