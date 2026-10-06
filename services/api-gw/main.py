import time
import httpx
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import os

from pydantic import BaseModel

app = FastAPI(title="ResilienceOps-API-Gateway", version="1.0.0")

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8001")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8002")

# Prometheus Metrics (Golden Signals)
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP Requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP Request Latency in seconds",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Agent Audit & Sandbox Security Metrics
AGENT_OPERATION_EVENTS = Counter(
    "sre_agent_operation_events_total",
    "Audited Agent Operations and Telemetry Events",
    ["squad", "agent", "action", "command", "result", "status"]
)
AGENT_SANDBOX_STATUS = Gauge(
    "sre_agent_sandbox_quarantine_status",
    "Kubernetes Agent Sandbox Quarantine and Security Isolation State",
    ["namespace", "cgroup_limits", "network_policy", "rbac_isolation"]
)

# Initialize Sandbox Security Status: Guaranteed Quarantined
AGENT_SANDBOX_STATUS.labels(
    namespace="sre-agent-sandbox",
    cgroup_limits="cpu_500m_mem_512Mi",
    network_policy="quarantine_egress_443_only",
    rbac_isolation="least_privilege"
).set(1)

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    endpoint = request.url.path
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as exc:
        status_code = 500
        raise exc
    finally:
        duration = time.time() - start_time
        REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=str(status_code)).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

class AgentEventRequest(BaseModel):
    squad: str
    agent: str
    action: str
    command: str = "N/A"
    result: str = "SUCCESS"
    status: str = "COMPLETED"

@app.post("/api/agent-events")
async def record_agent_event(event: AgentEventRequest):
    AGENT_OPERATION_EVENTS.labels(
        squad=event.squad,
        agent=event.agent,
        action=event.action,
        command=event.command[:120],
        result=event.result[:160],
        status=event.status
    ).inc()
    return {"status": "recorded", "event": event.dict()}

@app.api_route("/api/orders{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_orders(request: Request, path: str):
    url = f"{ORDER_SERVICE_URL}{path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=dict(request.query_params),
                content=body
            )
            return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))
        except httpx.TimeoutException:
            return Response(content='{"error": "Order service timeout (504)"}', status_code=504, media_type="application/json")
        except Exception as e:
            return Response(content=f'{{"error": "Upstream error: {str(e)}"}}', status_code=502, media_type="application/json")

@app.api_route("/api/payments{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_payments(request: Request, path: str):
    url = f"{PAYMENT_SERVICE_URL}{path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=dict(request.query_params),
                content=body
            )
            return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))
        except httpx.TimeoutException:
            return Response(content='{"error": "Payment service gateway timeout (504)"}', status_code=504, media_type="application/json")
        except Exception as e:
            return Response(content=f'{{"error": "Upstream error: {str(e)}"}}', status_code=502, media_type="application/json")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
