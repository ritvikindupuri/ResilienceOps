> **Example report** (not a live incident). Produced by
> `scripts/generate_example_post_mortem.py` calling `PostMortemGenerator`
> in `agents/incident_response/post_mortem.py` with representative
> `MEMORY_EXHAUSTION` inputs. The title comes from `resolve_fault_title()`
> (the `UNKNOWN_FAULT` title bug was fixed in PR #1). MTTD/MTTR below are
> example numbers, not a guarantee.

# Incident Post-Mortem Report: MEMORY_EXHAUSTION

**Incident Timestamp**: 2026-10-18 23:17:46 UTC  
**Classification**: Production Incident (`SEV-1`)  
**Impacted Service**: `order-service`  
**Incident State**: `RESOLVED`  
**Handling Agents**: Health & Uptime Monitor, Root Cause Investigator, Automated Recovery Fixer, Incident Report Writer  

---

## 1. Executive Summary
At 2026-10-18 23:17:46 UTC, an automated reliability breach was detected impacting `order-service`. Telemetry monitoring identified SLO violations across request latency and error rates. The autonomous diagnostic system identified `MEMORY_EXHAUSTION_OOM` with **98.0% confidence** and triggered remediation runbook `EVICT_CONTAINER_AND_PURGE_LEAK`, restoring normal operations.

### Key Metrics
- **Mean Time To Detect (MTTD)**: `3.81 seconds`
- **Mean Time To Remediate (MTTR)**: `5.26 seconds`
- **Total Incident Duration**: `9.07 seconds`
- **Service Level Objective (SLO)**: Preserved (Auto-mitigation completed prior to SLA breach threshold).

---

## 2. Chronological Timeline
- **T0 (+0.0s)**: Fault `MEMORY_EXHAUSTION` injected into `order-service`.
- **T1 (+3.8s)**: SLO breach detected by Incident Monitor. Severity classified as `SEV-1`.
- **T2 (+4.6s)**: Root Cause Analysis completed. Identified `MEMORY_EXHAUSTION_OOM`.
- **T3 (+5.6s)**: Runbook `EVICT_CONTAINER_AND_PURGE_LEAK` executed by Auto-Remediator.
- **T4 (+9.1s)**: Latency and error rates verified within baseline thresholds. Incident resolved.

---

## 3. Root Cause Analysis
- **Observed Behavior**: Container cgroup memory limit breached -> OOM killer triggers container restart.
- **Root Failure Mechanism**: Container memory limit exceeded (cgroup OOMKill)
- **Confidence Level**: `98.0%`

---

## 4. Remediation & Recovery Actions
- **Executed Actions**: ['Posted /fault/reset on order-service and payment-service (FaultCatalog.reset_environment).', 'Restarted the order-service Deployment because K8sToolKit.k8s_available was true.']
- **Verification Result**: Latency returned to `<800ms`, HTTP 200 health status confirmed.

---

## 5. Preventative Action Items
| Action Item | Type | Priority | Owner |
|---|---|---|---|
| Configure circuit breakers for downstream dependencies | Prevention | High | SRE Team |
| Tighten container resource requests and memory thresholds | Mitigation | High | Platform Team |
| Implement automated canary deployment rollbacks | Prevention | Medium | DevOps Team |
