import json

with open("dashboards/provisioning/dashboards/sre-dashboard.json", "r", encoding="utf-8") as f:
    dash = json.load(f)

dash["title"] = "SRE Real-Time Reliability and Auto-Remediation Monitor"

new_panels = []
for p in dash["panels"]:
    title = p.get("title", "")
    for icon in ["? ", "?? ", "?? ", "??? ", "?? ", "?? ", "?? ", "?? ", "?? "]:
        title = title.replace(icon, "")
    p["title"] = title

    # 1. Real-Time System State readability
    if "Real-Time System State" in title:
        p["fieldConfig"]["defaults"]["text"] = {"valueSize": 20, "titleSize": 14}
        p["options"] = {
            "colorMode": "background",
            "graphMode": "none",
            "justifyMode": "center",
            "textMode": "value"
        }
        p["fieldConfig"]["defaults"]["mappings"] = [
            {
                "type": "value",
                "options": {
                    "0": {"text": "HEALTHY", "color": "dark-green"},
                    "1": {"text": "ACTIVE INCIDENT", "color": "dark-red"}
                }
            }
        ]

    # 2. Agent Sandbox Security Status readability
    if "Agent Sandbox Security" in title:
        p["fieldConfig"]["defaults"]["text"] = {"valueSize": 20, "titleSize": 14}
        p["options"] = {
            "colorMode": "background",
            "graphMode": "none",
            "justifyMode": "center",
            "textMode": "value"
        }
        p["fieldConfig"]["defaults"]["mappings"] = [
            {
                "type": "value",
                "options": {
                    "0": {"text": "QUARANTINE LEAK DETECTED", "color": "dark-red"},
                    "1": {"text": "SECURE IN SANDBOX (ISOLATED)", "color": "dark-green"}
                }
            }
        ]

    # 3. Replace Operator Shell text with high-value Pie Chart
    if p["id"] == 10:
        pie_panel = {
            "id": 10,
            "gridPos": p["gridPos"],
            "type": "piechart",
            "title": "Incident Root Cause and Tactical Action Distribution",
            "targets": [
                {
                    "datasource": "Prometheus",
                    "expr": "count by (action) (sre_agent_operation_events_total)",
                    "legendFormat": "{{action}}",
                    "instant": True
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "hideFrom": {"legend": False, "tooltip": False, "viz": False}
                    }
                }
            },
            "options": {
                "reduceOptions": {
                    "values": True,
                    "calcs": ["lastNotNull"]
                },
                "pieType": "donut",
                "legend": {
                    "displayMode": "table",
                    "placement": "right",
                    "values": ["value", "percent"]
                },
                "tooltip": {
                    "mode": "single"
                }
            }
        }
        new_panels.append(pie_panel)
        continue

    # 4. Tables with transformation columns
    if "Red Team" in title:
        p["targets"] = [
            {
                "datasource": "Prometheus",
                "expr": "sre_agent_operation_events_total{squad=\"red-team\"}",
                "format": "table",
                "instant": True
            }
        ]
        p["transformations"] = [
            {
                "id": "labelsToFields",
                "options": {"mode": "columns"}
            },
            {
                "id": "organize",
                "options": {
                    "excludeByName": {
                        "Time": False,
                        "__name__": True,
                        "instance": True,
                        "job": True,
                        "squad": True,
                        "Value": True,
                        "Value #A": True
                    },
                    "renameByName": {
                        "agent": "Agent Name",
                        "action": "Tactical Action",
                        "status": "State",
                        "detail": "Vector Detail"
                    }
                }
            }
        ]

    if "Blue Team" in title:
        p["targets"] = [
            {
                "datasource": "Prometheus",
                "expr": "sre_agent_operation_events_total{squad=\"blue-team\"}",
                "format": "table",
                "instant": True
            }
        ]
        p["transformations"] = [
            {
                "id": "labelsToFields",
                "options": {"mode": "columns"}
            },
            {
                "id": "organize",
                "options": {
                    "excludeByName": {
                        "Time": False,
                        "__name__": True,
                        "instance": True,
                        "job": True,
                        "squad": True,
                        "Value": True,
                        "Value #A": True
                    },
                    "renameByName": {
                        "agent": "Agent Name",
                        "action": "Remediation Action",
                        "status": "State",
                        "detail": "Resolution Detail"
                    }
                }
            }
        ]

    new_panels.append(p)

dash["panels"] = new_panels

with open("dashboards/provisioning/dashboards/sre-dashboard.json", "w", encoding="utf-8") as f:
    json.dump(dash, f, indent=2)

print("sre-dashboard.json updated with zero icons, prominent large text, pie chart, and organized tables.")
