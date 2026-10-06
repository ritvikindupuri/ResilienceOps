import boto3, time

ssm = boto3.client("ssm", region_name="us-east-1")
commands = [
    "pod_name=$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-chaos -o jsonpath='{.items[0].metadata.name}')",
    "echo 'Pod Name:' $pod_name",
    "echo '=== [1] PROBE TARGET MICROSERVICES FROM INSIDE RED TEAM SANDBOX POD ==='",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- python -c \"import urllib.request; print('Gateway Probe HTTP:', urllib.request.urlopen('http://10.42.0.1:8000/health').status)\"",
    "echo ''",
    "echo '=== [2] RED TEAM INJECTION EXECUTED FROM INSIDE SANDBOX POD ==='",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- python -c \"import urllib.request; req = urllib.request.Request('http://10.42.0.1:8001/chaos/leak-memory?mb=150', data=b''); print('Raw Output:', urllib.request.urlopen(req).read().decode())\"",
    "echo ''",
    "echo '=== [3] BLUE TEAM REMEDIATION EXECUTED FROM INSIDE SANDBOX POD ==='",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- python -c \"import urllib.request; req = urllib.request.Request('http://10.42.0.1:8001/chaos/reset', data=b''); print('Raw Output:', urllib.request.urlopen(req).read().decode())\""
]
resp = ssm.send_command(
    InstanceIds=["i-0cf1c979f2cbd01c4"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
cmd_id = resp["Command"]["CommandId"]
time.sleep(8)
res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId="i-0cf1c979f2cbd01c4")
print(res.get("StandardOutputContent", ""))
print(res.get("StandardErrorContent", ""))
