"""Validate `/approve` on an `incident` issue and extract the proposed action.

The GitHub Actions workflow records the approval. It does not run the fix
(a GitHub-hosted runner cannot reach a local Compose stack).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from remediation.actions import Proposal, RemediationError, latest_proposal

APPROVE_RE = re.compile(r"^\s*/approve\s*$", re.IGNORECASE)
INCIDENT_LABEL = "incident"
WRITE_PERMISSIONS = frozenset({"admin", "write", "maintain"})
WRITE_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})


@dataclass(frozen=True)
class ApprovalDecision:
    ok: bool
    reason: str
    proposal: Proposal | None = None
    approver: str = ""

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": self.ok,
            "reason": self.reason,
            "approver": self.approver,
        }
        if self.proposal is not None:
            payload["proposal"] = self.proposal.as_dict()
        return payload


def is_approve_comment(body: str | None) -> bool:
    return bool(APPROVE_RE.match(body or ""))


def issue_has_incident_label(labels: Iterable[Any]) -> bool:
    names: list[str] = []
    for item in labels or []:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict):
            names.append(str(item.get("name") or ""))
    return INCIDENT_LABEL in names


def commenter_may_approve(
    *,
    login: str,
    user_type: str,
    author_association: str,
    permission: str | None,
    owner_login: str | None = None,
) -> tuple[bool, str]:
    """Owner or write/maintain/admin collaborator, never a bot account."""
    login_n = (login or "").strip()
    if not login_n:
        return False, "missing commenter login"
    if (user_type or "").lower() == "bot":
        return False, "bot accounts cannot approve"
    if owner_login and login_n.lower() == owner_login.lower():
        return True, "repo owner"
    assoc = (author_association or "").upper()
    perm = (permission or "").lower()
    if perm in WRITE_PERMISSIONS:
        return True, f"permission={perm}"
    if assoc == "OWNER":
        return True, "author_association=OWNER"
    if assoc in WRITE_ASSOCIATIONS and perm in WRITE_PERMISSIONS:
        return True, f"association={assoc}"
    return False, "commenter does not have write permission"


def evaluate_approval(
    *,
    comment_body: str,
    commenter_login: str,
    commenter_type: str,
    author_association: str,
    permission: str | None,
    issue_labels: Iterable[Any],
    issue_is_pull_request: bool,
    proposal_comments: Iterable[str],
    owner_login: str | None = None,
) -> ApprovalDecision:
    if issue_is_pull_request:
        return ApprovalDecision(False, "approval is only valid on issues, not pull requests")
    if not is_approve_comment(comment_body):
        return ApprovalDecision(False, "comment is not a lone /approve")
    if not issue_has_incident_label(issue_labels):
        return ApprovalDecision(False, "issue is not labeled incident")
    allowed, why = commenter_may_approve(
        login=commenter_login,
        user_type=commenter_type,
        author_association=author_association,
        permission=permission,
        owner_login=owner_login,
    )
    if not allowed:
        return ApprovalDecision(False, why, approver=commenter_login)
    try:
        proposal = latest_proposal(proposal_comments)
    except RemediationError as exc:
        return ApprovalDecision(False, str(exc), approver=commenter_login)
    return ApprovalDecision(
        True,
        "approval recorded",
        proposal=proposal,
        approver=commenter_login,
    )


APPROVAL_OPEN = "<!-- resilienceops-approval:v1 -->"
APPROVAL_CLOSE = "<!-- /resilienceops-approval -->"


def render_approval_comment(decision: ApprovalDecision) -> str:
    if not decision.ok or decision.proposal is None:
        raise RemediationError("cannot render a failed approval")
    p = decision.proposal
    return (
        f"{APPROVAL_OPEN}\n"
        f"approved_by: {decision.approver}\n"
        f"action: {p.action}\n"
        f"target: {p.target}\n"
        f"{APPROVAL_CLOSE}\n"
        "\n"
        f"Recorded `/approve` from `{decision.approver}` for "
        f"`{p.action}` / `{p.target}`.\n"
        "\n"
        "A GitHub-hosted runner cannot reach the lab. The host poller "
        "(`python3 remediation/poll_and_apply.py`) or "
        "`python3 remediation/remediate.py --via-ssm` on the AWS EC2 host "
        "is what actually runs the allowlisted fix.\n"
    )


APPROVAL_BLOCK = re.compile(
    r"<!--\s*resilienceops-approval:v1\s*-->(.*?)<!--\s*/resilienceops-approval\s*-->",
    re.DOTALL | re.IGNORECASE,
)
APPROVAL_FIELD = re.compile(r"^(approved_by|action|target)\s*:\s*(\S+)\s*$", re.IGNORECASE)


def parse_recorded_approval(text: str) -> dict[str, str]:
    matches = list(APPROVAL_BLOCK.finditer(text or ""))
    if len(matches) != 1:
        raise RemediationError("expected exactly one recorded approval block")
    fields: dict[str, str] = {}
    for raw in matches[0].group(1).splitlines():
        line = raw.strip()
        if not line:
            continue
        m = APPROVAL_FIELD.match(line)
        if not m:
            raise RemediationError("malformed approval field")
        fields[m.group(1).lower()] = m.group(2)
    if set(fields) != {"approved_by", "action", "target"}:
        raise RemediationError("approval block must be approved_by + action + target")
    return fields
