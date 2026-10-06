import sys
import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class StructuredLogger:
    def __init__(self, component_name: str, log_filename: str = "agent_activity.jsonl"):
        self.component_name = component_name
        self.logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        self.log_filepath = os.path.join(self.logs_dir, log_filename)

    def log(self, event_data: Dict[str, Any]):
        """Records structured telemetry event to JSONL file and formatted console."""
        if "timestamp" not in event_data:
            event_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        if "component" not in event_data:
            event_data["component"] = self.component_name

        json_record = json.dumps(event_data)

        # Append to structured log file
        try:
            with open(self.log_filepath, "a", encoding="utf-8") as f:
                f.write(json_record + "\n")
        except Exception:
            pass

        # Clean enterprise console output
        role = event_data.get("component", self.component_name).upper()
        action = event_data.get("action", event_data.get("phase", "INFO"))
        print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] [{role}] [{action}] {json_record}")

        # Non-blocking stream to Prometheus via API Gateway if reachable
        try:
            import urllib.request
            gateway_url = os.getenv("API_GATEWAY_URL", os.getenv("GATEWAY_URL", "http://localhost:8000"))
            c_lower = self.component_name.lower()
            if any(k in c_lower for k in ["red", "chaos", "disrupt", "adversary", "fault", "stresser", "injector"]):
                squad = "red-team"
            else:
                squad = "blue-team"
            
            # Extract exact command and exact result
            exact_command = str(event_data.get("command", event_data.get("endpoint", event_data.get("runbook", event_data.get("fault_type", action)))))
            exact_result = str(event_data.get("result", event_data.get("tactical_mechanism", event_data.get("actions_taken", event_data.get("details", event_data.get("status", "SUCCESS"))))))
            
            payload = json.dumps({
                "squad": squad,
                "agent": self.component_name,
                "action": str(action),
                "command": exact_command[:120],
                "result": exact_result[:160],
                "status": str(event_data.get("status", "SUCCESS"))
            }).encode("utf-8")
            req = urllib.request.Request(f"{gateway_url}/api/agent-events", data=payload, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=1.0)
        except Exception:
            pass

        # Stream directly to AWS CloudWatch Logs in real time
        try:
            import boto3
            cw_logs = boto3.client("logs", region_name="us-east-1")
            cw_event = {
                "timestamp": int(time.time() * 1000),
                "message": json.dumps({
                    "squad": squad,
                    "agent": self.component_name,
                    "action": str(action),
                    "exact_command_executed": exact_command,
                    "exact_execution_output": exact_result,
                    "status": str(event_data.get("status", "SUCCESS")),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            }
            cw_logs.put_log_events(
                logGroupName="/sre/autonomous-agent-audit",
                logStreamName="audit-stream",
                logEvents=[cw_event]
            )
        except Exception:
            pass
