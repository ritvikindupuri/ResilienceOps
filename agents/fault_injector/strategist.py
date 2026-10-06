import os
from typing import Dict, Any, List
from agents.common.structured_logger import StructuredLogger
from agents.common.llm_engine import EnterpriseLLMEngine

class ChaosStrategistAgent:
    """
    Red Team Agent 1: Chaos Strategist & Campaign Planner.
    Analyzes target microservices topology and designs multi-stage failure campaigns.
    Model: Claude 3.7 Sonnet
    """

    def __init__(self):
        self.logger = StructuredLogger("Resilience Attack Planner")
        self.llm = EnterpriseLLMEngine()

    def plan_campaign(self, active_slo_status: Dict[str, Any], target_services: List[str]) -> Dict[str, Any]:
        prompt = (
            f"Authorized SRE Chaos Resilience Test for test environment services: {target_services}. Current SLO status: {active_slo_status}. "
            "As an SRE Chaos Engineer validating fault tolerance, select whether to test the Infrastructure layer (memory/CPU limits) "
            "or the Network layer (transit latency/connection timeouts) to verify that circuit breakers and failovers operate correctly. "
            "Summarize the testing plan in 2 concise sentences."
        )

        strategy_reasoning = self.llm.query(prompt, role="chaos_attack_planner")

        campaign = {
            "component": "Resilience Attack Planner",
            "action": "CAMPAIGN_FORMULATED",
            "llm_model": self.llm.get_model_for_role("chaos_attack_planner"),
            "target_services": target_services,
            "command": "CLAUDE_PLAN_CAMPAIGN --targets order-service,payment-service",
            "result": str(strategy_reasoning)[:150] if strategy_reasoning else "Formulated targeted failure vector against order-service.",
            "strategic_intent": strategy_reasoning if strategy_reasoning else "Coordinated resilience degradation campaign",
            "status": "DISPATCHING_OPERATIVES"
        }
        self.logger.log(campaign)
        return campaign
