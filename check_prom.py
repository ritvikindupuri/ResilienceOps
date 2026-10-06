import urllib.request, json

try:
    res = urllib.request.urlopen("http://18.232.78.253:9090/api/v1/targets")
    data = json.loads(res.read())
    print("Prometheus Active Targets:")
    for t in data["data"]["activeTargets"]:
        print(f"  {t['scrapePool']}: {t['scrapeUrl']} -> {t['health']} (Last error: {t.get('lastError', 'none')})")
except Exception as e:
    print("Prometheus target error:", e)

try:
    res = urllib.request.urlopen("http://18.232.78.253:8000/metrics")
    lines = res.read().decode("ascii").split("\n")
    print("\nAPI Gateway sample metrics:")
    for l in lines[:10]:
        if l and not l.startswith("#"):
            print(" ", l)
except Exception as e:
    print("API Gateway metrics error:", e)
