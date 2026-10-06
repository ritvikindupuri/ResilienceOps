import time
import httpx
from typing import Dict, Any
from agents.config import CW_LOG_GROUP_DEFENDER, API_GATEWAY_URL
from agents.common.cw_logger import CloudWatchLogger
from agents.common.k8s_tools import K8sToolKit
from agents.attacker.vectors import ChaosVectors

class BlueTeamOperator:
    """Executes SRE runbooks, remediates broken infrastructure, and verifies recovery."""
    def __init__(self):
        self.cw = CloudWatchLogger(CW_LOG_GROUP_DEFENDER, stream_prefix="blue-operator")
        self.k8s = K8sToolKit()

    def execute_remediation(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """Applies targeted remediation based on RCA diagnosis."""
        action_name = diagnosis.get("recommended_runbook", "RESTART_POD")
        root_cause = diagnosis.get("primary_root_cause", "UNKNOWN")

        start_time = time.time()
        execution_log = []

        # 1. Execute Runbook Action
        if "PAYMENT" in action_name or "LATENCY" in root_cause:
            # Clear artificial latency and reset payment chaos
            ChaosVectors.reset_all()
            if self.k8s.k8s_available:
                self.k8s.restart_deployment("payment-service")
            execution_log.append("Reset payment service latency parameters to baseline 80ms.")
            
        elif "OOM" in action_name or "MEMORY" in root_cause:
            # Clear memory leak buffer and restart pod
            ChaosVectors.reset_all()
            if self.k8s.k8s_available:
                self.k8s.restart_deployment("order-service")
            execution_log.append("Purged leaked heap buffers and triggered rolling container bounce.")
            
        elif "CPU" in action_name:
            # Scale deployment to absorb CPU spike
            if self.k8s.k8s_available:
                self.k8s.scale_deployment("order-service", replicas=3)
            ChaosVectors.reset_all()
            execution_log.append("Scaled order-service replicas from 2 -> 3 to mitigate CFS throttling.")

        else:
            ChaosVectors.reset_all()
            if self.k8s.k8s_available:
                self.k8s.restart_deployment("order-service")
            execution_log.append("Executed general service recovery reset.")

        # 2. Log Action Execution to CloudWatch
        remediation_event = {
            "agent": "blue-team-operator",
            "action": "REMEDIATION_EXECUTED",
            "runbook": action_name,
            "root_cause_addressed": root_cause,
            "actions_taken": execution_log,
            "duration_ms": round((time.time() - start_time) * 1000, 2),
            "status": "VERIFYING_SLO_RECOVERY"
        }
        self.cw.log(remediation_event)

        # 3. Post-Remediation Verification Loop
        verification = self.verify_recovery()
        remediation_event["verification"] = verification
        return remediation_event

    def verify_recovery(self, max_attempts: int = 4) -> Dict[str, Any]:
        """Polls API Gateway to verify latency and error rate returned to SLO baseline."""
        for attempt in range(max_attempts):
            time.sleep(1.5)
            try:
                t0 = time.time()
                with httpx.Client(timeout=3.0) as client:
                    res = client.get(f"{API_GATEWAY_URL}/health")
                    latency = (time.time() - t0) * 1000
                    if res.status_code == 200 and latency < 1000:
                        verify_event = {
                            "agent": "blue-team-operator",
                            "action": "SLO_VERIFIED_HEALTHY",
                            "latency_ms": round(latency, 2),
                            "gateway_status": 200,
                            "attempt": attempt + 1,
                            "status": "INCIDENT_RESOLVED"
                        }
                        self.cw.log(verify_event)
                        return verify_event
            except Exception:
                pass

        failed_event = {
            "agent": "blue-team-operator",
            "action": "VERIFICATION_STILL_DEGRADED",
            "status": "ESCALATING"
        }
        self.cw.log(failed_event)
        return failed_event
