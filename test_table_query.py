import urllib.request, json, base64

from agents.config import require_grafana_basic_auth_header
auth = require_grafana_basic_auth_header()

# Check datasource UID
req = urllib.request.Request("http://18.232.78.253:3000/api/datasources/name/Prometheus")
req.add_header("Authorization", auth)
res = urllib.request.urlopen(req)
ds_info = json.loads(res.read())
print("Prometheus DS UID:", ds_info.get("uid"), "ID:", ds_info.get("id"))
ds_uid = ds_info.get("uid")

payload = {
    "queries": [
        {
            "refId": "A",
            "datasource": {"type": "prometheus", "uid": ds_uid},
            "expr": "sre_agent_operation_events_total{squad=\"red-team\"}",
            "format": "table",
            "instant": True
        }
    ],
    "from": "now-1h",
    "to": "now"
}

req2 = urllib.request.Request("http://18.232.78.253:3000/api/ds/query", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "Authorization": auth})
try:
    res2 = urllib.request.urlopen(req2)
    print("DS query response:", json.loads(res2.read())["results"]["A"]["frames"])
except urllib.error.HTTPError as e:
    print("DS error:", e.read().decode())
