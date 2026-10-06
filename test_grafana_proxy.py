import boto3
import json

cw = boto3.client("cloudwatch", region_name="us-east-1")
dashboard_name = "SRE-Chaos-Vectors-Live-Telemetry"

body = {
    "widgets": [
        {
            "type": "text",
            "x": 0,
            "y": 0,
            "width": 24,
            "height": 3,
            "properties": {
                "markdown": "# SRE Chaos Engineering: Live Attack Vectors & Telemetry Impact\n### Continuous Real-Time Tracking of Autonomous Red Team Chaos Injections & Kernel Degradation\nTracks **Physical Container Memory Exhaustion (cgroup OOMKill)**, **CPU CFS Quota Starvation**, and **Network Transit Delays & Packet Loss** across all microservices."
            }
        },
        {
            "type": "log",
            "x": 0,
            "y": 3,
            "width": 8,
            "height": 6,
            "properties": {
                "query": "SOURCE '/sre/autonomous-agent-audit' | filter exact_command_executed like /leak-memory/ or exact_command_executed like /MEMORY/ | sort @timestamp desc | fields @timestamp, exact_command_executed as `Memory Injection Command`, exact_execution_output as `cgroup Kernel Output` | limit 10",
                "region": "us-east-1",
                "title": "Vector 1: Container Memory Exhaustion (cgroup OOMKill)",
                "view": "table"
            }
        },
        {
            "type": "log",
            "x": 8,
            "y": 3,
            "width": 8,
            "height": 6,
            "properties": {
                "query": "SOURCE '/sre/autonomous-agent-audit' | filter exact_command_executed like /cpu-burn/ or exact_command_executed like /CPU/ | sort @timestamp desc | fields @timestamp, exact_command_executed as `CPU Burn Command`, exact_execution_output as `CFS Throttling Impact` | limit 10",
                "region": "us-east-1",
                "title": "Vector 2: CPU CFS Quota Starvation (Thread Exhaustion)",
                "view": "table"
            }
        },
        {
            "type": "log",
            "x": 16,
            "y": 3,
            "width": 8,
            "height": 6,
            "properties": {
                "query": "SOURCE '/sre/autonomous-agent-audit' | filter exact_command_executed like /latency/ or exact_command_executed like /packet/ or exact_command_executed like /LATENCY/ | sort @timestamp desc | fields @timestamp, exact_command_executed as `Network Fault Command`, exact_execution_output as `504 Timeout Cascade` | limit 10",
                "region": "us-east-1",
                "title": "Vector 3: Network Transit Delays & Packet Loss (HTTP 504)",
                "view": "table"
            }
        },
        {
            "type": "log",
            "x": 0,
            "y": 9,
            "width": 12,
            "height": 6,
            "properties": {
                "query": "SOURCE '/sre/autonomous-agent-audit' | filter squad = 'red-team' | stats count(*) as TotalAttacks by bin(5m)",
                "region": "us-east-1",
                "title": "Red Team Attack Frequency Over Time (5-Minute Buckets)",
                "view": "timeSeries",
                "stacked": False
            }
        },
        {
            "type": "log",
            "x": 12,
            "y": 9,
            "width": 12,
            "height": 6,
            "properties": {
                "query": "SOURCE '/sre/autonomous-agent-audit' | filter squad in ['red-team', 'blue-team'] | stats count(*) as Operations by squad, bin(5m)",
                "region": "us-east-1",
                "title": "Offensive Chaos Attacks vs SRE Remediations Over Time",
                "view": "timeSeries",
                "stacked": False
            }
        },
        {
            "type": "log",
            "x": 0,
            "y": 15,
            "width": 24,
            "height": 8,
            "properties": {
                "query": "SOURCE '/sre/autonomous-agent-audit' | filter squad = 'red-team' | sort @timestamp desc | fields @timestamp, agent as `Attacking Agent`, exact_command_executed as `Injected Attack Command`, exact_execution_output as `Raw Target Result`, status as State | limit 50",
                "region": "us-east-1",
                "title": "Live Chaos Attack Feed: Exact Injected Vector Commands & Target Responses",
                "view": "table"
            }
        }
    ]
}

resp = cw.put_dashboard(DashboardName=dashboard_name, DashboardBody=json.dumps(body))
print("Successfully created dashboard:", dashboard_name, resp["ResponseMetadata"]["HTTPStatusCode"])
