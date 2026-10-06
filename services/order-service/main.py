import os
import sys
import time
import uuid
import asyncio
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import redis

app = FastAPI(title="ResilienceOps-Order-Service", version="1.0.0")

# SRE Golden Signal Metrics
ORDER_COUNT = Counter("orders_processed_total", "Total Orders Processed", ["status"])
ORDER_LATENCY = Histogram("order_processing_duration_seconds", "Latency of order processing", buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0])
MEMORY_LEAK_GAUGE = Gauge("active_memory_leak_bytes", "Memory leaked via fault injection")
REDIS_POOL_GAUGE = Gauge("redis_active_connections_count", "Active connections to Redis cache")

import psycopg2
from psycopg2 import pool
import httpx

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = None

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, socket_timeout=2.0)
except Exception as e:
    redis_client = None

# PostgreSQL configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_USER = os.getenv("POSTGRES_USER", "sre_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "sre_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "orders_db")
pg_pool = None

try:
    pg_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB,
        connect_timeout=3
    )
    # Ensure orders table exists
    conn = pg_pool.getconn()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id VARCHAR(64) PRIMARY KEY,
                item_id VARCHAR(64),
                quantity INT,
                amount NUMERIC(10, 2),
                user_id VARCHAR(64),
                created_at DOUBLE PRECISION,
                status VARCHAR(32)
            );
        """)
        conn.commit()
    pg_pool.putconn(conn)
except Exception:
    pg_pool = None

PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8002")

# In-memory storage & state
ORDERS: Dict[str, dict] = {}
LEAKED_MEMORY_CHUNKS: List[bytes] = []
STARVED_REDIS_CLIENTS: List[Any] = []

FAULT_STATE = {
    "db_delay_seconds": 0.0,
    "error_injection_rate": 0.0,
    "is_corrupted": False,
    "redis_starvation_active": False
}

class CreateOrderRequest(BaseModel):
    item_id: str
    quantity: int
    amount: float
    user_id: str

@app.get("/health")
async def health():
    if FAULT_STATE["is_corrupted"]:
        raise HTTPException(status_code=500, detail="Service internal state corrupted")
    
    redis_status = "disabled"
    if redis_client:
        try:
            redis_client.ping()
            redis_status = "connected"
        except Exception as e:
            redis_status = f"unreachable: {str(e)[:40]}"
            
    postgres_status = "disabled"
    if pg_pool:
        try:
            conn = pg_pool.getconn()
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
            pg_pool.putconn(conn)
            postgres_status = "connected"
        except Exception as e:
            postgres_status = f"unreachable: {str(e)[:40]}"

    return {
        "status": "healthy",
        "service": "order-service",
        "orders_count": len(ORDERS),
        "redis_cache": redis_status,
        "postgres_db": postgres_status,
        "redis_starvation_active": FAULT_STATE["redis_starvation_active"]
    }

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/orders")
async def create_order(order_req: CreateOrderRequest):
    start = time.time()
    
    # Check error injection
    if FAULT_STATE["error_injection_rate"] > 0:
        import random
        if random.random() < FAULT_STATE["error_injection_rate"]:
            ORDER_COUNT.labels(status="failed_fault").inc()
            raise HTTPException(status_code=500, detail="Database connection pool timeout")
            
    # Check artificial DB delay
    if FAULT_STATE["db_delay_seconds"] > 0:
        await asyncio.sleep(FAULT_STATE["db_delay_seconds"])

    order_id = f"ord-{uuid.uuid4().hex[:8]}"
    order_data = {
        "order_id": order_id,
        "item_id": order_req.item_id,
        "quantity": order_req.quantity,
        "amount": order_req.amount,
        "user_id": order_req.user_id,
        "created_at": time.time(),
        "status": "confirmed"
    }
    
    # Persistence: Write directly to PostgreSQL database
    if pg_pool:
        try:
            conn = pg_pool.getconn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO orders (order_id, item_id, quantity, amount, user_id, created_at, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (order_id) DO NOTHING;
                    """,
                    (order_id, order_req.item_id, order_req.quantity, order_req.amount, order_req.user_id, order_data["created_at"], order_data["status"])
                )
                conn.commit()
            pg_pool.putconn(conn)
        except Exception as pge:
            pass

    # In-memory and Redis Caching Tier
    ORDERS[order_id] = order_data
    if redis_client:
        try:
            redis_client.setex(f"order:{order_id}", 300, str(order_data))
        except redis.ConnectionError as ce:
            ORDER_COUNT.labels(status="redis_starvation_error").inc()
            raise HTTPException(status_code=503, detail=f"Redis cache connection pool exhausted: {str(ce)}")

    # Downstream Order -> Payment Flow: Dispatch payment authorization to payment-service
    async with httpx.AsyncClient(timeout=6.0) as http_client:
        try:
            pay_payload = {
                "order_id": order_id,
                "amount": order_req.amount,
                "currency": "USD",
                "payment_method": "credit_card"
            }
            pay_resp = await http_client.post(f"{PAYMENT_SERVICE_URL}/payments", json=pay_payload)
            if pay_resp.status_code == 200:
                order_data["payment"] = pay_resp.json()
            elif pay_resp.status_code >= 500:
                ORDER_COUNT.labels(status="downstream_payment_failure").inc()
                order_data["status"] = "payment_failed"
        except httpx.TimeoutException:
            ORDER_COUNT.labels(status="downstream_payment_timeout").inc()
            raise HTTPException(status_code=504, detail="Payment-service upstream timeout during order settlement")
        except Exception as pe:
            ORDER_COUNT.labels(status="downstream_payment_error").inc()

    duration = time.time() - start
    ORDER_COUNT.labels(status="success").inc()
    ORDER_LATENCY.observe(duration)
    return order_data

@app.get("/orders")
async def list_orders():
    if FAULT_STATE["db_delay_seconds"] > 0:
        await asyncio.sleep(FAULT_STATE["db_delay_seconds"])
    return list(ORDERS.values())[-20:]

# ==========================================
# Fault Engineering Endpoints
# ==========================================

@app.post("/fault/redis-starvation")
async def fault_redis_starvation(connections: int = 55):
    """Spawns concurrent unclosed TCP connections to Redis to breach maxclients limit."""
    global STARVED_REDIS_CLIENTS
    STARVED_REDIS_CLIENTS.clear()
    success_count = 0
    errors = []
    
    for i in range(connections):
        try:
            client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, socket_timeout=30.0)
            client.ping()
            STARVED_REDIS_CLIENTS.append(client)
            success_count += 1
        except Exception as e:
            errors.append(str(e))
            
    FAULT_STATE["redis_starvation_active"] = True
    REDIS_POOL_GAUGE.set(success_count)
    return {
        "status": "redis_pool_starved",
        "opened_unclosed_connections": success_count,
        "errors": errors[:3],
        "detail": "Redis maxclients ceiling reached. Subsequent requests will block or raise ConnectionError."
    }

@app.post("/fault/leak-memory")
async def fault_leak_memory(mb: int = 50):
    """Allocates raw byte chunks in RAM to induce cgroup OOMKill (Exit 137)."""
    chunk = b"X" * (mb * 1024 * 1024)
    LEAKED_MEMORY_CHUNKS.append(chunk)
    total_bytes = sum(len(c) for c in LEAKED_MEMORY_CHUNKS)
    MEMORY_LEAK_GAUGE.set(total_bytes)
    return {
        "status": "memory_injected",
        "added_mb": mb,
        "total_leaked_mb": total_bytes // (1024 * 1024),
        "chunks_count": len(LEAKED_MEMORY_CHUNKS)
    }

@app.post("/fault/cpu-burn")
async def fault_cpu_burn(seconds: int = 15):
    """Spins CPU in tight mathematical loop, inducing CFS throttling and latency spikes."""
    async def burn():
        end_time = time.time() + seconds
        x = 0
        while time.time() < end_time:
            x += 1
            if x % 1000000 == 0:
                await asyncio.sleep(0.0001)
    asyncio.create_task(burn())
    return {"status": "cpu_burn_started", "duration_seconds": seconds}

@app.post("/fault/db-latency")
async def fault_db_latency(delay: float = 2.5):
    """Simulates database query degradation."""
    FAULT_STATE["db_delay_seconds"] = delay
    return {"status": "latency_injected", "db_delay_seconds": delay}

@app.post("/fault/error-rate")
async def fault_error_rate(rate: float = 0.5):
    """Simulates intermittent 500 error spikes."""
    FAULT_STATE["error_injection_rate"] = rate
    return {"status": "error_rate_injected", "rate": rate}

@app.post("/fault/crash")
async def fault_crash():
    """Immediately kills process with exit code 1."""
    def kill_soon():
        time.sleep(0.5)
        sys.exit(1)
    import threading
    threading.Thread(target=kill_soon).start()
    return {"status": "terminating_process", "signal": "SIGKILL"}

@app.post("/fault/reset")
async def fault_reset():
    """Resets all injected fault states, closes starved Redis connections."""
    global LEAKED_MEMORY_CHUNKS, STARVED_REDIS_CLIENTS
    LEAKED_MEMORY_CHUNKS.clear()
    
    # Close any lingering starved connections
    for c in STARVED_REDIS_CLIENTS:
        try:
            c.close()
        except Exception:
            pass
    STARVED_REDIS_CLIENTS.clear()
    REDIS_POOL_GAUGE.set(0)
    
    MEMORY_LEAK_GAUGE.set(0)
    FAULT_STATE["db_delay_seconds"] = 0.0
    FAULT_STATE["error_injection_rate"] = 0.0
    FAULT_STATE["is_corrupted"] = False
    FAULT_STATE["redis_starvation_active"] = False
    return {"status": "clean", "message": "All faults cleared and connection pools released"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
