import boto3, json, time
from datetime import datetime

logs = boto3.client("logs", region_name="us-east-1")

# Let us query the latest events from Prometheus and push them as a clean batch to CloudWatch
import urllib.request
res = urllib.request.urlopen("http://18.232.78.253:9090/api/v1/query?query=sre_agent_operation_events_total")
data = json.loads(res.read())["data"]["result"]

log_events = []
base_time = int(time.time() * 1000) - (len(data) * 1000)

for idx, item in enumerate(data):
    m = item["metric"]
    event_payload = {
        "squad": m.get("squad"),
        "agent": m.get("agent"),
        "action": m.get("action"),
        "exact_command_executed": m.get("command"),
        "exact_execution_output": m.get("result"),
        "status": m.get("status"),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    log_events.append({
        "timestamp": base_time + (idx * 1000),
        "message": json.dumps(event_payload)
    })

if log_events:
    # Sort chronologically as required by CloudWatch
    log_events.sort(key=lambda x: x["timestamp"])
    res = logs.put_log_events(
        logGroupName="/sre/autonomous-agent-audit",
        logStreamName="audit-stream",
        logEvents=log_events
    )
    print(f"Flushed {len(log_events)} audit events to CloudWatch: {res['ResponseMetadata']['HTTPStatusCode']}")
