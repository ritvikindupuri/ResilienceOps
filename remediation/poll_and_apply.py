#!/usr/bin/env python3
"""Poll GitHub for approved incident issues and run the allowlisted fix here.

A GitHub-hosted runner cannot reach a laptop Compose stack. Run this on the
host that has the lab (or with --via-ssm to reuse deploy_remote.SendCommand).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from remediation.actions import validate_proposal_fields  # noqa: E402
from remediation.approval import parse_recorded_approval  # noqa: E402
from remediation.github_api import (  # noqa: E402
    add_issue_comment,
    add_issue_labels,
    github_repository,
    list_issue_comments,
    list_labeled_issues,
)
from remediation.envload import load_remediation_env  # noqa: E402
from remediation.logutil import emit  # noqa: E402
from remediation.remediate import main as remediate_main  # noqa: E402

APPROVED = "remediation-approved"
APPLIED = "remediation-applied"


def _already_applied(comments: list[dict]) -> bool:
    for comment in comments:
        body = comment.get("body") or ""
        if "<!-- resilienceops-result:v1 -->" in body:
            return True
    return False


def _apply_one(issue: dict, *, dry_run: bool, via_ssm: bool, verify_timeout: int) -> None:
    repo = github_repository()
    number = int(issue["number"])
    comments = list_issue_comments(repo, number)
    if _already_applied(comments):
        emit({"event": "skip", "issue": number, "reason": "result comment already present"})
        return
    recorded = None
    for comment in comments:
        body = comment.get("body") or ""
        if "<!-- resilienceops-approval:v1 -->" not in body:
            continue
        recorded = parse_recorded_approval(body)
    if recorded is None:
        emit({"event": "skip", "issue": number, "reason": "no recorded approval block"})
        return
    proposal = validate_proposal_fields(recorded["action"], recorded["target"])
    argv = ["--action", proposal.action, "--target", proposal.target]
    if dry_run:
        argv.append("--dry-run")
    if via_ssm:
        argv.append("--via-ssm")
    argv.extend(["--verify-timeout", str(verify_timeout)])
    emit({"event": "apply", "issue": number, "proposal": proposal.as_dict(), "dry_run": dry_run})
    try:
        code = remediate_main(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        emit({"event": "apply_failed", "issue": number, "error": str(exc)})
    except Exception as exc:
        code = 2
        emit({"event": "apply_failed", "issue": number, "error": str(exc)})
    result_body = (
        "<!-- resilienceops-result:v1 -->\n"
        f"ok: {'true' if code == 0 else 'false'}\n"
        f"action: {proposal.action}\n"
        f"target: {proposal.target}\n"
        "<!-- /resilienceops-result -->\n\n"
        f"Host remediator finished with exit {code} "
        f"for `{proposal.action}` / `{proposal.target}`.\n"
    )
    add_issue_comment(repo, number, result_body)
    if code == 0 and not dry_run:
        add_issue_labels(repo, number, [APPLIED])


def main(argv: list[str] | None = None) -> int:
    load_remediation_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Scan once and exit (default).")
    parser.add_argument("--loop", action="store_true", help="Poll until interrupted.")
    parser.add_argument("--interval", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--via-ssm", action="store_true")
    parser.add_argument("--verify-timeout", type=int, default=45)
    args = parser.parse_args(argv)

    def scan() -> None:
        repo = github_repository()
        issues = list_labeled_issues(repo, ["incident", APPROVED])
        for issue in issues:
            labels = {item.get("name") for item in issue.get("labels") or []}
            if APPLIED in labels:
                continue
            _apply_one(
                issue,
                dry_run=args.dry_run,
                via_ssm=args.via_ssm,
                verify_timeout=args.verify_timeout,
            )

    if args.loop:
        while True:
            scan()
            time.sleep(max(5, args.interval))
    scan()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
