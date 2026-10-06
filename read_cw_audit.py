import boto3, json

logs = boto3.client("logs", region_name="us-east-1")
events = logs.get_log_events(
    logGroupName="/sre/autonomous-agent-audit",
    logStreamName="audit-stream",
    limit=15,
    startFromHead=False
)
print("=== CLOUDWATCH LOG GROUP: /sre/autonomous-agent-audit ===")
print("=== CLOUDWATCH STREAM:    audit-stream ===\n")
for e in events.get("events", []):
    payload = json.loads(e["message"])
    print(f"[{payload.get('squad')}] {payload.get('agent')}")
    print(f"  Exact Command: {payload.get('exact_command_executed')}")
    print(f"  Exact Output:  {payload.get('exact_execution_output')}")
    print(f"  State:         {payload.get('status')}")
    print("-" * 65)
