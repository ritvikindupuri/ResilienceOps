import boto3, time

ssm = boto3.client("ssm", region_name="us-east-1")
commands = [
    # Tar and copy agents directory and orchestrator.py into sandbox pod
    "cd /opt/sre-colosseum && tar -czf /tmp/agents.tar.gz agents orchestrator.py",
    "k3s kubectl cp /tmp/agents.tar.gz sre-agent-sandbox/$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-chaos -o jsonpath='{.items[0].metadata.name}'):/app/agents.tar.gz",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- tar -xzf /app/agents.tar.gz -C /app",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- ls -la /app",
    # Execute a live agent cycle from INSIDE the quarantined pod
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- python /app/orchestrator.py --target-ip 10.0.1.69 --cycles 1 --scenario MEMORY_EXHAUSTION"
]
resp = ssm.send_command(
    InstanceIds=["i-0cf1c979f2cbd01c4"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
cmd_id = resp["Command"]["CommandId"]
print("Live sandbox pod execution command dispatched:", cmd_id)
