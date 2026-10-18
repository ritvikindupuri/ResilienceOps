from agents.config import AWS_REGION, require_ec2_instance_id

INSTANCE_ID = require_ec2_instance_id()
﻿import boto3, time

ssm = boto3.client("ssm", region_name=AWS_REGION)
commands = [
    "pod_name=$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-fault -o jsonpath='{.items[0].metadata.name}')",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- cat /proc/net/route"
]
resp = ssm.send_command(
    InstanceIds=[INSTANCE_ID],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
cmd_id = resp["Command"]["CommandId"]
time.sleep(5)
res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=INSTANCE_ID)
print(res.get("StandardOutputContent", ""))
