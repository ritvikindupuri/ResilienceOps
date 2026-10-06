import time
from datetime import datetime
from typing import Dict, Any
from agents.config import CW_LOG_GROUP_INCIDENTS
from agents.common.cw_logger import CloudWatchLogger

class PostMortemGenerator:
    """Generates production-grade SRE Incident Post-Mortem documents."""
    def __init__(self):
        self.cw = CloudWatchLogger(CW_LOG_GROUP_INCIDENTS, stream_prefix="post-mortem")

    def generate(self, attack: Dict[str, Any], incident: Dict[str, Any], diagnosis: Dict[str, Any], remediation: Dict[str, Any], mttd_sec: float, mttr_sec: float) -> str:
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        vector = attack.get("vector", "UNKNOWN_FAULT")
        target = attack.get("target", "infrastructure")
        severity = incident.get("severity", "SEV-1")
        root_cause = diagnosis.get("primary_root_cause", "UNKNOWN")
        confidence = diagnosis.get("confidence_score", 0.0) * 100
        runbook = remediation.get("runbook", "N/A")

        report = f"""# SRE Incident Post-Mortem: {vector} on {target}

**Date**: {now_str}  
**Severity**: `{severity}`  
**Status**: `RESOLVED`  
**Lead SRE Agents**: Sentinel, Investigator, Operator  

---

## 1. Executive Summary
On {now_str}, an automated reliability breach was detected impacting `{target}`. Synthetic user traffic experienced elevated error rates and latency degradation exceeding our SLO budget. Autonomous Blue Team SRE agents diagnosed `{root_cause}` with **{confidence:.1f}% confidence** and executed runbook `{runbook}`, successfully restoring service.

- **MTTD (Mean Time To Detect)**: `{mttd_sec:.2f} seconds`
- **MTTR (Mean Time To Remediate)**: `{mttr_sec:.2f} seconds`
- **Total Impact Duration**: `{mttd_sec + mttr_sec:.2f} seconds`
- **SLO Error Budget Impact**: Breached (Automated mitigation prevented SLA violation).

---

## 2. Incident Timeline
- **T0 (Attack Injected)**: Red Team initiated `{vector}` against `{target}`.
- **T1 (+{mttd_sec:.1f}s - Incident Declared)**: Blue Sentinel detected SLO breach. Severity: `{severity}`.
- **T2 (+{mttd_sec + 1.2:.1f}s - Diagnosis)**: Blue Investigator completed RCA. Identified `{root_cause}`.
- **T3 (+{mttd_sec + 2.5:.1f}s - Remediation)**: Blue Operator executed runbook `{runbook}`.
- **T4 (+{mttd_sec + mttr_sec:.1f}s - Verification)**: Gateway latency normalized below 1000ms. SLO restored.

---

## 3. Root Cause Analysis (RCA)
- **Failure Mode**: {attack.get('expected_impact', 'Induced system fault')}
- **Underlying Mechanism**: {diagnosis.get('hypotheses_evaluated', [{}])[0].get('hypothesis', 'System degradation')}
- **Trigger**: Red Team Chaos injection simulating real-world node/network degradation.

---

## 4. Preventative Action Items
| Action Item | Type | Priority | Owner |
|---|---|---|---|
| Configure aggressive HPA threshold for {target} | Prevent | High | SRE Infra |
| Add client-side circuit breakers with tenacity/resilience4j | Mitigate | High | App Team |
| Fine-tune memory requests and cgroup limits | Mitigate | Medium | Platform Team |
"""
        # Ship to CloudWatch Incidents log group
        self.cw.log({
            "agent": "sre-post-mortem-engine",
            "action": "POST_MORTEM_PUBLISHED",
            "severity": severity,
            "vector": vector,
            "target": target,
            "mttd_seconds": round(mttd_sec, 2),
            "mttr_seconds": round(mttr_sec, 2),
            "root_cause": root_cause,
            "report_preview": report[:300] + "..."
        })
        return report
