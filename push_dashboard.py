import boto3, base64
from agents.config import AWS_REGION, require_ec2_instance_id

INSTANCE_ID = require_ec2_instance_id()


with open("dashboards/provisioning/dashboards/sre-dashboard.json", "rb") as f:
    b64_content = base64.b64encode(f.read()).decode("ascii")

ssm = boto3.client("ssm", region_name=AWS_REGION)
commands = [
    "cd /opt/sre-colosseum",
    f"cat << 'EOF' | base64 -d > dashboards/provisioning/dashboards/sre-dashboard.json\n{b64_content}\nEOF",
    "docker restart sre-colosseum_grafana_1"
]
resp = ssm.send_command(
    InstanceIds=[INSTANCE_ID],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
print("Pushed updated dashboard to AWS EC2:", resp["Command"]["CommandId"])
