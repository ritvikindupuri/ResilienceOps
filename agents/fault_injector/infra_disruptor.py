import time
from typing import Dict, Any
from agents.common.structured_logger import StructuredLogger
from agents.common.llm_engine import EnterpriseLLMEngine
from agents.fault_injector.fault_catalog import FaultCatalog

class InfraDisruptorAgent:
    """
    Red Team Agent 2: Infrastructure & Container Disruptor.
    Executes low-level kernel, cgroup, memory allocation, and CPU quota saturation attacks.
    Model: Claude 3.7 Sonnet
    """

    def __init__(self):
        self.logger = StructuredLogger("Server Resource Stresser")
        self.llm = EnterpriseLLMEngine()

    def execute_fault(self, fault_type: str = "MEMORY_EXHAUSTION") -> Dict[str, Any]:
        prompt = (
            f"You are executing {fault_type} against target 'order-service'. "
            "Explain the low-level Linux/cgroup mechanism that will lead to container OOMKill (Exit 137) or CFS throttling."
        )
        tactical_brief = self.llm.query(prompt, role="server_resource_stresser")

        start = time.time()
        if "CPU" in fault_type:
            result = FaultCatalog.inject_cpu_saturation(seconds=15)
        elif "CRASH" in fault_type:
            result = FaultCatalog.inject_process_crash()
        else:
            result = FaultCatalog.inject_memory_exhaustion(mb=150)

        duration_ms = (time.time() - start) * 1000

        if "CPU" in fault_type:
            cmd_str = f"POST {result.get('endpoint', '/chaos/cpu-burn')} [payload: 15s compute saturation]"
            res_str = f"HTTP {result.get('status_code', 200)} | CPU CFS quota saturated -> Worker thread starvation"
        elif "CRASH" in fault_type:
            cmd_str = f"POST {result.get('endpoint', '/chaos/process-crash')}"
            res_str = f"HTTP {result.get('status_code', 200)} | Worker process killed -> CrashLoopBackOff"
        else:
            cmd_str = f"POST {result.get('endpoint', '/chaos/leak-memory')} [payload: 150MB heap allocation]"
            res_str = f"HTTP {result.get('status_code', 200)} | Memory allocated -> cgroup ceiling breached -> Container OOMKill restart"

        event = {
            "component": "Server Resource Stresser",
            "action": "INFRA_FAULT_INJECTED",
            "fault_type": fault_type,
            "target_service": result.get("target_service", "order-service"),
            "command": cmd_str,
            "result": res_str,
            "execution_duration_ms": round(duration_ms, 2),
            "tactical_mechanism": tactical_brief if tactical_brief else "Kernel/cgroup limit breach",
            "status": "FAULT_ACTIVE"
        }
        self.logger.log(event)
        return event
