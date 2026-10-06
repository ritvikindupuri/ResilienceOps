import time
import random
import asyncio
import httpx
import os
import sys

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://api-gw:8000")
RPS_TARGET = int(os.getenv("RPS_TARGET", "25"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "10"))

print(f"[*] Starting Realtime Production Workload Traffic Generator against {GATEWAY_URL} target RPS: {RPS_TARGET}")

ITEMS = [
    {"item_id": "prod-macbook-pro", "amount": 1999.00},
    {"item_id": "prod-dell-xps", "amount": 1499.00},
    {"item_id": "prod-sony-wh1000", "amount": 349.99},
    {"item_id": "prod-ergonomic-chair", "amount": 450.00},
    {"item_id": "prod-mechanical-keyboard", "amount": 180.00}
]

USERS = [f"user_{i:03d}" for i in range(1, 50)]

stats = {
    "total_requests": 0,
    "success_2xx": 0,
    "client_4xx": 0,
    "server_5xx": 0,
    "timeouts": 0,
    "latencies_ms": []
}

async def simulated_user_session(client: httpx.AsyncClient):
    user = random.choice(USERS)
    item = random.choice(ITEMS)
    
    # 1. Health check / Browse
    try:
        t0 = time.time()
        resp = await client.get(f"{GATEWAY_URL}/health", timeout=3.0)
        dt = (time.time() - t0) * 1000
        record_metric(resp.status_code, dt)
    except httpx.TimeoutException:
        record_timeout()
    except Exception:
        record_error()

    # 2. Place Order
    order_id = None
    try:
        t0 = time.time()
        order_payload = {
            "item_id": item["item_id"],
            "quantity": random.randint(1, 3),
            "amount": item["amount"],
            "user_id": user
        }
        resp = await client.post(f"{GATEWAY_URL}/api/orders/orders", json=order_payload, timeout=5.0)
        dt = (time.time() - t0) * 1000
        record_metric(resp.status_code, dt)
        if resp.status_code == 200:
            order_id = resp.json().get("order_id")
    except httpx.TimeoutException:
        record_timeout()
    except Exception:
        record_error()

    # 3. Pay for Order
    if order_id:
        try:
            t0 = time.time()
            pay_payload = {
                "order_id": order_id,
                "amount": item["amount"],
                "currency": "USD",
                "payment_method": "credit_card"
            }
            resp = await client.post(f"{GATEWAY_URL}/api/payments/payments", json=pay_payload, timeout=5.0)
            dt = (time.time() - t0) * 1000
            record_metric(resp.status_code, dt)
        except httpx.TimeoutException:
            record_timeout()
        except Exception:
            record_error()

    # 4. View Order History
    try:
        t0 = time.time()
        resp = await client.get(f"{GATEWAY_URL}/api/orders/orders", timeout=3.0)
        dt = (time.time() - t0) * 1000
        record_metric(resp.status_code, dt)
    except httpx.TimeoutException:
        record_timeout()
    except Exception:
        record_error()

def record_metric(status_code: int, duration_ms: float):
    stats["total_requests"] += 1
    stats["latencies_ms"].append(duration_ms)
    if 200 <= status_code < 300:
        stats["success_2xx"] += 1
    elif 400 <= status_code < 500:
        stats["client_4xx"] += 1
    elif 500 <= status_code < 600:
        stats["server_5xx"] += 1
    if len(stats["latencies_ms"]) > 1000:
        stats["latencies_ms"] = stats["latencies_ms"][-1000:]

def record_timeout():
    stats["total_requests"] += 1
    stats["timeouts"] += 1
    stats["server_5xx"] += 1

def record_error():
    stats["total_requests"] += 1
    stats["server_5xx"] += 1

async def worker(queue: asyncio.Queue, client: httpx.AsyncClient):
    while True:
        await queue.get()
        try:
            await simulated_user_session(client)
        except Exception as e:
            pass
        finally:
            queue.task_done()

async def reporter():
    while True:
        await asyncio.sleep(5)
        total = stats["total_requests"]
        s2 = stats["success_2xx"]
        s5 = stats["server_5xx"]
        lats = sorted(stats["latencies_ms"])
        p50 = lats[int(len(lats) * 0.5)] if lats else 0
        p95 = lats[int(len(lats) * 0.95)] if lats else 0
        p99 = lats[int(len(lats) * 0.99)] if lats else 0
        err_rate = (s5 / total * 100) if total > 0 else 0
        print(f"[METRICS] Total: {total} | 2xx: {s2} | 5xx: {s5} (Err: {err_rate:.1f}%) | Latency p50: {p50:.1f}ms, p95: {p95:.1f}ms, p99: {p99:.1f}ms")

async def main():
    queue = asyncio.Queue(maxsize=100)
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    async with httpx.AsyncClient(limits=limits) as client:
        # Spawn workers
        workers = [asyncio.create_task(worker(queue, client)) for _ in range(CONCURRENCY)]
        asyncio.create_task(reporter())
        
        # Dispatch sessions at target rate
        delay = 1.0 / RPS_TARGET
        while True:
            await queue.put(True)
            await asyncio.sleep(delay)

if __name__ == "__main__":
    asyncio.run(main())
