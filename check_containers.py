import boto3, time

ssm = boto3.client("ssm", region_name="us-east-1")
resp = ssm.send_command(
    InstanceIds=["i-0cf1c979f2cbd01c4"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": ["docker ps -a", "docker-compose -f /opt/sre-colosseum/docker-compose.yml logs --tail=20 api-gw"]}
)
cmd_id = resp["Command"]["CommandId"]
time.sleep(4)
res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId="i-0cf1c979f2cbd01c4")
print(res.get("StandardOutputContent", "").encode("ascii", "replace").decode("ascii"))
