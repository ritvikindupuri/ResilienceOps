"""Approval is owner/write + incident label + exactly one proposal."""

from __future__ import annotations

from remediation.approval import (
    commenter_may_approve,
    evaluate_approval,
    is_approve_comment,
    parse_recorded_approval,
    render_approval_comment,
)

PROPOSAL = (
    "<!-- resilienceops-proposal:v1 -->\n"
    "action: reset_fault\n"
    "target: order-service\n"
    "<!-- /resilienceops-proposal -->\n"
)


def test_approve_comment_is_exact():
    assert is_approve_comment("/approve")
    assert is_approve_comment("  /APPROVE\n")
    assert not is_approve_comment("/approve please")
    assert not is_approve_comment("please /approve")
    assert not is_approve_comment("/approve\n/approve")


def test_owner_can_approve():
    ok, reason = commenter_may_approve(
        login="ritvikindupuri",
        user_type="User",
        author_association="NONE",
        permission="",
        owner_login="ritvikindupuri",
    )
    assert ok
    assert "owner" in reason


def test_write_permission_can_approve():
    ok, _ = commenter_may_approve(
        login="oncall",
        user_type="User",
        author_association="COLLABORATOR",
        permission="write",
        owner_login="ritvikindupuri",
    )
    assert ok


def test_bot_and_read_only_rejected():
    ok, reason = commenter_may_approve(
        login="incident-remediation[bot]",
        user_type="Bot",
        author_association="MEMBER",
        permission="write",
        owner_login="ritvikindupuri",
    )
    assert not ok
    assert "bot" in reason
    ok, _ = commenter_may_approve(
        login="random",
        user_type="User",
        author_association="NONE",
        permission="read",
        owner_login="ritvikindupuri",
    )
    assert not ok


def _eval(**overrides):
    base = dict(
        comment_body="/approve",
        commenter_login="ritvikindupuri",
        commenter_type="User",
        author_association="OWNER",
        permission="admin",
        issue_labels=[{"name": "incident"}],
        issue_is_pull_request=False,
        proposal_comments=[PROPOSAL],
        owner_login="ritvikindupuri",
    )
    base.update(overrides)
    return evaluate_approval(**base)


def test_happy_path_records_one_action():
    decision = _eval()
    assert decision.ok
    assert decision.proposal is not None
    assert decision.proposal.action == "reset_fault"
    assert decision.proposal.target == "order-service"
    rendered = render_approval_comment(decision)
    recorded = parse_recorded_approval(rendered)
    assert recorded["action"] == "reset_fault"
    assert recorded["approved_by"] == "ritvikindupuri"


def test_rejects_missing_incident_label():
    decision = _eval(issue_labels=[{"name": "bug"}])
    assert not decision.ok
    assert "incident" in decision.reason


def test_rejects_pull_request():
    decision = _eval(issue_is_pull_request=True)
    assert not decision.ok


def test_rejects_without_proposal():
    decision = _eval(proposal_comments=["looks bad, please fix"])
    assert not decision.ok
    assert "proposal" in decision.reason
