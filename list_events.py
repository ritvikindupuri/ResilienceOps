import urllib.request, json

res = urllib.request.urlopen("http://18.232.78.253:9090/api/v1/query?query=sre_agent_operation_events_total")
results = json.loads(res.read())["data"]["result"]
print(f"Total agent operations in Prometheus: {len(results)}")
for r in results:
    m = r["metric"]
    print(f"  [{m.get('squad')}] {m.get('agent')} -> {m.get('action')} ({m.get('status')})")
