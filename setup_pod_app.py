import boto3

from agents.config import AWS_REGION, require_ec2_instance_id

ssm = boto3.client("ssm", region_name=AWS_REGION)
commands = [
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- mkdir -p /app",
    "k3s kubectl cp /opt/resilienceops/agents sre-agent-sandbox/$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-fault -o jsonpath='{.items[0].metadata.name}'):/app/agents",
    "k3s kubectl cp /opt/resilienceops/orchestrator.py sre-agent-sandbox/$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-fault -o jsonpath='{.items[0].metadata.name}'):/app/orchestrator.py",
    "k3s kubectl set env deployment/red-team-sandbox -n sre-agent-sandbox --from-literal=ANTHROPIC_API_KEY=\"${ANTHROPIC_API_KEY}\" --overwrite || true",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- pip install httpx anthropic prometheus-client python-dotenv kubernetes",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- ls -la /app"
]
resp = ssm.send_command(
    InstanceIds=[require_ec2_instance_id()],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
print("Dispatched setup command:", resp["Command"]["CommandId"])
