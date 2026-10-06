import boto3, time

ssm = boto3.client("ssm", region_name="us-east-1")
commands = [
    "pod_name=$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-chaos -o jsonpath='{.items[0].metadata.name}')",
    "k3s kubectl exec $pod_name -n sre-agent-sandbox -- cat /proc/net/route"
]
resp = ssm.send_command(
    InstanceIds=["i-0cf1c979f2cbd01c4"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)
cmd_id = resp["Command"]["CommandId"]
time.sleep(5)
res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId="i-0cf1c979f2cbd01c4")
print(res.get("StandardOutputContent", ""))
