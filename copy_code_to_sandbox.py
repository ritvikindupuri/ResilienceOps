import boto3

from agents.config import AWS_REGION, require_ec2_instance_id

SANDBOX_POD = (
    "$(k3s kubectl get pod -n sre-agent-sandbox "
    "-l agent.role=red-team-fault "
    "-o jsonpath='{.items[0].metadata.name}')"
)

ssm = boto3.client("ssm", region_name=AWS_REGION)
commands = [
    # Copy project code into the pod. Do not copy .env — inject secrets from
    # the host environment / SSM Parameter Store / Secrets Manager instead.
    f"k3s kubectl cp /opt/sre-colosseum/agents sre-agent-sandbox/{SANDBOX_POD}:/app/agents",
    f"k3s kubectl cp /opt/sre-colosseum/orchestrator.py sre-agent-sandbox/{SANDBOX_POD}:/app/orchestrator.py",
    "k3s kubectl set env deployment/red-team-sandbox -n sre-agent-sandbox "
    "--from-literal=ANTHROPIC_API_KEY=\"${ANTHROPIC_API_KEY}\" --overwrite || true",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- pip install httpx anthropic prometheus-client python-dotenv kubernetes",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- ls -la /app",
]
resp = ssm.send_command(
    InstanceIds=[require_ec2_instance_id()],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands},
)
print("Code sync into sandbox pod dispatched:", resp["Command"]["CommandId"])
