import boto3

# We will just write the files directly into the pod from local on host
ssm = boto3.client("ssm", region_name="us-east-1")
commands = [
    "pod_name=$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-chaos -o jsonpath='{.items[0].metadata.name}')",
    "echo \"Target Pod: $pod_name\"",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- apt-get update -y",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- apt-get install -y curl",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- mkdir -p /app",
    "echo '=== [TEST 1] VERIFY QUARANTINED CGROUP MEMORY CEILING INSIDE POD ==='",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- cat /sys/fs/cgroup/memory.max 2>/dev/null || k3s kubectl exec $pod_name -n sre-agent-sandbox -- cat /sys/fs/cgroup/memory/memory.limit_in_bytes",
    "echo '=== [TEST 2] PROBE TARGET APP FROM INSIDE QUARANTINED POD ==='",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- curl -s http://10.0.1.69:8000/health",
    "echo ''",
    "echo '=== [TEST 3] FIRE ATTACK DIRECTLY FROM INSIDE THE SANDBOX POD ==='",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- curl -s -X POST 'http://10.0.1.69:8001/chaos/leak-memory?mb=150'",
    "echo ''",
    "echo '=== [TEST 4] FIRE REMEDIATION DIRECTLY FROM INSIDE THE SANDBOX POD ==='",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- curl -s -X POST 'http://10.0.1.69:8001/chaos/reset'"
]
resp = ssm.send_command(
    InstanceIds=["i-0cf1c979f2cbd01c4"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
cmd_id = resp["Command"]["CommandId"]
print("Live sandbox commands dispatched:", cmd_id)
