import boto3, time, urllib.request

ssm = boto3.client("ssm", region_name="us-east-1")
cmd_script = [
    "docker rm -f sre-colosseum_api-gw_1 || true",
    "docker run -d --name sre-colosseum_api-gw_1 --network sre-colosseum_default -p 8000:8000 -e ORDER_SERVICE_URL=http://order-service:8001 -e PAYMENT_SERVICE_URL=http://payment-service:8002 sre-colosseum_api-gw:latest",
    "sleep 3",
    "docker ps"
]
resp = ssm.send_command(
    InstanceIds=["i-0cf1c979f2cbd01c4"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": cmd_script}
)
cmd_id = resp["Command"]["CommandId"]
time.sleep(5)
res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId="i-0cf1c979f2cbd01c4")
print("Status:", res["Status"])
print(res.get("StandardOutputContent", ""))
