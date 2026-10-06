import subprocess
import time
import sys
import os

print("[*] Launching target microservices for live duel verification...")

env = os.environ.copy()
env["ORDER_SERVICE_URL"] = "http://127.0.0.1:8001"
env["PAYMENT_SERVICE_URL"] = "http://127.0.0.1:8002"
env["API_GATEWAY_URL"] = "http://127.0.0.1:8000"

p_order = subprocess.Popen([sys.executable, "services/order-service/main.py"], env=env)
p_payment = subprocess.Popen([sys.executable, "services/payment-service/main.py"], env=env)
time.sleep(2)
p_gw = subprocess.Popen([sys.executable, "services/api-gw/main.py"], env=env)

try:
    print("[*] Waiting for services to become healthy...")
    time.sleep(3)
    
    # Run 1 arena battle round
    print("[*] Starting Arena Battle Round 1...")
    res = subprocess.run([sys.executable, "arena_runner.py", "--rounds", "1", "--vector", "CASCADING_NETWORK_LATENCY"], env=env)
    print(f"[*] Arena runner exited with code: {res.returncode}")

finally:
    print("[*] Terminating test microservices...")
    p_gw.terminate()
    p_order.terminate()
    p_payment.terminate()
    p_gw.wait()
    p_order.wait()
    p_payment.wait()
    print("[*] All services terminated successfully.")
