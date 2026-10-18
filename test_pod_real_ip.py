from agents.config import AWS_REGION, require_ec2_instance_id

INSTANCE_ID = require_ec2_instance_id()
﻿import boto3, time

ssm = boto3.client("ssm", region_name=AWS_REGION)
commands = [
    # Get the actual newly created pod after rollout
    "pod_name=$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-fault --sort-by=.metadata.creationTimestamp | tail -n1 | awk '{print $1}')",
    "echo 'Latest Pod:' $pod_name",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- python -c \"import urllib.request; req = urllib.request.Request('http://127.0.0.1:8001/fault/leak-memory?mb=150', data=b''); print('INJECTION RESULT:', urllib.request.urlopen(req).read().decode())\"",
    "echo ''",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- python -c \"import urllib.request; req = urllib.request.Request('http://127.0.0.1:8001/fault/reset', data=b''); print('REMEDIATION RESULT:', urllib.request.urlopen(req).read().decode())\""
]
resp = ssm.send_command(
    InstanceIds=[INSTANCE_ID],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
cmd_id = resp["Command"]["CommandId"]
time.sleep(8)
res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=INSTANCE_ID)
print(res.get("StandardOutputContent", ""))
print(res.get("StandardErrorContent", ""))
