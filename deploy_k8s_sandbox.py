import boto3, base64
from agents.config import AWS_REGION, require_ec2_instance_id

INSTANCE_ID = require_ec2_instance_id()


with open("k8s/agents/agent-sandbox.yaml", "rb") as f:
    b64_manifest = base64.b64encode(f.read()).decode("ascii")

ssm = boto3.client("ssm", region_name=AWS_REGION)
commands = [
    "mkdir -p /opt/sre-colosseum/k8s/agents",
    f"cat << 'EOF' | base64 -d > /opt/sre-colosseum/k8s/agents/agent-sandbox.yaml\n{b64_manifest}\nEOF",
    "k3s kubectl apply -f /opt/sre-colosseum/k8s/agents/agent-sandbox.yaml",
    "sleep 3",
    "k3s kubectl get pods -n sre-agent-sandbox -o wide"
]
resp = ssm.send_command(
    InstanceIds=[INSTANCE_ID],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
print("Dispatched sandbox manifest deployment:", resp["Command"]["CommandId"])
