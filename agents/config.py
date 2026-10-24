import os

# Target Microservice Endpoints
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8001")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8002")

# Observability Configuration (Grafana + Prometheus)
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
LOGS_DIR = os.getenv("LOGS_DIR", "logs")

# SRE SLO Thresholds
SLO_MAX_P99_LATENCY_MS = float(os.getenv("SLO_MAX_P99_LATENCY_MS", "1200.0"))
SLO_MAX_ERROR_RATE_PERCENT = float(os.getenv("SLO_MAX_ERROR_RATE_PERCENT", "2.0"))

# AWS / CloudWatch (imported by defender, attacker, cw_logger)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
CW_LOG_GROUP_ATTACKER = os.getenv("CW_LOG_GROUP_ATTACKER", "/sre/autonomous-agent-audit")
CW_LOG_GROUP_DEFENDER = os.getenv("CW_LOG_GROUP_DEFENDER", "/sre/autonomous-agent-audit")
CW_LOG_GROUP_INCIDENTS = os.getenv("CW_LOG_GROUP_INCIDENTS", "/sre/autonomous-agent-incidents")

# Optional / unused-by-default providers
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ==============================================================================
# PURE ANTHROPIC CLAUDE MULTI-AGENT SPECIFICATION
# ==============================================================================
# Red Team (Offensive Squad):
MODEL_fault_STRATEGIST = os.getenv("MODEL_fault_STRATEGIST", "claude-sonnet-4-6")
MODEL_INFRA_DISRUPTOR = os.getenv("MODEL_INFRA_DISRUPTOR", "claude-sonnet-4-6")
MODEL_NETWORK_ADVERSARY = os.getenv("MODEL_NETWORK_ADVERSARY", "claude-haiku-4-5-20251001")

# Blue Team (Defensive Squad):
MODEL_INCIDENT_MONITOR = os.getenv("MODEL_INCIDENT_MONITOR", "claude-haiku-4-5-20251001")
MODEL_DIAGNOSTIC_RCA = os.getenv("MODEL_DIAGNOSTIC_RCA", "claude-sonnet-4-6")
MODEL_AUTO_REMEDIATOR = os.getenv("MODEL_AUTO_REMEDIATOR", "claude-sonnet-4-6")
MODEL_POST_MORTEM = os.getenv("MODEL_POST_MORTEM", "claude-sonnet-4-6")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", MODEL_DIAGNOSTIC_RCA)


def require_ec2_instance_id() -> str:
    """Return the target EC2 instance id or raise a clear error if unset."""
    value = (os.getenv("EC2_INSTANCE_ID") or os.getenv("SRE_EC2_INSTANCE_ID") or "").strip()
    if not value:
        raise RuntimeError(
            "EC2_INSTANCE_ID is not set. Export the target instance id before "
            "running deploy or SSM helper scripts, for example: "
            "export EC2_INSTANCE_ID=i-xxxxxxxxxxxxxxxxx"
        )
    return value


def require_grafana_basic_auth_header() -> str:
    """Build a Grafana Basic auth header from env vars. No default password."""
    import base64

    user = os.getenv("GRAFANA_ADMIN_USER", "").strip()
    password = os.getenv("GRAFANA_ADMIN_PASSWORD", "").strip()
    if not user or not password:
        raise RuntimeError(
            "GRAFANA_ADMIN_USER and GRAFANA_ADMIN_PASSWORD must be set. "
            "There is no default admin password."
        )
    token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"
