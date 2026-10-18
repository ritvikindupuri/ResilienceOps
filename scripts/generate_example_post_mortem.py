#!/usr/bin/env python3
"""Write reports/example_incident_memory_exhaustion.md from PostMortemGenerator.

Uses representative MEMORY_EXHAUSTION inputs that match InfraDisruptorAgent,
DiagnosticAgent (OOM path), and RemediatorAgent (always POST /fault/reset;
k8s restart only when K8sToolKit.k8s_available). MTTD/MTTR are example
values, not measured from a live run.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.incident_response.post_mortem import PostMortemGenerator

EXAMPLE = ROOT / "reports" / "example_incident_memory_exhaustion.md"
BANNER = """> **Example report** (not a live incident). Produced by
> `scripts/generate_example_post_mortem.py` calling `PostMortemGenerator`
> in `agents/incident_response/post_mortem.py` with representative
> `MEMORY_EXHAUSTION` inputs. The title comes from `resolve_fault_title()`
> (the `UNKNOWN_FAULT` title bug was fixed in PR #1). MTTD/MTTR below are
> example numbers, not a guarantee.

"""

# Inputs a k3s cycle can emit: catalog scenario MEMORY_EXHAUSTION, RCA
# MEMORY_EXHAUSTION_OOM when order-service is 5xx and events mention oom,
# remediator always resets then restarts only if k8s is available.
FAULT = {
    "scenario": "MEMORY_EXHAUSTION",
    "fault_type": "MEMORY_EXHAUSTION",
    "target_service": "order-service",
    "expected_sre_impact": (
        "Container cgroup memory limit breached -> OOM killer triggers container restart."
    ),
}
INCIDENT = {"severity": "SEV-1"}
DIAGNOSIS = {
    "primary_root_cause": "MEMORY_EXHAUSTION_OOM",
    "confidence_score": 0.98,
    "hypotheses": [
        {
            "hypothesis": "Container memory limit exceeded (cgroup OOMKill)",
            "confidence": 0.98,
        }
    ],
    "recommended_runbook": "EVICT_CONTAINER_AND_PURGE_LEAK",
}
REMEDIATION = {
    "runbook": "EVICT_CONTAINER_AND_PURGE_LEAK",
    "actions_taken": [
        "Posted /fault/reset on order-service and payment-service (FaultCatalog.reset_environment).",
        "Restarted the order-service Deployment because K8sToolKit.k8s_available was true.",
    ],
}
EXAMPLE_MTTD_S = 3.81
EXAMPLE_MTTR_S = 5.26


def main() -> int:
    reports_dir = ROOT / "reports"
    before = set(reports_dir.glob("incident_*.md"))
    body = PostMortemGenerator().generate(
        FAULT, INCIDENT, DIAGNOSIS, REMEDIATION, EXAMPLE_MTTD_S, EXAMPLE_MTTR_S
    )
    after = set(reports_dir.glob("incident_*.md"))
    for extra in after - before:
        extra.unlink()
    EXAMPLE.parent.mkdir(parents=True, exist_ok=True)
    EXAMPLE.write_text(BANNER + body, encoding="utf-8")
    print(f"wrote {EXAMPLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
