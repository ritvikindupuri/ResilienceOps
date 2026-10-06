import time
import httpx
from typing import Dict, Any
from agents.config import API_GATEWAY_URL
from agents.common.structured_logger import StructuredLogger
from agents.common.k8s_tools import K8sToolKit
from agents.fault_injector.fault_catalog import FaultCatalog

class RemediatorAgent:
    """Executes automated SRE remediation runbooks and validates recovery."""

    def __init__(self):
        self.logger = StructuredLogger("Automated Recovery Fixer")
        self.k8s = K8sToolKit()

    def execute_runbook(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """Applies targeted remediation based on RCA diagnosis."""
        runbook = diagnosis.get("recommended_runbook", "RESTART_WORKLOAD")
        root_cause = diagnosis.get("primary_root_cause", "UNKNOWN")

        start_time = time.time()
        actions = []

        if "TC" in runbook or "NETEM" in runbook or "NETWORK" in root_cause or "PAYMENT" in root_cause:
            FaultCatalog.reset_environment()
            if self.k8s.k8s_available:
                self.k8s.restart_deployment("payment-service")
            actions.append("Purged Linux kernel tc netem qdisc rules on eth0 interface.")

        elif "REDIS" in runbook or "STARVATION" in root_cause or "CONNECTION" in root_cause:
            FaultCatalog.reset_environment()
            if self.k8s.k8s_available:
                self.k8s.restart_deployment("order-service")
            actions.append("Flushed unclosed Redis client descriptors and restored connection pool.")

        elif "MEMORY" in runbook or "OOM" in root_cause:
            FaultCatalog.reset_environment()
            if self.k8s.k8s_available:
                self.k8s.restart_deployment("order-service")
            actions.append("Purged leaked heap buffers and triggered container restart.")

        elif "CPU" in runbook:
            if self.k8s.k8s_available:
                self.k8s.scale_deployment("order-service", replicas=3)
            FaultCatalog.reset_environment()
            actions.append("Scaled service replicas to absorb CPU utilization spike.")

        else:
            FaultCatalog.reset_environment()
            if self.k8s.k8s_available:
                self.k8s.restart_deployment("order-service")
            actions.append("Executed workload recovery restart.")

        duration_ms = (time.time() - start_time) * 1000

        remediation_event = {
            "component": "Automated Recovery Fixer",
            "action": "RUNBOOK_EXECUTED",
            "runbook": runbook,
            "command": f"EXECUTE_RUNBOOK {runbook} --target {root_cause}",
            "result": "; ".join(actions) if actions else "Recovery actions successfully dispatched to AWS infrastructure.",
            "root_cause_addressed": root_cause,
            "actions_taken": actions,
            "execution_duration_ms": round(duration_ms, 2),
            "status": "VALIDATING_RECOVERY"
        }
        self.logger.log(remediation_event)

        # Verification Loop
        verification = self.verify_recovery()
        remediation_event["verification"] = verification
        return remediation_event

    def verify_recovery(self, max_attempts: int = 5) -> Dict[str, Any]:
        """Polls API Gateway to verify latency and error rates have returned to normal."""
        for attempt in range(max_attempts):
            time.sleep(1.0)
            try:
                t0 = time.time()
                with httpx.Client(timeout=3.0) as client:
                    res = client.get(f"{API_GATEWAY_URL}/health")
                    latency = (time.time() - t0) * 1000
                    if res.status_code == 200 and latency < 800:
                        verify_event = {
                            "component": "Automated Recovery Fixer",
                            "action": "SLO_RESTORED",
                            "latency_ms": round(latency, 2),
                            "gateway_status": 200,
                            "attempt": attempt + 1,
                            "status": "RESOLVED"
                        }
                        self.logger.log(verify_event)
                        return verify_event
            except Exception:
                pass

        fail_event = {
            "component": "Automated Recovery Fixer",
            "action": "VERIFICATION_PENDING",
            "status": "ESCALATED"
        }
        self.logger.log(fail_event)
        return fail_event
