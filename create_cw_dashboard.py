import boto3, json

cw = boto3.client("cloudwatch", region_name="us-east-1")

cw_dashboard_body = {
    "widgets": [
        # Widget 1: Security & SRE Header Banner
        {
            "type": "text",
            "x": 0,
            "y": 0,
            "width": 24,
            "height": 2,
            "properties": {
                "markdown": "# Autonomous AI Agent Security Audit & Command Execution Log\nReal-time SecOps audit trail capturing every offensive injection command and autonomous SRE remediation action with exact parameters and raw kernel outputs."
            }
        },
        # Widget 2: Live Table of Red Team Chaos Agent Operations
        {
            "type": "log",
            "x": 0,
            "y": 2,
            "width": 24,
            "height": 7,
            "properties": {
                "query": "SOURCE '/sre/autonomous-agent-audit' | filter squad = 'red-team' | sort @timestamp desc | fields @timestamp, agent as Agent, exact_command_executed as `Exact Command Executed`, exact_execution_output as `Exact Execution Output`, status as State | limit 100",
                "region": "us-east-1",
                "title": "Red Team Chaos Agents: Exact Injected Commands & Outputs",
                "view": "table"
            }
        },
        # Widget 3: Live Table of Blue Team SRE Agent Remediations
        {
            "type": "log",
            "x": 0,
            "y": 9,
            "width": 24,
            "height": 7,
            "properties": {
                "query": "SOURCE '/sre/autonomous-agent-audit' | filter squad = 'blue-team' | sort @timestamp desc | fields @timestamp, agent as Agent, exact_command_executed as `Exact Remediation Command`, exact_execution_output as `Exact Remediation Output`, status as State | limit 100",
                "region": "us-east-1",
                "title": "Blue Team SRE Agents: Exact Remediation Commands & Outputs",
                "view": "table"
            }
        },
        # Widget 4: Unified Live Security Audit Stream (Full JSON Logs)
        {
            "type": "log",
            "x": 0,
            "y": 16,
            "width": 24,
            "height": 7,
            "properties": {
                "query": "SOURCE '/sre/autonomous-agent-audit' | sort @timestamp desc | fields @timestamp, squad, agent, action, exact_command_executed, exact_execution_output | limit 50",
                "region": "us-east-1",
                "title": "Unified Agent Security Audit Log Stream",
                "view": "table"
            }
        }
    ]
}

res = cw.put_dashboard(
    DashboardName="SRE-Autonomous-Agent-Security-Audit",
    DashboardBody=json.dumps(cw_dashboard_body)
)
print("AWS CloudWatch Security Audit Dashboard created:", res)
