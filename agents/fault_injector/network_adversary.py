import time
from typing import Dict, Any
from agents.common.structured_logger import StructuredLogger
from agents.common.llm_engine import EnterpriseLLMEngine
from agents.fault_injector.fault_catalog import FaultCatalog

class NetworkAdversaryAgent:
    """
    Red Team Agent 3: Network & Traffic Adversary.
    Executes network latency, jitter, packet loss, and upstream gateway timeout attacks.
    Model: Claude 3.5 Sonnet
    """

    def __init__(self):
        self.logger = StructuredLogger("Network Delay Injector")
        self.llm = EnterpriseLLMEngine()

    def execute_fault(self, fault_type: str = "NETWORK_LATENCY") -> Dict[str, Any]:
        prompt = (
            f"You are injecting Linux kernel Traffic Control ({fault_type}) via 'tc netem' directly into downstream 'payment-service' eth0. "
            "Explain how kernel queueing discipline (qdisc) delay and frame drops cascade to upstream API Gateway 504 Gateway Timeouts."
        )
        tactical_brief = self.llm.query(prompt, role="network_delay_injector")

        start = time.time()
        if "PACKET" in fault_type or "DROP" in fault_type:
            result = FaultCatalog.inject_packet_loss(loss_percent=35.0)
        else:
            result = FaultCatalog.inject_network_latency(delay_ms=2500, jitter_ms=100)

        duration_ms = (time.time() - start) * 1000

        event = {
            "component": "Network Delay Injector",
            "action": "KERNEL_NETEM_FAULT_INJECTED",
            "fault_type": fault_type,
            "target_service": result.get("target_service", "payment-service"),
            "command": f"tc qdisc add dev eth0 root netem [rule: {fault_type}]",
            "result": f"HTTP {result.get('status_code', 200)} | Linux tc netem active on eth0 -> Kernel queue packet delay/loss",
            "execution_duration_ms": round(duration_ms, 2),
            "tactical_mechanism": tactical_brief if tactical_brief else "Linux kernel Traffic Control (tc netem) qdisc packet manipulation",
            "status": "FAULT_ACTIVE"
        }
        self.logger.log(event)
        return event
