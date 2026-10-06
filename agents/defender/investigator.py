from typing import Dict, Any, List
from agents.config import CW_LOG_GROUP_DEFENDER
from agents.common.cw_logger import CloudWatchLogger
from agents.common.k8s_tools import K8sToolKit

class BlueTeamInvestigator:
    """Performs Root Cause Analysis (RCA) on declared incidents using K8s telemetry."""
    def __init__(self):
        self.cw = CloudWatchLogger(CW_LOG_GROUP_DEFENDER, stream_prefix="blue-investigator")
        self.k8s = K8sToolKit()

    def diagnose(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes incident evidence, inspects pods/logs, and emits root cause diagnosis."""
        telemetry = incident.get("telemetry_snapshot", {})
        pods = self.k8s.get_pods() if self.k8s.k8s_available else []
        events = self.k8s.get_recent_events() if self.k8s.k8s_available else []

        hypotheses = []
        primary_root_cause = "UNKNOWN_DEGRADATION"
        confidence = 0.50
        recommended_action = "RESTART_POD"

        # Evidence Rule 1: Payment Latency / Timeout
        if telemetry.get("payment_status") in [504, 502] or (telemetry.get("latency_ms", 0) > 2000 and telemetry.get("order_status") == 200):
            hypotheses.append({
                "hypothesis": "Payment service upstream latency causing gateway timeout",
                "evidence": f"Payment status {telemetry.get('payment_status')}, latency {telemetry.get('latency_ms')}ms",
                "confidence": 0.94
            })
            primary_root_cause = "PAYMENT_GATEWAY_LATENCY"
            confidence = 0.94
            recommended_action = "RESET_PAYMENT_LATENCY_AND_BOUNCE"

        # Evidence Rule 2: Order Service Failure / Crash / OOM
        elif telemetry.get("order_status") in [500, 502, 504]:
            # Check if any pod was OOMKilled or in CrashLoop
            oom_detected = any("oom" in str(ev).lower() for ev in events)
            if oom_detected:
                hypotheses.append({
                    "hypothesis": "Container cgroup memory exhaustion (OOMKill Exit 137)",
                    "evidence": "K8s OOMKilled events detected",
                    "confidence": 0.98
                })
                primary_root_cause = "MEMORY_LEAK_OOM"
                confidence = 0.98
                recommended_action = "EVICT_OOM_POD_AND_CLEAR_BUFFER"
            else:
                hypotheses.append({
                    "hypothesis": "Order service process crash or connection saturation",
                    "evidence": f"Order status {telemetry.get('order_status')}",
                    "confidence": 0.88
                })
                primary_root_cause = "ORDER_SERVICE_CRASH"
                confidence = 0.88
                recommended_action = "RESTART_ORDER_SERVICE"

        # Evidence Rule 3: High Latency with 200s (CPU Throttling)
        elif telemetry.get("latency_ms", 0) > 1000:
            hypotheses.append({
                "hypothesis": "CPU quota saturation / CFS throttling",
                "evidence": f"Slow response time {telemetry.get('latency_ms')}ms with HTTP 200",
                "confidence": 0.85
            })
            primary_root_cause = "CPU_THROTTLING"
            confidence = 0.85
            recommended_action = "SCALE_DEPLOYMENT_REPLICAS"

        diagnostic_report = {
            "agent": "blue-team-investigator",
            "action": "RCA_DIAGNOSIS_COMPLETED",
            "incident_severity": incident.get("severity", "SEV-2"),
            "primary_root_cause": primary_root_cause,
            "confidence_score": confidence,
            "hypotheses_evaluated": hypotheses,
            "recommended_runbook": recommended_action,
            "inspected_pods_count": len(pods),
            "status": "READY_FOR_REMEDIATION"
        }
        self.cw.log(diagnostic_report)
        return diagnostic_report
