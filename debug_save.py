import json, urllib.request, base64

from agents.config import require_grafana_basic_auth_header
auth = require_grafana_basic_auth_header()
req = urllib.request.Request("http://18.232.78.253:3000/api/dashboards/uid/cg0cyg4je7o5cb")
req.add_header("Authorization", auth)
res = urllib.request.urlopen(req)
raw = json.loads(res.read())

save_payload = {
    "dashboard": raw["dashboard"],
    "folderUid": raw["meta"].get("folderUid"),
    "message": "Update",
    "overwrite": True
}
save_req = urllib.request.Request("http://18.232.78.253:3000/api/dashboards/db", data=json.dumps(save_payload).encode(), headers={"Content-Type": "application/json", "Authorization": auth})
try:
    save_res = urllib.request.urlopen(save_req)
    print("Success:", save_res.read().decode())
except urllib.error.HTTPError as e:
    print("Error:", e.read().decode())
