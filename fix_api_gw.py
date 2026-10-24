import boto3, time
from agents.config import AWS_REGION, require_ec2_instance_id

INSTANCE_ID = require_ec2_instance_id()


ssm = boto3.client("ssm", region_name=AWS_REGION)
cmd_script = [
    "cd /opt/resilienceops",
    "python3 -c \"content = open('services/api-gw/main.py').read().replace('from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST', 'from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST'); open('services/api-gw/main.py', 'w').write(content)\"",
    "docker-compose build --no-cache api-gw",
    "docker-compose up -d api-gw",
    "sleep 3",
    "docker ps"
]
resp = ssm.send_command(
    InstanceIds=[INSTANCE_ID],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": cmd_script}
)
cmd_id = resp["Command"]["CommandId"]
print("Rebuild Command ID:", cmd_id)
time.sleep(18)
res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=INSTANCE_ID)
print("Status:", res["Status"])
print(res.get("StandardOutputContent", "")[-800:])
