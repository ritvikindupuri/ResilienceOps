import json, urllib.request, base64

auth = base64.b64encode(b"admin:admin").decode("ascii")

# Load current dashboard
with open("dashboards/provisioning/dashboards/sre-dashboard.json", "r", encoding="utf-8") as f:
    dash = json.load(f)

for p in dash["panels"]:
    if p["id"] == 10:
        # Give human-friendly mappings in value mappings
        p["fieldConfig"]["defaults"]["mappings"] = [
            {
                "type": "value",
                "options": {
                    "CAMPAIGN_FORMULATED": { "text": "Chaos Attack Formulated" },
                    "INFRA_FAULT_INJECTED": { "text": "Memory / CPU Stress Injected" },
                    "NETWORK_FAULT_INJECTED": { "text": "Network Delay Injected" },
                    "INCIDENT_DECLARED": { "text": "SLO Breach Alert Declared" },
                    "RCA_COMPLETE": { "text": "Root Cause Diagnosed (Claude)" },
                    "RUNBOOK_EXECUTED": { "text": "Recovery Runbook Executed" },
                    "VERIFICATION_PENDING": { "text": "Health Verification Check" },
                    "POST_MORTEM_SAVED": { "text": "Incident Post-Mortem Generated" }
                }
            }
        ]
        # Also let us add valueMapping transformation or renameByName
        p["transformations"] = [
            {
                "id": "organize",
                "options": {
                    "renameByName": {
                        "CAMPAIGN_FORMULATED": "Chaos Attack Formulated",
                        "INFRA_FAULT_INJECTED": "Memory / CPU Stress Injected",
                        "NETWORK_FAULT_INJECTED": "Network Delay Injected",
                        "INCIDENT_DECLARED": "SLO Breach Alert Declared",
                        "RCA_COMPLETE": "Root Cause Diagnosed (Claude)",
                        "RUNBOOK_EXECUTED": "Recovery Runbook Executed",
                        "VERIFICATION_PENDING": "Health Verification Check",
                        "POST_MORTEM_SAVED": "Incident Post-Mortem Generated"
                    }
                }
            }
        ]

with open("dashboards/provisioning/dashboards/sre-dashboard.json", "w", encoding="utf-8") as f:
    json.dump(dash, f, indent=2)

print("Added readable human-friendly text mappings for pie chart actions.")
