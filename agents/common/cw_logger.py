import sys
import time
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from agents.config import AWS_REGION

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Setup basic Python logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sre-arena")

class CloudWatchLogger:
    def __init__(self, log_group_name: str, stream_prefix: str = "agent-stream"):
        self.log_group_name = log_group_name
        self.stream_name = f"{stream_prefix}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        self.boto_client = None
        self.sequence_token = None
        self._init_client()

    def _init_client(self):
        try:
            import boto3
            self.boto_client = boto3.client("logs", region_name=AWS_REGION)
            
            # Ensure log group exists
            try:
                self.boto_client.create_log_group(logGroupName=self.log_group_name)
            except self.boto_client.exceptions.ResourceAlreadyExistsException:
                pass

            # Create log stream
            try:
                self.boto_client.create_log_stream(
                    logGroupName=self.log_group_name,
                    logStreamName=self.stream_name
                )
            except self.boto_client.exceptions.ResourceAlreadyExistsException:
                pass

            logger.info(f"[CloudWatch] Successfully initialized stream {self.stream_name} in group {self.log_group_name}")
        except Exception as e:
            logger.warning(f"[CloudWatch] AWS credentials/boto3 not active ({e}). Streaming to console & file.")
            self.boto_client = None

    def log(self, payload: Dict[str, Any]):
        """Emits structured JSON event to CloudWatch and local console."""
        if "timestamp" not in payload:
            payload["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
        json_message = json.dumps(payload, indent=None)
        
        # Colorized console output for local observability
        role = payload.get("agent", "SYSTEM")
        action = payload.get("action", payload.get("phase", "LOG"))
        if "red" in role.lower() or "attacker" in role.lower():
            color = "\033[91m" # Red
        elif "blue" in role.lower() or "sentinel" in role.lower() or "operator" in role.lower():
            color = "\033[94m" # Blue
        else:
            color = "\033[92m" # Green
        reset = "\033[0m"

        print(f"{color}[{role.upper()}] [{action}]{reset} {json_message}")

        # Send to AWS CloudWatch if connected
        if self.boto_client:
            try:
                event = {
                    "timestamp": int(time.time() * 1000),
                    "message": json_message
                }
                kwargs = {
                    "logGroupName": self.log_group_name,
                    "logStreamName": self.stream_name,
                    "logEvents": [event]
                }
                if self.sequence_token:
                    kwargs["sequenceToken"] = self.sequence_token
                    
                resp = self.boto_client.put_log_events(**kwargs)
                self.sequence_token = resp.get("nextSequenceToken")
            except Exception as e:
                logger.error(f"[CloudWatch] Failed to push event: {e}")
