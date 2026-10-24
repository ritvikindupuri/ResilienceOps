#!/usr/bin/env python3
"""GitHub Actions entrypoint: record a valid `/approve` on an incident issue.

Reads GITHUB_EVENT_PATH. Never executes a lab fix.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from remediation.approval import evaluate_approval, render_approval_comment  # noqa: E402
from remediation.github_api import (  # noqa: E402
    add_issue_comment,
    add_issue_labels,
    collaborator_permission,
    github_repository,
    list_issue_comments,
    repo_owner_login,
)
from remediation.envload import load_remediation_env  # noqa: E402
from remediation.logutil import emit  # noqa: E402


def _load_event() -> dict:
    path = Path(os.getenv("GITHUB_EVENT_PATH") or "")
    if not path.is_file():
        raise SystemExit("GITHUB_EVENT_PATH is missing")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    load_remediation_env()
    event = _load_event()
    comment = event.get("comment") or {}
    issue = event.get("issue") or {}
    repo = github_repository()
    owner = repo_owner_login(repo)
    login = str((comment.get("user") or {}).get("login") or "")
    user_type = str((comment.get("user") or {}).get("type") or "")
    permission = collaborator_permission(repo, login) if login else ""
    comments = []
    number = issue.get("number")
    if number:
        comments = [c.get("body") or "" for c in list_issue_comments(repo, int(number))]
    decision = evaluate_approval(
        comment_body=comment.get("body") or "",
        commenter_login=login,
        commenter_type=user_type,
        author_association=str(comment.get("author_association") or ""),
        permission=permission,
        issue_labels=issue.get("labels") or [],
        issue_is_pull_request=bool(issue.get("pull_request")),
        proposal_comments=comments,
        owner_login=owner,
    )
    emit({"event": "approval_decision", **decision.as_dict(), "issue": number})
    if not decision.ok:
        # Non-approve comments and unauthorized approvers exit 0 so the
        # workflow stays green; only unexpected errors fail the job.
        print(decision.reason)
        return 0
    add_issue_comment(repo, int(number), render_approval_comment(decision))
    add_issue_labels(repo, int(number), ["remediation-approved"])
    print(f"recorded approval for {decision.proposal.action}/{decision.proposal.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
