import boto3

ssm = boto3.client("ssm", region_name="us-east-1")
commands = [
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- mkdir -p /app",
    "k3s kubectl cp /opt/sre-colosseum/agents sre-agent-sandbox/$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-chaos -o jsonpath='{.items[0].metadata.name}'):/app/agents",
    "k3s kubectl cp /opt/sre-colosseum/orchestrator.py sre-agent-sandbox/$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-chaos -o jsonpath='{.items[0].metadata.name}'):/app/orchestrator.py",
    "k3s kubectl cp /opt/sre-colosseum/.env sre-agent-sandbox/$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-chaos -o jsonpath='{.items[0].metadata.name}'):/app/.env",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- pip install httpx anthropic prometheus-client python-dotenv",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- ls -la /app"
]
resp = ssm.send_command(
    InstanceIds=["i-0cf1c979f2cbd01c4"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
print("Dispatched setup command:", resp["Command"]["CommandId"])
