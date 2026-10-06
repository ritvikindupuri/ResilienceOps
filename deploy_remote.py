import base64, boto3, time

with open("deploy_payload.zip", "rb") as f:
    b64_payload = base64.b64encode(f.read()).decode("ascii")

ssm = boto3.client("ssm", region_name="us-east-1")

commands = [
    "mkdir -p /opt/sre-colosseum",
    "cd /opt/sre-colosseum",
    f"cat << 'EOF' | base64 -d > deploy_payload.zip\n{b64_payload}\nEOF",
    "apt-get install -y unzip",
    "unzip -o deploy_payload.zip",
    "docker-compose up --build -d grafana prometheus api-gw order-service payment-service traffic-generator",
    "docker ps"
]

resp = ssm.send_command(
    InstanceIds=["i-0cf1c979f2cbd01c4"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
cmd_id = resp["Command"]["CommandId"]
print("Dispatched SSM deployment command:", cmd_id)
