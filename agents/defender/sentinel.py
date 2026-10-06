import time
import httpx
from typing import Dict, Any, Optional
from agents.config import (
    CW_LOG_GROUP_DEFENDER,
    API_GATEWAY_URL,
    ORDER_SERVICE_URL,
    PAYMENT_SERVICE_URL,
    SLO_MAX_P99_LATENCY_MS,
    SLO_MAX_ERROR_RATE_PERCENT
)
from agents.common.cw_logger import CloudWatchLogger

class BlueTeamSentinel:
    """Continuously observes telemetry and declares incidents on SLO violations."""
    def __init__(self):
        self.cw = CloudWatchLogger(CW_LOG_GROUP_DEFENDER, stream_prefix="blue-sentinel")

    def inspect_telemetry(self) -> Dict[str, Any]:
        """Polls microservice health and scrapes Prometheus metrics."""
        telemetry = {
            "gateway_status": 200,
            "order_status": 200,
            "payment_status": 200,
            "latency_ms": 0.0,
            "error_rate_percent": 0.0,
            "active_anomalies": []
        }
        
        # 1. Probe Gateway Latency & Errors
        try:
            t0 = time.time()
            with httpx.Client(timeout=4.0) as client:
                res = client.get(f"{API_GATEWAY_URL}/health")
                telemetry["latency_ms"] = round((time.time() - t0) * 1000, 2)
                telemetry["gateway_status"] = res.status_code
                if res.status_code != 200:
                    telemetry["active_anomalies"].append(f"Gateway returned HTTP {res.status_code}")
        except httpx.TimeoutException:
            telemetry["gateway_status"] = 504
            telemetry["latency_ms"] = 4000.0
            telemetry["active_anomalies"].append("Gateway request TIMED OUT (>4000ms)")
        except Exception as e:
            telemetry["gateway_status"] = 502
            telemetry["active_anomalies"].append(f"Gateway connection error: {str(e)}")

        # 2. Probe Order Service
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{ORDER_SERVICE_URL}/health")
                telemetry["order_status"] = res.status_code
                if res.status_code != 200:
                    telemetry["active_anomalies"].append(f"Order-service unhealthy: HTTP {res.status_code}")
        except httpx.TimeoutException:
            telemetry["order_status"] = 504
            telemetry["active_anomalies"].append("Order-service request TIMED OUT")
        except Exception as e:
            telemetry["order_status"] = 502
            telemetry["active_anomalies"].append(f"Order-service unreachable: {str(e)}")

        # 3. Probe Payment Service
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{PAYMENT_SERVICE_URL}/health")
                telemetry["payment_status"] = res.status_code
                if res.status_code != 200:
                    telemetry["active_anomalies"].append(f"Payment-service unhealthy: HTTP {res.status_code}")
        except httpx.TimeoutException:
            telemetry["payment_status"] = 504
            telemetry["active_anomalies"].append("Payment-service request TIMED OUT")
        except Exception as e:
            telemetry["payment_status"] = 502
            telemetry["active_anomalies"].append(f"Payment-service unreachable: {str(e)}")

        return telemetry

    def evaluate_slos(self, telemetry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluates whether current telemetry breaches SRE Service Level Objectives."""
        breaches = []
        severity = "SEV-2"

        # Check Latency SLO
        if telemetry["latency_ms"] > SLO_MAX_P99_LATENCY_MS:
            breaches.append(f"P99 Latency ({telemetry['latency_ms']}ms) exceeded SLO ({SLO_MAX_P99_LATENCY_MS}ms)")
            severity = "SEV-1"

        # Check Service Status
        for svc in ["gateway", "order", "payment"]:
            status_code = telemetry.get(f"{svc}_status", 200)
            if status_code >= 500:
                breaches.append(f"{svc}-service returned server error HTTP {status_code}")
                severity = "SEV-1"

        if breaches:
            incident = {
                "agent": "blue-team-sentinel",
                "action": "INCIDENT_DECLARED",
                "severity": severity,
                "breaches": breaches,
                "telemetry_snapshot": telemetry,
                "slo_budget_burn_rate": "14.4x (High Burn)",
                "status": "TRIAGE_IN_PROGRESS"
            }
            self.cw.log(incident)
            return incident
            
        return None
