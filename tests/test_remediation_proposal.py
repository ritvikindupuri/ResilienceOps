"""Proposal parser: exactly one action, stable render, latest-wins."""

from __future__ import annotations

import pytest

from remediation.actions import Proposal, RemediationError, latest_proposal, parse_proposal


def test_round_trip_render():
    original = Proposal("restart_service", "api-gw")
    parsed = parse_proposal(original.render())
    assert parsed == original


def test_case_and_spacing_normalized():
    text = (
        "Diagnosis above.\n"
        "<!-- ResilienceOps-Proposal:v1 -->\n"
        "Action: RESET_FAULT\n"
        "Target: BOTH\n"
        "<!-- /resilienceops-proposal -->\n"
    )
    parsed = parse_proposal(text)
    assert parsed.action == "reset_fault"
    assert parsed.target == "both"


def test_latest_proposal_wins():
    first = Proposal("reset_fault", "order-service").render()
    second = Proposal("restart_service", "payment-service").render()
    chosen = latest_proposal(["noise", first, "still noise", second])
    assert chosen.action == "restart_service"
    assert chosen.target == "payment-service"


def test_latest_proposal_raises_when_absent():
    with pytest.raises(RemediationError, match="no resilienceops proposal"):
        latest_proposal(["hello", "world"])
