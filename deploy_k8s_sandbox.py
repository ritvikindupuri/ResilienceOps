import boto3, base64

with open("k8s/agents/agent-sandbox.yaml", "rb") as f:
    b64_manifest = base64.b64encode(f.read()).decode("ascii")

ssm = boto3.client("ssm", region_name="us-east-1")
commands = [
    "mkdir -p /opt/sre-colosseum/k8s/agents",
    f"cat << 'EOF' | base64 -d > /opt/sre-colosseum/k8s/agents/agent-sandbox.yaml\n{b64_manifest}\nEOF",
    "k3s kubectl apply -f /opt/sre-colosseum/k8s/agents/agent-sandbox.yaml",
    "sleep 3",
    "k3s kubectl get pods -n sre-agent-sandbox -o wide"
]
resp = ssm.send_command(
    InstanceIds=["i-0cf1c979f2cbd01c4"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
print("Dispatched sandbox manifest deployment:", resp["Command"]["CommandId"])
