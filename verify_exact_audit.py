import urllib.request, json

res = urllib.request.urlopen("http://18.232.78.253:9090/api/v1/query?query=sre_agent_operation_events_total")
data = json.loads(res.read())["data"]["result"]
print(f"Total Events: {len(data)}\n")
for item in data:
    m = item["metric"]
    print(f"[{m.get('squad')}] {m.get('agent')}")
    print(f"   Tactical Action: {m.get('action')}")
    print(f"   Exact Command:   {m.get('command')}")
    print(f"   Exact Result:    {m.get('result')}")
    print(f"   State:           {m.get('status')}")
    print("-" * 65)
