from typing import Dict, Any, List
from agents.common.structured_logger import StructuredLogger
from agents.common.k8s_tools import K8sToolKit
from agents.common.llm_engine import EnterpriseLLMEngine

class DiagnosticAgent:
    """Performs Root Cause Analysis (RCA) on declared production incidents."""

    def __init__(self):
        self.logger = StructuredLogger("Root Cause Investigator")
        self.k8s = K8sToolKit()
        self.llm = EnterpriseLLMEngine()

    def analyze(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes incident evidence and generates an RCA diagnostic report."""
        telemetry = incident.get("telemetry", {})
        events = self.k8s.get_recent_events() if self.k8s.k8s_available else []

        hypotheses = []
        root_cause = "UNKNOWN_DEGRADATION"
        confidence = 0.50
        recommended_runbook = "RESTART_WORKLOAD"

        # Check Payment Latency Scenario
        if telemetry.get("payment_status") in [504, 502] or (telemetry.get("latency_ms", 0) > 2000 and telemetry.get("order_status") == 200):
            hypotheses.append({
                "hypothesis": "Downstream payment provider latency propagating to API gateway",
                "confidence": 0.95
            })
            root_cause = "DOWNSTREAM_PAYMENT_LATENCY"
            confidence = 0.95
            recommended_runbook = "RESET_PAYMENT_PARAMETERS"

        # Check Memory Leak / Crash Scenario
        elif telemetry.get("order_status") in [500, 502, 504]:
            oom_event = any("oom" in str(e).lower() for e in events)
            if oom_event:
                hypotheses.append({
                    "hypothesis": "Container memory limit exceeded (cgroup OOMKill)",
                    "confidence": 0.98
                })
                root_cause = "MEMORY_EXHAUSTION_OOM"
                confidence = 0.98
                recommended_runbook = "EVICT_CONTAINER_AND_PURGE_LEAK"
            else:
                hypotheses.append({
                    "hypothesis": "Order service process failure or unhandled exception",
                    "confidence": 0.90
                })
                root_cause = "ORDER_PROCESS_FAILURE"
                confidence = 0.90
                recommended_runbook = "ROLLING_RESTART_ORDER_SERVICE"

        # Check CPU Saturation
        elif telemetry.get("latency_ms", 0) > 1000:
            hypotheses.append({
                "hypothesis": "CPU CFS quota throttling causing request queue buildup",
                "confidence": 0.88
            })
            root_cause = "CPU_QUOTA_THROTTLING"
            confidence = 0.88
            recommended_runbook = "SCALE_WORKLOAD_REPLICAS"

        # Query active LLM with Extended Thinking for deep RCA
        prompt = f"Analyze incident:\nTelemetry: {telemetry}\nK8s Events: {events}\nFormulate hypotheses, identify primary root cause, and specify recovery runbook."
        llm_insights = self.llm.query(prompt, role="root_cause_investigator", enable_extended_thinking=True)

        report = {
            "component": "Root Cause Investigator",
            "action": "RCA_COMPLETE",
            "command": "CLAUDE_EXTENDED_THINKING_RCA --budget 1024",
            "result": f"Root Cause: {root_cause} (Confidence: {int(confidence*100)}%) -> Prescribed Runbook: {recommended_runbook}",
            "llm_provider": self.llm.active_provider,
            "llm_model": self.llm.active_model,
            "llm_reasoning": llm_insights if llm_insights else "Evaluated via high-precision SRE diagnostic rules",
            "incident_severity": incident.get("severity", "SEV-2"),
            "primary_root_cause": root_cause,
            "confidence_score": confidence,
            "hypotheses": hypotheses,
            "recommended_runbook": recommended_runbook,
            "status": "REMEDIATION_READY"
        }
        self.logger.log(report)
        return report
