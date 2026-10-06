import httpx
from typing import Dict, Any
from agents.config import ORDER_SERVICE_URL, PAYMENT_SERVICE_URL

class FaultCatalog:
    """Library of real, executable production failure scenarios."""

    @staticmethod
    def inject_memory_exhaustion(mb: int = 150) -> Dict[str, Any]:
        """Allocates real memory chunks in RAM to induce cgroup OOMKill."""
        url = f"{ORDER_SERVICE_URL}/chaos/leak-memory?mb={mb}"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url)
                return {
                    "scenario": "MEMORY_EXHAUSTION",
                    "target_service": "order-service",
                    "endpoint": url,
                    "status_code": res.status_code,
                    "details": res.json() if res.status_code == 200 else res.text,
                    "expected_sre_impact": "Container cgroup memory limit breached -> OOM killer triggers container restart."
                }
        except Exception as e:
            return {"scenario": "MEMORY_EXHAUSTION", "error": str(e)}

    @staticmethod
    def inject_cpu_saturation(seconds: int = 15) -> Dict[str, Any]:
        """Executes CPU intensive operations to trigger CFS quota throttling."""
        url = f"{ORDER_SERVICE_URL}/chaos/cpu-burn?seconds={seconds}"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url)
                return {
                    "scenario": "CPU_SATURATION",
                    "target_service": "order-service",
                    "endpoint": url,
                    "status_code": res.status_code,
                    "details": res.json() if res.status_code == 200 else res.text,
                    "expected_sre_impact": "CFS throttling degrades thread pool -> p95/p99 latency spikes above SLO threshold."
                }
        except Exception as e:
            return {"scenario": "CPU_SATURATION", "error": str(e)}

    @staticmethod
    def inject_network_latency(delay_ms: int = 2500, jitter_ms: int = 100) -> Dict[str, Any]:
        """Applies Linux kernel tc netem delay directly to payment-service eth0 interface."""
        url = f"{PAYMENT_SERVICE_URL}/chaos/latency?delay_ms={delay_ms}&jitter_ms={jitter_ms}"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url)
                return {
                    "scenario": "KERNEL_TC_NETEM_LATENCY",
                    "target_service": "payment-service",
                    "interface": "eth0",
                    "endpoint": url,
                    "status_code": res.status_code,
                    "details": res.json() if res.status_code == 200 else res.text,
                    "expected_sre_impact": "Linux kernel qdisc queues packets on eth0 -> Downstream response exceeds 2500ms -> API Gateway triggers HTTP 504 Gateway Timeout."
                }
        except Exception as e:
            return {"scenario": "KERNEL_TC_NETEM_LATENCY", "error": str(e)}

    @staticmethod
    def inject_packet_loss(loss_percent: float = 35.0) -> Dict[str, Any]:
        """Applies Linux kernel tc netem packet drop rate directly to payment-service eth0 interface."""
        url = f"{PAYMENT_SERVICE_URL}/chaos/drop-rate?loss_percent={loss_percent}"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url)
                return {
                    "scenario": "KERNEL_TC_NETEM_PACKET_LOSS",
                    "target_service": "payment-service",
                    "interface": "eth0",
                    "endpoint": url,
                    "status_code": res.status_code,
                    "details": res.json() if res.status_code == 200 else res.text,
                    "expected_sre_impact": "Linux kernel drops 35% of ingress/egress frames -> TCP retransmission backoff & connection timeouts."
                }
        except Exception as e:
            return {"scenario": "KERNEL_TC_NETEM_PACKET_LOSS", "error": str(e)}

    @staticmethod
    def inject_redis_starvation(connections: int = 55) -> Dict[str, Any]:
        """Exhausts Redis maxclients connection pool, starving backend cache queries."""
        url = f"{ORDER_SERVICE_URL}/chaos/redis-starvation?connections={connections}"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url)
                return {
                    "scenario": "REDIS_CONNECTION_STARVATION",
                    "target_service": "order-service",
                    "endpoint": url,
                    "status_code": res.status_code,
                    "details": res.json() if res.status_code == 200 else res.text,
                    "expected_sre_impact": "Redis client limits saturated -> Worker connections rejected with ConnectionError -> HTTP 503 errors."
                }
        except Exception as e:
            return {"scenario": "REDIS_CONNECTION_STARVATION", "error": str(e)}

    @staticmethod
    def inject_process_crash() -> Dict[str, Any]:
        """Simulates immediate process crash."""
        url = f"{ORDER_SERVICE_URL}/chaos/crash"
        try:
            with httpx.Client(timeout=2.0) as client:
                try:
                    res = client.post(url)
                    details = res.text
                except httpx.RemoteProtocolError:
                    details = "Process terminated immediately"
                return {
                    "scenario": "PROCESS_CRASH",
                    "target_service": "order-service",
                    "endpoint": url,
                    "details": details,
                    "expected_sre_impact": "Sudden pod outage -> Kubernetes restarts container instance."
                }
        except Exception as e:
            return {"scenario": "PROCESS_CRASH", "error": str(e)}

    @staticmethod
    def reset_environment() -> Dict[str, Any]:
        """Cleans all injected faults across services."""
        results = {}
        for name, base_url in [("order-service", ORDER_SERVICE_URL), ("payment-service", PAYMENT_SERVICE_URL)]:
            try:
                with httpx.Client(timeout=3.0) as client:
                    res = client.post(f"{base_url}/chaos/reset")
                    results[name] = res.json() if res.status_code == 200 else res.text
            except Exception as e:
                results[name] = str(e)
        return results
