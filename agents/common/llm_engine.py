import os
import httpx
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()

from agents.config import (
    MODEL_fault_STRATEGIST,
    MODEL_INFRA_DISRUPTOR,
    MODEL_NETWORK_ADVERSARY,
    MODEL_INCIDENT_MONITOR,
    MODEL_DIAGNOSTIC_RCA,
    MODEL_AUTO_REMEDIATOR,
    MODEL_POST_MORTEM
)

class EnterpriseLLMEngine:
    """
    Pure Anthropic Claude Multi-Agent Engine.
    Routes every Red and Blue team agent directly to Anthropic's frontier models:
      - Claude 3.7 Sonnet (with Extended Thinking for Diagnostic RCA)
      - Claude 3.5 Sonnet (for high-throughput sub-second telemetry scanning)
    """

    ROLE_MODELS = {
        # --- Red Team (Offensive Testing Squad) ---
        "fault_attack_planner": MODEL_fault_STRATEGIST,
        "fault_strategist": MODEL_fault_STRATEGIST,
        "planner": MODEL_fault_STRATEGIST,
        "server_resource_stresser": MODEL_INFRA_DISRUPTOR,
        "infra_disruptor": MODEL_INFRA_DISRUPTOR,
        "resource_stresser": MODEL_INFRA_DISRUPTOR,
        "network_delay_injector": MODEL_NETWORK_ADVERSARY,
        "network_adversary": MODEL_NETWORK_ADVERSARY,
        "delay_injector": MODEL_NETWORK_ADVERSARY,

        # --- Blue Team (Defensive Recovery Squad) ---
        "health_uptime_monitor": MODEL_INCIDENT_MONITOR,
        "incident_monitor": MODEL_INCIDENT_MONITOR,
        "uptime_monitor": MODEL_INCIDENT_MONITOR,
        "root_cause_investigator": MODEL_DIAGNOSTIC_RCA,
        "diagnostic_rca": MODEL_DIAGNOSTIC_RCA,
        "investigator": MODEL_DIAGNOSTIC_RCA,
        "automated_recovery_fixer": MODEL_AUTO_REMEDIATOR,
        "auto_remediator": MODEL_AUTO_REMEDIATOR,
        "recovery_fixer": MODEL_AUTO_REMEDIATOR,
        "incident_report_writer": MODEL_POST_MORTEM,
        "post_mortem": MODEL_POST_MORTEM,
        "report_writer": MODEL_POST_MORTEM,
    }

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.api_version = "2023-06-01"
        self.active_provider = "Anthropic"
        self.active_model = "claude-sonnet-4-6"

    def get_model_for_role(self, role: str) -> str:
        """Returns the specific Claude model assigned to this agent role."""
        for key, model in self.ROLE_MODELS.items():
            if key in role.lower():
                return model
        return "claude-sonnet-4-6"

    def query(self, prompt: str, system_prompt: str = "", role: str = "root_cause_investigator", enable_extended_thinking: bool = False) -> Optional[str]:
        """Sends inference request directly to Anthropic Messages API."""
        if not self.api_key:
            return None

        model_name = self.get_model_for_role(role)
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json"
        }

        payload = {
            "model": model_name,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 1.0 if enable_extended_thinking else 0.2
        }

        if system_prompt:
            payload["system"] = system_prompt

        # Enable Extended Thinking for deep RCA
        if enable_extended_thinking and "sonnet" in model_name:
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": 1024
            }

        try:
            with httpx.Client(timeout=90.0) as client:
                resp = client.post(self.api_url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text_blocks = [c.get("text", "") for c in data.get("content", []) if c.get("type") == "text"]
                    return "\n".join(text_blocks).strip()
                else:
                    print(f"[!] Anthropic API Error ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"[!] Anthropic API request failed: {e}")

        return None
