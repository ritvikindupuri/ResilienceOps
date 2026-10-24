"""Approval-gated, allowlisted incident remediator (Path C).

The imported Incident Remediation bot proposes a fix on a GitHub `incident`
issue. A human with write access comments `/approve`. A host-side process
(not a GitHub-hosted runner) then runs exactly one allowlisted action.
"""
