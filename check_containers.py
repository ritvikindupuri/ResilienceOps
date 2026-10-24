import boto3, time
from agents.config import AWS_REGION, require_ec2_instance_id

INSTANCE_ID = require_ec2_instance_id()


ssm = boto3.client("ssm", region_name=AWS_REGION)
resp = ssm.send_command(
    InstanceIds=[INSTANCE_ID],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": ["docker ps -a", "docker-compose -f /opt/resilienceops/docker-compose.yml logs --tail=20 api-gw"]}
)
cmd_id = resp["Command"]["CommandId"]
time.sleep(4)
res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=INSTANCE_ID)
print(res.get("StandardOutputContent", "").encode("ascii", "replace").decode("ascii"))
