import time
import httpx
from typing import Dict, Any, Optional
from agents.config import (
    API_GATEWAY_URL,
    ORDER_SERVICE_URL,
    PAYMENT_SERVICE_URL,
    PROMETHEUS_URL,
    SLO_MAX_P99_LATENCY_MS,
    SLO_MAX_ERROR_RATE_PERCENT
)
from agents.common.structured_logger import StructuredLogger


def query_prometheus_scalar(query: str) -> Optional[float]:
    """Best-effort Prometheus instant query. Returns None if Prometheus is unreachable."""
    try:
        with httpx.Client(timeout=2.0) as client:
            res = client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
            result = res.json().get("data", {}).get("result", [])
            if result:
                return float(result[0]["value"][1])
    except Exception:
        return None
    return None


def probe_error_rate_percent(snapshot: Dict[str, Any]) -> float:
    statuses = [snapshot.get(f"{svc}_status", 200) for svc in ("gateway", "order", "payment")]
    if not statuses:
        return 0.0
    return 100.0 * sum(1 for code in statuses if code >= 500) / len(statuses)

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
            "probe_latency_ms": 0.0,
            "error_rate_percent": 0.0,
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

        snapshot["probe_latency_ms"] = snapshot["latency_ms"]
        p99_seconds = query_prometheus_scalar(
            "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[1m])) by (le))"
        )
        if p99_seconds is not None:
            snapshot["p99_latency_ms"] = round(p99_seconds * 1000.0, 2)

        prom_error_rate = query_prometheus_scalar(
            '100 * (sum(rate(http_requests_total{status=~"5.."}[1m])) or vector(0)) '
            "/ clamp_min(sum(rate(http_requests_total[1m])), 1e-9)"
        )
        snapshot["error_rate_percent"] = (
            round(prom_error_rate, 3) if prom_error_rate is not None else probe_error_rate_percent(snapshot)
        )
        return snapshot

    def evaluate_slos(self, snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluates whether current telemetry breaches SLO thresholds."""
        violations = []
        severity = "SEV-2"

        # Single health-probe latency is not p99. Use Prometheus p99 when present.
        if "p99_latency_ms" in snapshot:
            latency_ms = snapshot["p99_latency_ms"]
            latency_label = "p99 latency"
        else:
            latency_ms = snapshot.get("probe_latency_ms", snapshot.get("latency_ms", 0.0))
            latency_label = "probe latency"
        if latency_ms > SLO_MAX_P99_LATENCY_MS:
            violations.append(
                f"{latency_label} ({latency_ms}ms) exceeded SLO limit ({SLO_MAX_P99_LATENCY_MS}ms)"
            )
            severity = "SEV-1"

        error_rate = snapshot.get("error_rate_percent")
        if error_rate is None:
            error_rate = probe_error_rate_percent(snapshot)
            snapshot["error_rate_percent"] = error_rate
        if error_rate > SLO_MAX_ERROR_RATE_PERCENT:
            violations.append(
                f"error rate ({error_rate:.2f}%) exceeded SLO limit ({SLO_MAX_ERROR_RATE_PERCENT}%)"
            )
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
