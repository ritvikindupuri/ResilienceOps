import time
import uuid
import subprocess
import os
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="ResilienceOps-Payment-Service", version="1.0.0")

PAYMENT_COUNT = Counter("payments_processed_total", "Total Payments Processed", ["status", "gateway"])
PAYMENT_LATENCY = Histogram("payment_processing_duration_seconds", "Latency of payment gateway", buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0])

FAULT_STATE = {
    "tc_netem_active": False,
    "tc_rule": None,
    "gateway_outage": False
}

def run_tc_command(args: list) -> dict:
    """Executes Linux Traffic Control (tc) command on eth0."""
    try:
        res = subprocess.run(["tc"] + args, capture_output=True, text=True, check=False)
        return {
            "returncode": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }
    except Exception as e:
        return {"returncode": -1, "error": str(e)}

class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    currency: str = "USD"
    payment_method: str = "credit_card"

@app.get("/health")
async def health():
    if FAULT_STATE["gateway_outage"]:
        raise HTTPException(status_code=503, detail="Payment upstream gateway unavailable")
    return {
        "status": "healthy",
        "service": "payment-service",
        "tc_netem_active": FAULT_STATE["tc_netem_active"],
        "tc_rule": FAULT_STATE["tc_rule"]
    }

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/payments")
async def process_payment(req: PaymentRequest):
    start = time.time()
    
    if FAULT_STATE["gateway_outage"]:
        PAYMENT_COUNT.labels(status="503_outage", gateway="stripe-sim").inc()
        raise HTTPException(status_code=503, detail="External Payment Gateway Connection Refused")
    
    # Process payment (real kernel-level tc netem delays and packet loss will affect TCP stack)
    tx_id = f"tx-{uuid.uuid4().hex[:10]}"
    PAYMENT_COUNT.labels(status="success", gateway="stripe-sim").inc()
    PAYMENT_LATENCY.observe(time.time() - start)
    
    return {
        "transaction_id": tx_id,
        "order_id": req.order_id,
        "amount": req.amount,
        "currency": req.currency,
        "status": "settled",
        "processed_at": time.time()
    }

# ==========================================
# Fault Engineering Endpoints (Linux tc netem)
# ==========================================

@app.post("/fault/latency")
async def set_latency(delay_ms: int = 2500, jitter_ms: int = 100):
    """Applies Linux kernel tc netem delay directly to eth0 network interface."""
    # Delete existing root qdisc if any
    run_tc_command(["qdisc", "del", "dev", "eth0", "root"])
    
    # Add netem delay
    result = run_tc_command([
        "qdisc", "add", "dev", "eth0", "root", "netem",
        "delay", f"{delay_ms}ms", f"{jitter_ms}ms"
    ])
    FAULT_STATE["tc_netem_active"] = (result["returncode"] == 0)
    FAULT_STATE["tc_rule"] = f"delay {delay_ms}ms {jitter_ms}ms"
    return {
        "status": "tc_netem_applied" if result["returncode"] == 0 else "tc_failed",
        "rule": FAULT_STATE["tc_rule"],
        "tc_output": result
    }

@app.post("/fault/drop-rate")
async def set_drop_rate(loss_percent: float = 30.0):
    """Applies Linux kernel tc netem packet drop rate to eth0."""
    run_tc_command(["qdisc", "del", "dev", "eth0", "root"])
    
    result = run_tc_command([
        "qdisc", "add", "dev", "eth0", "root", "netem",
        "loss", f"{loss_percent}%"
    ])
    FAULT_STATE["tc_netem_active"] = (result["returncode"] == 0)
    FAULT_STATE["tc_rule"] = f"loss {loss_percent}%"
    return {
        "status": "tc_netem_applied" if result["returncode"] == 0 else "tc_failed",
        "rule": FAULT_STATE["tc_rule"],
        "tc_output": result
    }

@app.post("/fault/outage")
async def set_outage(enabled: bool = True):
    FAULT_STATE["gateway_outage"] = enabled
    return {"status": "fault_applied", "gateway_outage": enabled}

@app.post("/fault/reset")
async def reset_fault():
    """Removes Linux tc netem qdisc and resets state."""
    result = run_tc_command(["qdisc", "del", "dev", "eth0", "root"])
    FAULT_STATE["tc_netem_active"] = False
    FAULT_STATE["tc_rule"] = None
    FAULT_STATE["gateway_outage"] = False
    return {
        "status": "clean",
        "message": "Linux tc netem qdisc purged and service state normalized",
        "tc_output": result
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
