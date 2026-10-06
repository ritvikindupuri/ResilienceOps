import json, urllib.request, base64

auth = base64.b64encode(b"admin:admin").decode("ascii")

# 1. Fetch current dashboard
req = urllib.request.Request("http://18.232.78.253:3000/api/dashboards/uid/cg0cyg4je7o5cb")
req.add_header("Authorization", f"Basic {auth}")
res = urllib.request.urlopen(req)
raw = json.loads(res.read())
dash = raw["dashboard"]

# Get Prometheus DS UID
req_ds = urllib.request.Request("http://18.232.78.253:3000/api/datasources/name/Prometheus")
req_ds.add_header("Authorization", f"Basic {auth}")
ds_info = json.loads(urllib.request.urlopen(req_ds).read())
prom_uid = ds_info["uid"]

# Remove all emojis/icons from dashboard title
dash["title"] = "SRE Real-Time Reliability and Auto-Remediation Monitor"

# Transform and redesign panels
new_panels = []
for p in dash["panels"]:
    # 1. Strip icons from titles
    title = p.get("title", "")
    for icon in ["? ", "?? ", "?? ", "??? ", "?? ", "?? ", "?? ", "?? ", "?? "]:
        title = title.replace(icon, "")
    p["title"] = title

    # 2. Fix System State font & readability
    if "Real-Time System State" in title:
        p["fieldConfig"]["defaults"]["text"] = {"valueSize": 22, "titleSize": 14}
        p["options"] = {"colorMode": "background", "graphMode": "none", "justifyMode": "center", "textMode": "value"}
        p["fieldConfig"]["defaults"]["mappings"] = [
            {
                "type": "value",
                "options": {
                    "0": {"text": "HEALTHY", "color": "dark-green"},
                    "1": {"text": "ACTIVE INCIDENT", "color": "dark-red"}
                }
            }
        ]

    # 3. Fix Agent Sandbox Security Status readability
    if "Agent Sandbox Security" in title:
        p["fieldConfig"]["defaults"]["text"] = {"valueSize": 20, "titleSize": 14}
        p["options"] = {"colorMode": "background", "graphMode": "none", "justifyMode": "center", "textMode": "value"}
        p["fieldConfig"]["defaults"]["mappings"] = [
            {
                "type": "value",
                "options": {
                    "0": {"text": "QUARANTINE LEAK DETECTED", "color": "dark-red"},
                    "1": {"text": "SECURE IN SANDBOX (QUARANTINED)", "color": "dark-green"}
                }
            }
        ]

    # 4. Replace Operator Shell text box with a High-Value Pie Chart
    if p["id"] == 10:
        pie_panel = {
            "id": 10,
            "gridPos": p["gridPos"],
            "type": "piechart",
            "title": "Incident Root Cause and Attack Distribution",
            "targets": [
                {
                    "datasource": {"type": "prometheus", "uid": prom_uid},
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

    # 5. Fix Red Team & Blue Team live tables to format labels into clean columns
    if "Red Team" in title:
        p["targets"] = [
            {
                "datasource": {"type": "prometheus", "uid": prom_uid},
                "expr": "sre_agent_operation_events_total{squad=\"red-team\"}",
                "format": "table",
                "instant": True
            }
        ]
        p["transformations"] = [
            {
                "id": "labelsToFields",
                "options": {
                    "mode": "columns"
                }
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
                "datasource": {"type": "prometheus", "uid": prom_uid},
                "expr": "sre_agent_operation_events_total{squad=\"blue-team\"}",
                "format": "table",
                "instant": True
            }
        ]
        p["transformations"] = [
            {
                "id": "labelsToFields",
                "options": {
                    "mode": "columns"
                }
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

    # Ensure all targets have the explicit Prometheus UID
    for t in p.get("targets", []):
        t["datasource"] = {"type": "prometheus", "uid": prom_uid}

    new_panels.append(p)

dash["panels"] = new_panels

# Save updated dashboard via API
save_payload = {
    "dashboard": dash,
    "overwrite": True
}
save_req = urllib.request.Request("http://18.232.78.253:3000/api/dashboards/db", data=json.dumps(save_payload).encode(), headers={"Content-Type": "application/json", "Authorization": f"Basic {auth}"})
save_res = urllib.request.urlopen(save_req)
print("Dashboard update result:", save_res.read().decode())

# Save local copy as well
with open("dashboards/provisioning/dashboards/sre-dashboard.json", "w", encoding="utf-8") as f:
    json.dump(dash, f, indent=2)
print("Local file dashboards/provisioning/dashboards/sre-dashboard.json updated.")
