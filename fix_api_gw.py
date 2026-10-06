import boto3, time

ssm = boto3.client("ssm", region_name="us-east-1")
cmd_script = [
    "cd /opt/sre-colosseum",
    "python3 -c \"content = open('services/api-gw/main.py').read().replace('from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST', 'from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST'); open('services/api-gw/main.py', 'w').write(content)\"",
    "docker-compose build --no-cache api-gw",
    "docker-compose up -d api-gw",
    "sleep 3",
    "docker ps"
]
resp = ssm.send_command(
    InstanceIds=["i-0cf1c979f2cbd01c4"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": cmd_script}
)
cmd_id = resp["Command"]["CommandId"]
print("Rebuild Command ID:", cmd_id)
time.sleep(18)
res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId="i-0cf1c979f2cbd01c4")
print("Status:", res["Status"])
print(res.get("StandardOutputContent", "")[-800:])
