from agents.config import AWS_REGION, require_ec2_instance_id

INSTANCE_ID = require_ec2_instance_id()
﻿import boto3, time

ssm = boto3.client("ssm", region_name=AWS_REGION)
commands = [
    "echo '=== [STEP 1] BASELINE MEMORY BEFORE ATTACK ==='",
    "docker exec sre-colosseum_order-service_1 cat /proc/self/status | grep -E 'VmRSS'",
    "echo ''",
    "echo '=== [STEP 2] RED TEAM INJECTION (150MB HEAP LEAK) ==='",
    "curl -s -X POST 'http://localhost:8001/fault/leak-memory?mb=150'",
    "echo ''",
    "echo '=== [STEP 3] KERNEL RAM DURING INJECTION ==='",
    "docker exec sre-colosseum_order-service_1 cat /proc/self/status | grep -E 'VmRSS'",
    "sleep 3",
    "echo ''",
    "echo '=== [STEP 4] BLUE TEAM REMEDIATION (AUTOMATED RECOVERY FIXER) ==='",
    "curl -s -X POST 'http://localhost:8001/fault/reset'",
    "echo ''",
    "echo '=== [STEP 5] KERNEL RAM AFTER REMEDIATION ==='",
    "docker exec sre-colosseum_order-service_1 cat /proc/self/status | grep -E 'VmRSS'",
    "echo ''",
    "echo '=== [STEP 6] DOCKER AUDIT LOG ENTRIES ==='",
    "docker-compose -f /opt/sre-colosseum/docker-compose.yml logs --tail=10 order-service | grep -E 'fault'",
    "echo ''",
    "echo '=== [STEP 7] KUBERNETES AGENT SANDBOX PODS (QUARANTINED ON CLUSTER) ==='",
    "k3s kubectl get pods -n sre-agent-sandbox -o wide"
]

resp = ssm.send_command(
    InstanceIds=[INSTANCE_ID],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
cmd_id = resp["Command"]["CommandId"]
time.sleep(12)
res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=INSTANCE_ID)
print(res.get("StandardOutputContent", ""))
