import json, urllib.request, base64

auth = base64.b64encode(b"admin:admin").decode("ascii")
req = urllib.request.Request("http://18.232.78.253:3000/api/dashboards/uid/cg0cyg4je7o5cb")
req.add_header("Authorization", f"Basic {auth}")
res = urllib.request.urlopen(req)
raw = json.loads(res.read())

save_payload = {
    "dashboard": raw["dashboard"],
    "folderUid": raw["meta"].get("folderUid"),
    "message": "Update",
    "overwrite": True
}
save_req = urllib.request.Request("http://18.232.78.253:3000/api/dashboards/db", data=json.dumps(save_payload).encode(), headers={"Content-Type": "application/json", "Authorization": f"Basic {auth}"})
try:
    save_res = urllib.request.urlopen(save_req)
    print("Success:", save_res.read().decode())
except urllib.error.HTTPError as e:
    print("Error:", e.read().decode())
