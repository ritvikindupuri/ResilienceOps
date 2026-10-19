# Live Path B run — GitHub issue #5

Recorded on a separate Linux box against `main` at `9253ea5` (2026-10-19).
This is a real Compose stack, a real `POST /fault/redis-starvation`, and the live
**AI Incident Diagnosis** bot. Source: public issue
https://github.com/ritvikindupuri/ResilienceOps/issues/5

Times are UTC. The operator clock was EDT (UTC−4).

| UTC | What happened |
|---|---|
| 01:51:05Z | Prometheus alert `RedisConnectionSaturation` (critical, `order-service`) entered firing. `startsAt` on the issue. |
| ~01:51:17Z | incident-bridge POSTed the enriched payload to the live bot webhook; the webhook returned **HTTP 200**. Fault-to-webhook was **about 12 seconds** (`for: 5s` on the rule plus Alertmanager `group_wait: 5s`). |
| 01:51:10Z | Evidence window stamped on the firing issue (600s PromQL summaries). |
| 01:52:06Z | Bot opened **issue #5** (`[critical] RedisConnectionSaturation on order-service`, label `incident`, fingerprint `279c3ab8f16c75be`). About **61 seconds** after firing. |
| — | Operator ran `POST /fault/reset` on order-service (and the matching payment-service reset). |
| 01:55:05Z | Alert resolved (`status: resolved` forwarded; webhook **200**). Duration about 4 minutes. |
| 01:55:10Z | Evidence window stamped on the Resolved comment. |
| 01:55:39Z | Bot commented **Resolved** on issue #5. No remediation action by the bot. |

Notes that match the issue body:

- `redis_active_connections_count` jumped 0 → 49 (maxclients 50).
- Agent activity / k8s events were empty: the agents Compose profile was not running. The bridge only tails `logs/agent_activity.jsonl` when that file has rows.
- `#4` is the earlier synthetic E2E (`RedisConnectionsSaturated`, fingerprint `e2etest-redis-starvation-20261018`). This issue is the live firing.
