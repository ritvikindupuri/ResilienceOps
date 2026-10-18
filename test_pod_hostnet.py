from agents.config import AWS_REGION, require_ec2_instance_id

INSTANCE_ID = require_ec2_instance_id()
﻿import boto3, time

ssm = boto3.client("ssm", region_name=AWS_REGION)
commands = [
    # Verify the host IP and test curl from host to ensure endpoints are listening
    "echo 'Testing from host to localhost:8001...'",
    "curl -s -X POST 'http://127.0.0.1:8001/fault/leak-memory?mb=150'",
    "echo ''",
    "curl -s -X POST 'http://127.0.0.1:8001/fault/reset'",
    "echo ''",
    # Patch sandbox deployment to hostNetwork: true so the pod shares the host network stack directly
    "k3s kubectl patch deployment red-team-sandbox -n sre-agent-sandbox -p '{\"spec\":{\"template\":{\"spec\":{\"hostNetwork\":true}}}}'",
    "sleep 5",
    "k3s kubectl rollout status deployment/red-team-sandbox -n sre-agent-sandbox --timeout=30s",
    "pod_name=$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-fault -o jsonpath='{.items[0].metadata.name}')",
    "echo 'Patched Pod Name:' $pod_name",
    "echo '=== [1] RED TEAM INJECTION FROM INSIDE POD ==='",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- python -c \"import urllib.request; req = urllib.request.Request('http://127.0.0.1:8001/fault/leak-memory?mb=150', data=b''); print('Raw Output:', urllib.request.urlopen(req).read().decode())\"",
    "echo ''",
    "echo '=== [2] BLUE TEAM REMEDIATION FROM INSIDE POD ==='",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- python -c \"import urllib.request; req = urllib.request.Request('http://127.0.0.1:8001/fault/reset', data=b''); print('Raw Output:', urllib.request.urlopen(req).read().decode())\""
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
print(res.get("StandardErrorContent", ""))
