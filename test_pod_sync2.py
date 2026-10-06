import boto3, base64

# Package current local files to zip and push
import os, zipfile, io
bio = io.BytesIO()
with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk("agents"):
        for f in files:
            full = os.path.join(root, f)
            zf.write(full, os.path.relpath(full, "."))
    zf.write("orchestrator.py", "orchestrator.py")
    if os.path.exists(".env"):
        zf.write(".env", ".env")

b64_zip = base64.b64encode(bio.getvalue()).decode("ascii")

ssm = boto3.client("ssm", region_name="us-east-1")
commands = [
    f"cat << 'EOF' | base64 -d > /tmp/agent_pkg.zip\n{b64_zip}\nEOF",
    "k3s kubectl cp /tmp/agent_pkg.zip sre-agent-sandbox/$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-fault -o jsonpath='{.items[0].metadata.name}'):/app/agent_pkg.zip",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- apt-get update -y",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- apt-get install -y unzip curl procps",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- bash -c 'cd /app && unzip -o agent_pkg.zip'",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- ls -la /app",
    "k3s kubectl exec deployment/red-team-sandbox -n sre-agent-sandbox -- bash -c 'cd /app && python orchestrator.py --target-ip 10.0.1.69 --cycles 1 --scenario MEMORY_EXHAUSTION'"
]
resp = ssm.send_command(
    InstanceIds=["i-0cf1c979f2cbd01c4"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
cmd_id = resp["Command"]["CommandId"]
print("Live sandbox pod execution command dispatched:", cmd_id)
