# ResilienceOps real E2E run, 2026-10-18 (all times America/Indianapolis, EDT / UTC-4)

Repo: ritvikindupuri/ResilienceOps `main` @ `9253ea5` (shallow clone). Default compose profile (no `agents`).
Fault: `RedisConnectionSaturation` via `POST http://127.0.0.1:8001/fault/redis-starvation` (default `connections=55`; **49** opened, then Redis "max number of clients reached").
Traffic: the stack's own traffic-generator (`RPS_TARGET=20`, `CONCURRENCY=8`). No synthetic alert payloads used.

Operator log from the Linux-box run (webhook URL truncated). Redacted bridge lines: [`live_run_issue5_bridge.log`](live_run_issue5_bridge.log). Public GitHub issue: https://github.com/ritvikindupuri/ResilienceOps/issues/5

| Time (EDT) | Hop | Event |
|---|---|---|
| 21:44:59 | compose | `docker compose up -d --build` started |
| 21:46:25 | compose | all 10 containers started; bridge logs `webhook_configured=True auth_header=Authorization auth_scheme_set=True` |
| 21:46:45 | env | Prometheus: `Error sending alert ... alertmanager:9093 ... context deadline exceeded`; all scrape targets down. Box firewall issue (legacy iptables FORWARD DROP); fixed on the host (not a repo change). See README troubleshooting *Containers cannot reach each other*. |
| 21:47:53–21:48:25 | side effect | `docker compose restart order-service` (to reconnect Postgres) caused a real `APIGatewayHighErrorRate` blip (pending 21:47:53, firing ~21:48:13, resolved 21:48:25). Bridge accepted it (21:48:18 firing, 21:48:33 resolved) but egress was still blocked: 3/3 `ConnectTimeout` each, then `ERROR: Exception in ASGI application` 21:49:49 / 21:50:04. **Nothing was delivered to the bot for this blip.** That unhandled ASGI exception is what PR #3's bridge `forward FAILED after N attempts` path fixes. Egress was restored afterwards. |
| 21:50:59 | fault | `POST /fault/redis-starvation`: `opened_unclosed_connections: 49` |
| 21:51:01 | Prometheus | `RedisConnectionSaturation` + `RedisConnectionSaturationWarning`: inactive → pending |
| 21:51:05.886 | Prometheus | alert `startsAt` (`activeAt` + `for: 5s`) |
| 21:51:06 | Prometheus | both → firing |
| 21:51:06 | Alertmanager | `RedisConnectionSaturation` `active`; Warning `suppressed` (`inhibit_rules` critical > warning, same `service`) |
| 21:51:10.894 | incident-bridge | `POST /webhook HTTP/1.1 200 OK` from alertmanager, after `group_wait: 5s` |
| 21:51:10–11 | incident-bridge | evidence collection (12 Prometheus query/query_range calls, all 200) |
| 21:51:11.134 | bridge → Grok webhook | `POST …/automations/webhook/<redacted> "HTTP/1.1 200 OK"`; `forwarded 1 alert(s) status=firing` |
| 21:52:06 | Grok Bot → GitHub | issue #5 `[critical] RedisConnectionSaturation on order-service` opened, label `incident`, fingerprint `279c3ab8f16c75be` |
| 21:55:01 | fault reset | `POST /fault/reset` → `{"status":"clean"}` |
| 21:55:05 | Prometheus | alert resolved (`endsAt` per bot) |
| 21:55:06 | Prometheus / AM | both rules firing → inactive; AM active alerts empty |
| 21:55:10.904 | incident-bridge | resolved `POST /webhook 200 OK` from alertmanager |
| 21:55:11.218 | bridge → Grok webhook | `HTTP/1.1 200 OK`; `forwarded 1 alert(s) status=resolved` |
| 21:55:39 | Grok Bot → GitHub | "Resolved" comment on issue #5 (duration ~4 min) |

Fault-to-bot-webhook latency: **12.1 s** (21:50:59 fault → 21:51:11.134 webhook 200).
Firing-to-GitHub-issue: **~61 s** (21:51:05 `startsAt` → 21:52:06 issue #5).

Notes:

- Default compose profile: **no `agents`**, so `agent_activity` on the issue is empty.
- `redis_active_connections_count` was 49 of `maxclients` 50.
- `#4` is the earlier synthetic E2E (`RedisConnectionsSaturated`, fingerprint `e2etest-redis-starvation-20261018`). This issue is the live firing.
