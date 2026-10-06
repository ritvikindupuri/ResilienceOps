import urllib.request, json

# Re-fire the Server Resource Stresser event explicitly tagged with red-team
payload = {
    "squad": "red-team",
    "agent": "Server Resource Stresser",
    "action": "INFRA_FAULT_INJECTED",
    "detail": "cgroup heap memory allocation stress injected into order-service",
    "status": "FAULT_ACTIVE"
}
req = urllib.request.Request("http://18.232.78.253:8000/api/agent-events", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
res = urllib.request.urlopen(req)
print("Updated Red Team event response:", res.read().decode())
