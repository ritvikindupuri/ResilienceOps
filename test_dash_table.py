import urllib.request, json, base64

auth = base64.b64encode(b"admin:admin").decode("ascii")

# Let us fetch the dashboard directly from Grafana
req = urllib.request.Request("http://18.232.78.253:3000/api/dashboards/uid/cg0cyg4je7o5cb")
req.add_header("Authorization", f"Basic {auth}")
res = urllib.request.urlopen(req)
dash_data = json.loads(res.read())
print("Dashboard Title:", dash_data["dashboard"]["title"])

payload = {
    "queries": [
        {
            "refId": "A",
            "datasource": {"type": "prometheus", "name": "Prometheus"},
            "expr": "sre_agent_operation_events_total{squad=\"red-team\"}",
            "format": "table",
            "instant": True
        }
    ],
    "from": "now-15m",
    "to": "now"
}
req2 = urllib.request.Request("http://18.232.78.253:3000/api/ds/query", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "Authorization": f"Basic {auth}"})
res2 = urllib.request.urlopen(req2)
result = json.loads(res2.read())
print("Table Query Result:", json.dumps(result, indent=2)[:800])
