import urllib.request, json

url = "http://18.232.78.253:9090/api/v1/query?query=sum(rate(http_requests_total[1m]))"
res = urllib.request.urlopen(url)
data = json.loads(res.read())
print("Rate query result:", data["data"]["result"])

url2 = "http://18.232.78.253:9090/api/v1/query?query=sre_agent_sandbox_quarantine_status"
res2 = urllib.request.urlopen(url2)
data2 = json.loads(res2.read())
print("Sandbox status query result:", data2["data"]["result"])
