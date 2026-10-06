import time
import httpx
from typing import Dict, Any, Optional
from agents.config import (
    API_GATEWAY_URL,
    ORDER_SERVICE_URL,
    PAYMENT_SERVICE_URL,
    SLO_MAX_P99_LATENCY_MS,
    SLO_MAX_ERROR_RATE_PERCENT
)
from agents.common.structured_logger import StructuredLogger

class IncidentMonitor:
    """Continuously monitors service telemetry and declares incidents on SLO violations."""

    def __init__(self):
        self.logger = StructuredLogger("Health & Uptime Monitor")

    def inspect_telemetry(self) -> Dict[str, Any]:
        """Polls endpoints to gather live latency and service availability."""
        snapshot = {
            "gateway_status": 200,
            "order_status": 200,
            "payment_status": 200,
            "latency_ms": 0.0,
            "anomalies": []
        }

        # 1. API Gateway Probe
        try:
            t0 = time.time()
            with httpx.Client(timeout=4.0) as client:
                res = client.get(f"{API_GATEWAY_URL}/health")
                snapshot["latency_ms"] = round((time.time() - t0) * 1000, 2)
                snapshot["gateway_status"] = res.status_code
                if res.status_code != 200:
                    snapshot["anomalies"].append(f"Gateway returned HTTP {res.status_code}")
        except httpx.TimeoutException:
            snapshot["gateway_status"] = 504
            snapshot["latency_ms"] = 4000.0
            snapshot["anomalies"].append("Gateway request timeout (>4000ms)")
        except Exception as e:
            snapshot["gateway_status"] = 502
            snapshot["anomalies"].append(f"Gateway connection failure: {str(e)}")

        # 2. Order Service Probe
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{ORDER_SERVICE_URL}/health")
                snapshot["order_status"] = res.status_code
                if res.status_code != 200:
                    snapshot["anomalies"].append(f"Order service degraded: HTTP {res.status_code}")
        except httpx.TimeoutException:
            snapshot["order_status"] = 504
            snapshot["anomalies"].append("Order service timeout")
        except Exception as e:
            snapshot["order_status"] = 502
            snapshot["anomalies"].append(f"Order service unreachable: {str(e)}")

        # 3. Payment Service Probe
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{PAYMENT_SERVICE_URL}/health")
                snapshot["payment_status"] = res.status_code
                if res.status_code != 200:
                    snapshot["anomalies"].append(f"Payment service degraded: HTTP {res.status_code}")
        except httpx.TimeoutException:
            snapshot["payment_status"] = 504
            snapshot["anomalies"].append("Payment service timeout")
        except Exception as e:
            snapshot["payment_status"] = 502
            snapshot["anomalies"].append(f"Payment service unreachable: {str(e)}")

        return snapshot

    def evaluate_slos(self, snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluates whether current telemetry breaches SLO thresholds."""
        violations = []
        severity = "SEV-2"

        if snapshot["latency_ms"] > SLO_MAX_P99_LATENCY_MS:
            violations.append(f"p99 Latency ({snapshot['latency_ms']}ms) exceeded SLO limit ({SLO_MAX_P99_LATENCY_MS}ms)")
            severity = "SEV-1"

        for svc in ["gateway", "order", "payment"]:
            code = snapshot.get(f"{svc}_status", 200)
            if code >= 500:
                violations.append(f"{svc}-service returned server error HTTP {code}")
                severity = "SEV-1"

        if violations:
            incident = {
                "component": "Health & Uptime Monitor",
                "action": "INCIDENT_DECLARED",
                "severity": severity,
                "command": "EVALUATE_SLO_TELEMETRY --thresholds p99_latency>1200ms,error_rate>2%",
                "result": f"SLO BREACH ({severity}): " + "; ".join(violations)[:120],
                "violations": violations,
                "telemetry": snapshot,
                "status": "INVESTIGATING"
            }
            self.logger.log(incident)
            return incident

        return None
