import subprocess
import time
import sys
import os

print("[*] Launching microservices stack for resilience system verification...")

env = os.environ.copy()
env["ORDER_SERVICE_URL"] = "http://127.0.0.1:8001"
env["PAYMENT_SERVICE_URL"] = "http://127.0.0.1:8002"
env["API_GATEWAY_URL"] = "http://127.0.0.1:8000"

p_order = subprocess.Popen([sys.executable, "services/order-service/main.py"], env=env)
p_payment = subprocess.Popen([sys.executable, "services/payment-service/main.py"], env=env)
time.sleep(2)
p_gw = subprocess.Popen([sys.executable, "services/api-gw/main.py"], env=env)

try:
    print("[*] Waiting for services to initialize...")
    time.sleep(3)

    print("[*] Executing Resilience Testing Cycle with Fault Injection & Auto-Remediation...")
    res = subprocess.run([
        sys.executable, "orchestrator.py",
        "--cycles", "1",
        "--scenario", "MEMORY_EXHAUSTION"
    ], env=env)
    print(f"[*] Orchestrator exited with status code: {res.returncode}")

finally:
    print("[*] Shutting down test services...")
    p_gw.terminate()
    p_order.terminate()
    p_payment.terminate()
    p_gw.wait()
    p_order.wait()
    p_payment.wait()
    print("[*] All services shut down cleanly.")
