import time
from typing import Dict, Any, Optional
from agents.common.structured_logger import StructuredLogger
from agents.common.llm_engine import EnterpriseLLMEngine
from agents.fault_injector.fault_catalog import FaultCatalog

class FaultInjectorAgent:
    """Autonomous agent that injects real production faults to test system resilience."""

    def __init__(self):
        self.logger = StructuredLogger("fault-injector")
        self.llm = EnterpriseLLMEngine()
        self.scenarios = [
            ("MEMORY_EXHAUSTION", FaultCatalog.inject_memory_exhaustion, {"mb": 150}),
            ("NETWORK_LATENCY", FaultCatalog.inject_network_latency, {"seconds": 3.0}),
            ("CPU_SATURATION", FaultCatalog.inject_cpu_saturation, {"seconds": 15}),
            ("PACKET_LOSS", FaultCatalog.inject_packet_loss, {"drop_rate": 0.45}),
            ("PROCESS_CRASH", FaultCatalog.inject_process_crash, {})
        ]
        self.cursor = 0

    def trigger_scenario(self, scenario_name: Optional[str] = None) -> Dict[str, Any]:
        """Executes a fault injection scenario and logs structured telemetry."""
        if scenario_name:
            matched = next((s for s in self.scenarios if s[0].lower() == scenario_name.lower()), None)
            if not matched:
                raise ValueError(f"Unknown scenario: {scenario_name}")
            name, func, kwargs = matched
        else:
            name, func, kwargs = self.scenarios[self.cursor % len(self.scenarios)]
            self.cursor += 1

        # Query Claude / LLM for offensive chaos hypothesis
        prompt = (
            f"Target: Microservices cluster (api-gw, order-service, payment-service). "
            f"Scenario: {name}. Describe how this fault degrades upstream connection pools and breaches p99 latency SLOs."
        )
        llm_strategy = self.llm.query(prompt, role="attacker")

        # 1. Log Scenario Intent
        intent_event = {
            "component": "fault-injector",
            "phase": "SCENARIO_INITIATED",
            "scenario": name,
            "target": "target-microservices",
            "llm_provider": self.llm.provider,
            "llm_model": self.llm.model,
            "chaos_strategy": llm_strategy if llm_strategy else f"Controlled injection of {name}",
            "intent": f"Inject {name} to evaluate automated SRE detection and auto-remediation."
        }
        self.logger.log(intent_event)

        # 2. Execute Real Fault Injection
        start_time = time.time()
        result = func(**kwargs)
        duration_ms = (time.time() - start_time) * 1000

        # 3. Log Execution Result
        execution_event = {
            "component": "fault-injector",
            "phase": "EXECUTION_COMPLETE",
            "scenario": name,
            "target_service": result.get("target_service", "cluster"),
            "execution_duration_ms": round(duration_ms, 2),
            "expected_sre_impact": result.get("expected_sre_impact", ""),
            "status": "FAULT_ACTIVE"
        }
        self.logger.log(execution_event)
        return execution_event
