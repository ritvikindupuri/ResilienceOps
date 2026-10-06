import httpx
import time
from typing import Dict, Any
from agents.config import ORDER_SERVICE_URL, PAYMENT_SERVICE_URL, API_GATEWAY_URL

class ChaosVectors:
    @staticmethod
    def inject_memory_leak(mb: int = 150) -> Dict[str, Any]:
        """Injects high memory allocation into order-service to trigger cgroup OOMKill (Exit 137)."""
        url = f"{ORDER_SERVICE_URL}/chaos/leak-memory?mb={mb}"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url)
                return {
                    "vector": "MEMORY_LEAK_OOM",
                    "target": "order-service",
                    "endpoint": url,
                    "status_code": res.status_code,
                    "details": res.json() if res.status_code == 200 else res.text,
                    "expected_sre_impact": "Pod memory limits reached -> Linux OOM Killer terminates container (Exit 137) -> Pod enters CrashLoopBackOff."
                }
        except Exception as e:
            return {"vector": "MEMORY_LEAK_OOM", "error": str(e)}

    @staticmethod
    def inject_cpu_burn(seconds: int = 20) -> Dict[str, Any]:
        """Injects 100% CPU burn into order-service to trigger CFS quota throttling and latency explosion."""
        url = f"{ORDER_SERVICE_URL}/chaos/cpu-burn?seconds={seconds}"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url)
                return {
                    "vector": "CPU_STARVATION_THROTTLING",
                    "target": "order-service",
                    "endpoint": url,
                    "status_code": res.status_code,
                    "details": res.json() if res.status_code == 200 else res.text,
                    "expected_sre_impact": "Kubernetes CFS quota throttles pod -> p95/p99 latency spikes above 2000ms -> Upstream timeouts."
                }
        except Exception as e:
            return {"vector": "CPU_STARVATION_THROTTLING", "error": str(e)}

    @staticmethod
    def inject_payment_latency(seconds: float = 3.5) -> Dict[str, Any]:
        """Injects network delay in payment-service causing API Gateway 504 timeouts."""
        url = f"{PAYMENT_SERVICE_URL}/chaos/latency?seconds={seconds}"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url)
                return {
                    "vector": "CASCADING_NETWORK_LATENCY",
                    "target": "payment-service",
                    "endpoint": url,
                    "status_code": res.status_code,
                    "details": res.json() if res.status_code == 200 else res.text,
                    "expected_sre_impact": "Payment gateway processing takes >3.5s -> API Gateway 504 Gateway Timeout -> SLO error budget burns."
                }
        except Exception as e:
            return {"vector": "CASCADING_NETWORK_LATENCY", "error": str(e)}

    @staticmethod
    def inject_packet_drop(rate: float = 0.5) -> Dict[str, Any]:
        """Injects 50% packet drop rate into payment service."""
        url = f"{PAYMENT_SERVICE_URL}/chaos/drop-rate?rate={rate}"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url)
                return {
                    "vector": "PACKET_DROP_CORRUPTION",
                    "target": "payment-service",
                    "endpoint": url,
                    "status_code": res.status_code,
                    "details": res.json() if res.status_code == 200 else res.text,
                    "expected_sre_impact": "Intermittent HTTP 500 / TLS connection resets -> SLO error rate spikes above 5%."
                }
        except Exception as e:
            return {"vector": "PACKET_DROP_CORRUPTION", "error": str(e)}

    @staticmethod
    def inject_crash() -> Dict[str, Any]:
        """Immediately terminates order-service process."""
        url = f"{ORDER_SERVICE_URL}/chaos/crash"
        try:
            with httpx.Client(timeout=2.0) as client:
                try:
                    res = client.post(url)
                    details = res.text
                except httpx.RemoteProtocolError:
                    details = "Process killed before HTTP response completed"
                return {
                    "vector": "PROCESS_TERMINATION",
                    "target": "order-service",
                    "endpoint": url,
                    "details": details,
                    "expected_sre_impact": "Instant pod failure -> K8s restart backoff."
                }
        except Exception as e:
            return {"vector": "PROCESS_TERMINATION", "error": str(e)}

    @staticmethod
    def reset_all() -> Dict[str, Any]:
        """Resets all target services back to pristine baseline."""
        results = {}
        for name, base_url in [("order-service", ORDER_SERVICE_URL), ("payment-service", PAYMENT_SERVICE_URL)]:
            try:
                with httpx.Client(timeout=3.0) as client:
                    res = client.post(f"{base_url}/chaos/reset")
                    results[name] = res.json() if res.status_code == 200 else res.text
            except Exception as e:
                results[name] = str(e)
        return results
