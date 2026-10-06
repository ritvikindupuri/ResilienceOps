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

# ==============================================================================
# PURE ANTHROPIC CLAUDE MULTI-AGENT SPECIFICATION
# ==============================================================================
# Red Team (Offensive Squad):
MODEL_CHAOS_STRATEGIST = os.getenv("MODEL_CHAOS_STRATEGIST", "claude-sonnet-4-6")
MODEL_INFRA_DISRUPTOR = os.getenv("MODEL_INFRA_DISRUPTOR", "claude-sonnet-4-6")
MODEL_NETWORK_ADVERSARY = os.getenv("MODEL_NETWORK_ADVERSARY", "claude-haiku-4-5-20251001")

# Blue Team (Defensive Squad):
MODEL_INCIDENT_MONITOR = os.getenv("MODEL_INCIDENT_MONITOR", "claude-haiku-4-5-20251001")
MODEL_DIAGNOSTIC_RCA = os.getenv("MODEL_DIAGNOSTIC_RCA", "claude-sonnet-4-6")
MODEL_AUTO_REMEDIATOR = os.getenv("MODEL_AUTO_REMEDIATOR", "claude-sonnet-4-6")
MODEL_POST_MORTEM = os.getenv("MODEL_POST_MORTEM", "claude-sonnet-4-6")
