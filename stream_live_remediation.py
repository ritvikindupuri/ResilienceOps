import boto3, time, sys

ssm = boto3.client("ssm", region_name="us-east-1")
instance_id = "i-0cf1c979f2cbd01c4"

commands = [
    "echo '=== [1] LIVE PROCESS RESIDENT MEMORY (RAM) BEFORE FAULT ==='",
    "docker exec sre-colosseum_order-service_1 cat /proc/self/status | grep -E 'VmRSS|VmSize'",
    "echo ''",
    "echo '=== [2] RECENT DOCKER LOGS: INJECTIONS & REMEDIATIONS ==='",
    "docker-compose -f /opt/sre-colosseum/docker-compose.yml logs --tail=25 order-service payment-service | grep -E 'fault|POST|reset|leak'",
    "echo ''",
    "echo '=== [3] KUBERNETES AGENT SANDBOX PODS (RUNNING ON K3S) ==='",
    "k3s kubectl get pods -A 2>&1 || true"
]

resp = ssm.send_command(
    InstanceIds=[instance_id],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
cmd_id = resp["Command"]["CommandId"]
time.sleep(5)
res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=instance_id)
print(res.get("StandardOutputContent", ""))
