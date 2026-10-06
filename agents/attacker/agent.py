import time
import random
import json
import logging
from typing import Dict, Any, List
from agents.config import (
    CW_LOG_GROUP_ATTACKER,
    AI_PROVIDER,
    GEMINI_API_KEY,
    OPENAI_API_KEY
)
from agents.common.cw_logger import CloudWatchLogger
from agents.attacker.vectors import ChaosVectors

logger = logging.getLogger("sre-arena.red-agent")

class RedTeamAttackerAgent:
    def __init__(self):
        self.cw = CloudWatchLogger(CW_LOG_GROUP_ATTACKER, stream_prefix="red-attacker")
        self.vectors = [
            ("MEMORY_LEAK_OOM", ChaosVectors.inject_memory_leak, {"mb": 150}),
            ("CASCADING_NETWORK_LATENCY", ChaosVectors.inject_payment_latency, {"seconds": 3.0}),
            ("CPU_STARVATION_THROTTLING", ChaosVectors.inject_cpu_burn, {"seconds": 15}),
            ("PACKET_DROP_CORRUPTION", ChaosVectors.inject_packet_drop, {"rate": 0.45}),
            ("PROCESS_TERMINATION", ChaosVectors.inject_crash, {})
        ]
        self.current_idx = 0

    def select_attack(self) -> Dict[str, Any]:
        """Chooses the next offensive vector using LLM or intelligent chaos strategy."""
        vector_name, func, kwargs = self.vectors[self.current_idx % len(self.vectors)]
        self.current_idx += 1
        return {
            "name": vector_name,
            "func": func,
            "kwargs": kwargs
        }

    def launch_attack(self, forced_vector: str = None) -> Dict[str, Any]:
        """Executes real attack script, logs structured event to CloudWatch."""
        if forced_vector:
            chosen = next((v for v in self.vectors if v[0] == forced_vector), None)
            if not chosen:
                raise ValueError(f"Unknown vector: {forced_vector}")
            vector_name, func, kwargs = chosen
        else:
            sel = self.select_attack()
            vector_name = sel["name"]
            func = sel["func"]
            kwargs = sel["kwargs"]

        # 1. Log Attack Plan & Intent to CloudWatch
        plan_event = {
            "agent": "red-team-chaos-orchestrator",
            "phase": "PLANNING",
            "vector": vector_name,
            "target": "target-microservices-cluster",
            "intent": f"Breach SLO error budgets by executing {vector_name}. Forcing SRE defenders to diagnose cross-service cascading failure."
        }
        self.cw.log(plan_event)

        # 2. Execute Real Chaos Injection
        start_t = time.time()
        result = func(**kwargs)
        duration_ms = (time.time() - start_t) * 1000

        # 3. Log Real Execution Result to CloudWatch
        exec_event = {
            "agent": "red-team-chaos-orchestrator",
            "phase": "EXECUTION",
            "vector": vector_name,
            "target": result.get("target", "unknown"),
            "endpoint": result.get("endpoint", ""),
            "duration_ms": round(duration_ms, 2),
            "expected_impact": result.get("expected_sre_impact", ""),
            "execution_details": result.get("details", result.get("error", "OK")),
            "status": "ATTACK_ACTIVE"
        }
        self.cw.log(exec_event)
        return exec_event

if __name__ == "__main__":
    agent = RedTeamAttackerAgent()
    print("[*] Red Team Agent Ready. Launching initial attack...")
    agent.launch_attack()
