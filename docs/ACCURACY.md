# Claim-to-evidence (diagram + README vs code)

This file is the audit table for the architecture PNG and the root README.
Every row cites the code (or config) that proves the claim. Diagram coordinates
come from `scripts/build_architecture.py` (the PNG is a raster of
`docs/architecture.svg`). Companion mermaid: `docs/architecture.mmd`.

**Must-include facts (requested for this pass):** VPC + IGW, three subnets with
which are used, security groups, IAM role / SSM, the single EC2 host running
Compose + k3s, local vs AWS, optional fault injection, bot outbound HTTPS only.

---

## Corrections made in this accuracy pass

| What was wrong / overstated / missing | Fix |
|---|---|
| Grafana default window described as a rolling 2-minute window | README + this table: dashboard `time.from` is `now-5m` (`sre-dashboard.json:20`) |
| Tech stack listed k6, Compose `v2.24+`, “Certified k3s v1.29+”, Terraform `v1.7+` | Dropped k6 (load is `traffic-generator`). Compose is v2. k3s is `curl https://get.k3s.io` in `user_data` (unpinned). Terraform `required_version = ">= 1.5.0"` |
| NetworkPolicy described as allowing the Grok webhook from the sandbox | Webhook is sent by **incident-bridge** on the Compose network. Sandbox egress is DNS 53, victim ns, TCP 443 (Anthropic/AWS; default k3s/flannel cannot FQDN-filter), plus TCP 8000–8002/9090 to VPC `10.0.0.0/16` for Compose on the EC2 host |
| Prometheus → Alertmanager documented as `127.0.0.1:9093` for in-compose traffic | Compose DNS `alertmanager:9093` (`prometheus.yml:20`). Host bind is `127.0.0.1:9093` |
| IGW missing from the figure | IGW satellite `public RT only` (`build_architecture.py:399`) |
| Unused subnets unlabeled | Caption `unused: app_workloads 10.0.10.0/24 · data_persistence 10.0.20.0/24` (`build_architecture.py:455`) |
| Memory panel threshold `256000000` while the PromQL already divides to MB | Threshold is now `256` with unit `none` (`sre-dashboard.json:293-312`) |
| CloudWatch dashboards named `Agent-Command-Log` / `System-Fault-Metrics` as if Terraform created them | README now names helper scripts `SRE-Autonomous-Agent-Security-Audit` and `SRE-fault-Vectors-Live-Telemetry`. RESULTS.md names are a dated snapshot |
| RBAC described as verbs `get, list, watch, pods/exec` | `pods/exec` is a **resource**. Red Role: `get/list/watch` on `pods` + `pods/exec`. Blue Role is separate (`namespace-rbac.yaml`) |
| Figure 3 console card “Subnets (5)” | Caption: Terraform creates **three** subnets; prefer `main.tf` |
| Step 4 implied host `pip install` is required for Compose | Marked “host agents / tests only” |
| Step 7 “Equivalent curl” sat under the bridge test but posted to `:9093` | Split AM curl vs bridge curl |
| Fault injection looked required | Step 7 + bottom cards: optional; real outages use the same Path B |
| `agent_activity` empty on live issue #5 unexplained | README: empty unless the `agents` profile / host orchestrator writes `logs/agent_activity.jsonl` |
| order-service Postgres connect-once at import (`pg_pool = None` forever) | `init_postgres` retry/backoff + `ensure_pg_pool` + Compose `/ready` |
| Compose had no healthchecks | `healthcheck` + `depends_on: condition: service_healthy` |
| Bridge forward failure raised into ASGI (`Exception in ASGI application`) | Log `forward FAILED after N attempts`, dead-letter JSONL, bounded retry queue, return `forward_failed` |
| Host iptables FORWARD breakage undocumented | Troubleshooting: “Containers cannot reach each other” |
| Sample output led with synthetic issue #4 | Primary sample is live issue #5; #4 demoted |
| Live-run hops were reconstructed (~12s / ~61s) | Operator table `examples/live_run_issue5_timeline.md` (EDT): **12.1 s** fault→webhook (21:50:59 → 21:51:11.134), **~61 s** `startsAt`→issue #5 (21:51:05.886 → 21:52:06). Redacted bridge lines `examples/live_run_issue5_bridge.log` |
| Live `httpx` INFO printed the full webhook URL | `app.py:31-32` sets httpx to WARNING. Committed sample log redacts `…/automations/webhook/<redacted>` |
| Terraform / IAM / SSM / IGW drawn inside `public_ingress` | Terraform + `deploy_remote.py` are operator-side (above the VPC). IAM + SSM sit in an **AWS account** strip outside the VPC, with `deploy_remote.py → SSM → EC2`. IGW straddles the VPC **right** border. Inside `public_ingress`: k3s, Compose, and a dashed SG around the host (`build_architecture.py:366-408,435-449`) |
| Blue Team arrow landed on order-service only | Three ticks: `health ×3` into api-gw, order-service, payment-service (`monitor.py:52-95`); `reset ×2` into order-service and payment-service (`fault_catalog.py:122-132`) |
| AWS README listed only `sts:GetCallerIdentity`; apply 403'd on a read-only principal | Checked-in operator policy `terraform/deployer-policy.json` (EC2/VPC create+delete, IAM CreateRole/DeleteRole/PassRole/instance-profile, SSM SendCommand/GetCommandInvocation/DescribeInstanceInformation/PutParameter, S3 deploy bucket, CW log groups) |
| `deploy_remote.py` started a subset of Compose services (no alertmanager / incident-bridge); inline ~98 KB base64 vs 100 KB SSM limit; no `reports/`; printed CommandId only; no SSM Online wait; API-key check read empty SSM env | S3 + presigned GET; `docker compose up --build -d` (all default services) + `--profile agents`; archive includes `reports/`; `wait_for_ssm_online` + `cloud-init status --wait`; `GetCommandInvocation` fail-nonzero; host `.env` from Parameter Store SecureString (`scripts/put_lab_secrets.py`) |
| `user_data` installed Compose v1; default `t3.small`; no `instance_id`/`region` outputs; IMDS hop 1; instance role SSM-only | Compose v2 plugin (`docker-compose-v2`); default `t3.medium` (~$0.0416/hr + ~$0.005/hr IPv4); outputs `instance_id`, `region`, `deploy_bucket`, `private_ip`; hop limit 2; inline GetParameter / S3 GetObject / `logs:PutLogEvents`; Terraform **log groups** (dashboards still helper scripts) |
| k3s sandbox undocumented; `orchestrator.py` missing in the pod; `--target-ip` used k8s DNS for Compose apps; faults piled up when Blue did not declare in 9s | `deploy_k8s_sandbox.py` applies `namespace-rbac.yaml` + `agent-sandbox.yaml`, copies repo code, targets host private IP. Orchestrator `finally` always `FaultCatalog.reset_environment()`. Duplicate Path B fingerprint comments on the open GitHub issue |
| 2× review: title clipped by the AWS-account strip; Terraform shaft bisected `VPC sre-enterprise-vpc`; deploy→SSM started on `deploy_remote.py`; IGW labels sat on the dashed VPC stroke; `health ×3` / `reset ×2` / `faults` / `PromQL` / `enriched JSON` sat on lines | Title reserved in a top band (baseline `y=34`). Terraform L-routes just above the VPC stroke and lands **right of** the VPC title. deploy→S3 starts past the name. IGW icon straddles the **right** border; labels live in the VPC–Grok gutter. Pills sit off their shafts |
| Orchestrator `finally` reset ran before `alerts.yml` `for:` windows (up to 20s) could fire | `FAULT_HOLD_SECONDS` default 120 holds after detection / RCA and before Blue remediation; `finally` still always `FaultCatalog.reset_environment()` (`orchestrator.py`) |
| k3s Blue PromQL failed: `deploy_k8s_sandbox.py` set `PROMETHEUS_URL=http://<private-ip>:9090` while Compose bound `127.0.0.1:9090` | Compose keeps loopback (SSM). `docker-compose.prom-lan.yml` + `PROMETHEUS_BIND=<private-ip>` on AWS. **No** `ingress_sg` rule for 9090 (only 3000/8000). Never `0.0.0.0` |
| Figure/README claimed incident-bridge k8s evidence | Compose bridge has no `kubernetes` client and no kubeconfig (`services/incident-bridge/requirements.txt`). Evidence is PromQL + agent jsonl (jsonl only with `--profile agents`) |
| Figure put Red/Blue in k3s; caption said `PromQL · jsonl · k8s`; Grok title `local or AWS`; footer called the bot read-only; unused CIDRs sat in `public_ingress`; Redis arrows started detached; pill `firing alerts` | Agents box inside `Docker Compose on this host` as `Agents (--profile agents)`; small dashed `k3s (optional)` outside Compose; Grok `Grok Bot (external)`; pill `diagnose`; unused CIDRs on the VPC; `public_ingress` labeled `10.0.1.0/24`; Redis/Postgres arrows from order-service; pill `alerts` |
| `put-user-policy` over the 2,048-char inline cap; deployer-policy missing provider-v5 S3 Gets / `DeleteObjectVersion`; README `cd terraform` broke step 9; k3s pod had no `workingDir` | Managed policy `create-policy`/`attach-*-policy`; `s3:Get*`/`List*` + `DeleteObjectVersion`; `terraform -chdir=terraform`; sandbox `workingDir: /app` |
| README k3s steps used laptop `$PRIVATE_IP`; empty `PROMETHEUS_BIND` could bind `0.0.0.0`; empty `GROK_WEBHOOK_AUTH_SCHEME` skipped on AWS; audit-stream never created; README implied k3s restart/scale | IMDSv2 on the host; `${PROMETHEUS_BIND:?…}` + host `COMPOSE_FILE`; `__EMPTY__` sentinel; Terraform `audit-stream` + logger `CreateLogStream` + Compose `AWS_REGION`; README says `sre-target-apps` is empty |
| Diagram at `0fcdcd2` crossed itself: SSM shaft through the label, Terraform/deploy arrows through the account box, faults/`/api/payments` buses through request arrows, verticals through health/reset/query/scrape, missing order-service→Redis/Postgres, Grafana on the bottom border, IGW caption on `operator :3000/:8000` | Orthogonal lanes in `build_architecture.py`. Dropped the operator-port edge (SG title `:3000 / :8000`) and the agents→api-gw edge (Agents caption `POST /api/agent-events · jsonl`). SSM is caption-only. `check_geometry()` refuses line×line, line-through-bbox, and overlapping icon/text/pill boxes; `render_architecture.sh` still writes 2× |

---

## 1. Diagram groups

| Element | What the figure says | Evidence |
|---|---|---|
| Canvas | 1600×1360 with a 32px margin; title “How ResilienceOps + AI Incident Diagnosis works”; node names 26px, captions 22px, title 40px (effective ≥13px at 950px) | `scripts/build_architecture.py` `build_scene()`; 2× PNG is 3200×2720. README `<img width="100%">` |
| Operator (laptop) | Thin top band “Deploy (optional AWS) · laptop”: Terraform, `put_lab_secrets.py`, `deploy_remote.py` | Laptop scripts, not AWS resources. `terraform/main.tf`; `scripts/put_lab_secrets.py`; `deploy_remote.py` |
| AWS group | “AWS” holds S3, SSM, Param Store. One drop into the EC2 host (S3 zip + SSM `send_command` + Param Store `.env`) | S3 `terraform/main.tf` deploy bucket; `deploy_remote.py` `ssm.send_command`; Param Store `scripts/put_lab_secrets.py`. IAM / CW / IGW / unused subnets are a footnote, not icons |
| EC2 host | Purple dashed, “EC2 host · VPC 10.0.0.0/16 · public subnet · SG :3000/:8000 from allowed_cidr” | `aws_instance` in `public_ingress`; VPC `sre-enterprise-vpc` `10.0.0.0/16`; `ingress_sg` 3000+8000 to `allowed_cidr` |
| k3s group | Small dashed “k3s sandbox (optional)” + “Optional: runs orchestrator.py in one sandbox pod” | Only `red-team-sandbox` runs `orchestrator.py`. `deploy_k8s_sandbox.py`; namespace `sre-agent-sandbox` |
| Agents group | “Agents” + “--profile agents” holds Red + Blue, inside Lab (Docker Compose) | One process: `orchestrator.py`. Compose service `agent-sandbox` `profiles: [agents]` |
| Compose group | “Lab (Docker Compose)” wrapping Agents, app, observability | `docker-compose.yml`; deploy zip includes compose (`deploy_remote.py` `INCLUDE_PATHS`) |
| External column | “External” + AI Incident Diagnosis hex avatar | Imported template, not hosted in-repo. Bridge needs outbound HTTPS (`GROK_WEBHOOK_URL`); agents also call Anthropic. Never “Your Grok bot” |
| Unused subnets | Footnote: `app_workloads 10.0.10.0/24 · data_persistence 10.0.20.0/24` | Created `terraform/main.tf`; instance `subnet_id` is `public_ingress` only |

---

## 2. Diagram nodes (boxes)

| Node | Caption on figure | Evidence |
|---|---|---|
| Terraform | “optional AWS” (outside the VPC) | AWS is not required for Compose. `terraform/main.tf` is the optional cloud host, run on the operator laptop |
| deploy_remote.py | “operator” (outside the VPC) | Builds a zip, uploads to S3, `ssm.send_command` |
| S3 satellite | “deploy → host” | `aws_s3_bucket.deploy`; `deploy_remote.py` `_upload_payload` |
| Param Store satellite | “secrets → .env” | `scripts/put_lab_secrets.py` SecureString; host `.env` via instance role `GetParameter` |
| IAM satellite | “role + profile” | `aws_iam_role.sre_host_role` name `sre-platform-host-role`; instance profile `sre-platform-instance-profile` |
| SSM satellite | “send_command” | `AmazonSSMManagedInstanceCore`; `deploy_remote.py` `send_and_wait` / `AWS-RunShellScript` |
| CW Logs satellite | “agents → CW” | `agents/common/structured_logger.py` `CreateLogStream` + `put_log_events` to `/sre/autonomous-agent-audit` stream `audit-stream` (Terraform + logger). Compose `agent-sandbox` `AWS_REGION` |
| put_lab_secrets.py satellite | “laptop → Param” | Operator script; not an AWS resource. Arrow into Param Store |
| SG box | “ingress + internal” around the host | `aws_security_group.ingress_sg` / `internal_app_sg` |
| IGW satellite | “public RT only”, straddling the VPC **right** border; labels in the VPC–Grok gutter | `aws_internet_gateway.igw`; public RT `0.0.0.0/0` via IGW; association **only** `public_ingress`. SG `ingress_sg` opens Grafana 3000 + API 8000 to `allowed_cidr` (SG title `:3000 / :8000`, no operator-port arrow) |
| k3s | small dashed “k3s sandbox (optional)” / “Optional: runs orchestrator.py in one sandbox pod” | `deploy_k8s_sandbox.py`; namespace `sre-agent-sandbox`; only `red-team-sandbox` runs `orchestrator.py` |
| Red Team | “faults order” / “+ payment” (inside Agents box) | `orchestrator.py` Red agents; `infra_disruptor.py` / `network_adversary.py` |
| Blue Team | “health on all 3” / “reset order + payment” (inside Agents box) | `orchestrator.py` Blue agents; `monitor.py`; `remediator.py` always `FaultCatalog.reset_environment()` after the hold |
| Traffic | “Live load” | `docker-compose.yml:120-129` `traffic-generator`; `traffic-generator/load_generator.py:8-12` |
| api-gw | “Gateway” | `services/api-gw/main.py`; compose port `8000:8000` (`docker-compose.yml:6`); uvicorn `:136` |
| order-service | “Orders” | `services/order-service/main.py`; compose `8001:8001` (`docker-compose.yml:32`); uvicorn `:376` |
| payment-service | “Payments” | `services/payment-service/main.py`; compose `8002:8002` (`docker-compose.yml:70`); uvicorn `:135` |
| Redis | “order-service cache” | compose `redis:7-alpine` `docker-compose.yml:92-95` (`maxclients 50`); order-service `REDIS_HOST` `:25-32`, `setex` around create-order |
| PostgreSQL | “orders_db” | compose `postgres:16-alpine` `POSTGRES_DB=orders_db` `docker-compose.yml:103-109`; order-service `POSTGRES_DB` `:39` |
| Prometheus | (no caption; scrape arrow from the service row) | image `prom/prometheus:v2.52.0` `docker-compose.yml:132`; `dashboards/prometheus.yml:1-12` |
| Alertmanager | “Groups alerts” | image `prom/alertmanager:v0.27.0` `docker-compose.yml:153`; `dashboards/alertmanager.yml:4-16` |
| incident-bridge | “PromQL · agent jsonl (Compose agents)” | `services/incident-bridge/app.py`; `evidence.py` PromQL + `collect_agent_activity`. Compose image has no `kubernetes` / kubeconfig. jsonl only with `--profile agents` |
| Grafana | (no caption; under the payment-service column, reads from Prometheus) | `grafana/grafana:10.4.2` `docker-compose.yml:210-212`; dashboard `sre-dashboard.json:8-22` |
| AI Incident Diagnosis | Grok hex avatar | Imported template; not source in this repo. README link `https://x.ai/bot/feQpDSeSki7HVgkDCBUaY` |
| GitHub issue | “label: incident” | Bot behavior (imported template). Sample: issue #5 label `incident`. Path A does **not** open issues (`orchestrator.py:112-115` writes `reports/`) |
| Owner ping | “Firing critical” | Bot template at import (not in this repo). README `:40`, `:666` |

---

## 3. Diagram arrows and pills

IAM has no chain arrow (Terraform creates the role + instance profile). SG is a box, not an arrow. Numbering matches comments in `build_architecture.py`.

| # | Arrow | Pill | Evidence |
|---|---|---|---|
| 1 | Terraform → VPC border (L-route just above the stroke, right of the VPC title) | (none) | Operator laptop, outside AWS. `terraform/main.tf` |
| 1b | deploy_remote.py lands on the AWS-account **left border** (below the caption) → S3; S3 → VPC/host and SSM → VPC/host drop from the account **bottom border** | (S3 cap `deploy → host`, SSM cap `send_command`) | Zip upload `_upload_payload`; `ssm.send_command` `AWS-RunShellScript`. Drops start on the box stroke so they do not run through satellite captions or the AWS title |
| 1c | put_lab_secrets.py → Param Store | (satellite cap `secrets → .env`) | `scripts/put_lab_secrets.py` SecureString; host `GetParameter` in `build_host_env_script`. Empty values stored as `__EMPTY__` |
| 2 | Traffic → api-gw | `requests` | `load_generator.py:40`, `:58`, `:78`; compose `GATEWAY_URL=http://api-gw:8000` `docker-compose.yml:124` |
| 3 | api-gw → order-service | `/api/orders` | `api-gw/main.py:92-111` strips prefix and proxies to `ORDER_SERVICE_URL`; generator POSTs `/api/orders/orders` `load_generator.py:58` |
| 4 | order-service → payment-service | `POST /payments` | `order-service/main.py:250` `POST {PAYMENT_SERVICE_URL}/payments` |
| 5 | api-gw → payment-service U-turn | `/api/payments` | `api-gw/main.py:113-132`; generator `/api/payments/payments` `load_generator.py:78` |
| 6–7 | order-service → Redis / Postgres | (none; fork from order-service) | Redis `setex` and Postgres INSERT in `order-service/main.py` create-order path; compose env `REDIS_HOST=redis`, `POSTGRES_DB=orders_db` |
| 8 | Red Team → order-service **and** payment-service | `faults` | Infra faults hit order-service (`infra_disruptor.py:40-47`, catalog `/fault/leak-memory`, `/fault/redis-starvation`, `/fault/cpu-burn`, `/fault/crash`). Network faults hit payment-service (`fault_catalog.py:45-80` `/fault/latency`, `/fault/drop-rate` on `eth0`). **Not** Traffic. One flyover + two ticks; pill sits above the shaft (`build_architecture.py:576-591`) instead of one arrow per endpoint |
| 9 | Blue Team → api-gw, order-service, payment-service | `health ×3` and `reset ×2` | `GET /health` on api-gw (4s), order, payment: `monitor.py:52-95`. Reset: `fault_catalog.py:122-132` POSTs `/fault/reset` on **order-service and payment-service only** (api-gw has no `/fault/reset`). Three ticks; two pills off the bus (`build_architecture.py:593-606`) |
| 10 | Blue Team → Prometheus | `query` | `monitor.py:15-25`, `:98-110` PromQL if `PROMETHEUS_URL` answers |
| 11 | Prometheus pulls /metrics from api-gw, order-service, payment-service | badge ② | `prometheus.yml:22-33` jobs `api-gw:8000`, `order-service:8001`, `payment-service:8002`; scrape `1s` `:2`. Orange ticks into Prometheus (pull), not payment-service pushing |
| 12 | Prometheus → Alertmanager | `alerts` | `prometheus.yml` `alertmanager:9093`; rules `dashboards/alerts.yml` |
| 13 | Alertmanager → incident-bridge | `webhook` | `alertmanager.yml:14-16` `http://incident-bridge:8080/webhook` `send_resolved: true` |
| 14 | Prometheus → Grafana | `reads` | Grafana is **not** on the alert path. Datasource provisioning `dashboards/provisioning/datasources/prometheus.yaml`. Host Grafana `:3000` (`docker-compose.yml:212`) |
| 15 | incident-bridge ⇢ Prometheus (dashed) | `PromQL` | `evidence.py:29-67` range queries; `app.py` `collect_evidence` |
| 16 | incident-bridge → Grok avatar | `enriched JSON` | `app.py` outbound `{status, alerts, evidence, source: "resilienceops"}` (`:155-160`); HTTPS to `GROK_WEBHOOK_URL` |
| 17–18 | AI Incident Diagnosis → GitHub / owner ping | badge ⑥ | Imported bot. Opening an issue is a write. Firing critical alerts also chat-ping the owner. The bot has no control path into the lab (webhook in, GitHub issue + owner ping out) |
| (omitted) | agents → api-gw `/api/agent-events`; agents → `agent_activity.jsonl` → bridge | Agents caption `POST /api/agent-events · jsonl`; bridge caption `PromQL · agent jsonl (Compose agents)`; CW `agents → CW`. No extra shaft | `structured_logger.py` POST `/api/agent-events` + jsonl; `evidence.py` `collect_agent_activity` |
| (omitted) | operator → SG `:3000 / :8000` | SG title `SG  ingress + internal  ·  :3000 / :8000`. No IGW→SG arrow | `ingress_sg` Grafana 3000 + API 8000 to `allowed_cidr` |

---

## 4. Diagram chrome (gate + cards)

| Element | Text | Evidence |
|---|---|---|
| Gate line 1 | “The bot has no control path into the lab: it only receives webhooks and writes GitHub issues.” | Bot template (not in-repo). Path A **does** reset/restart when k8s toolkit is available (`remediator.py`) — that is not the bot |
| Gate line 2 | “AWS/EC2 is optional: docker compose up runs the same lab (agents need --profile agents). The bridge needs outbound HTTPS to the bot; agents also call Anthropic.” | Local Compose `docker-compose.yml`; `agent-sandbox` profile; bridge POST `forwarding.py`; agents `llm_engine.py` |
| Card 1 | “Held fault (FAULT_HOLD_SECONDS, default 120) or a real outage trips a Prometheus alert rule.” | `FAULT_HOLD_SECONDS` default 120 (`orchestrator.py`). Rules in `dashboards/alerts.yml`. Real `up==0` / SLO / Redis saturation fire without `/fault` |
| Card 2 | “Bridge adds PromQL + jsonl and posts enriched JSON to the bot.” | `app.py` `collect_evidence`; jsonl only when agents write `logs/agent_activity.jsonl` |
| Card 3 | “Bot diagnoses and files or updates a GitHub issue.” | Imported template; samples issues #4 (synthetic) and #5 (live) |

---

## 5. README — architecture & dual path

| Claim | Evidence |
|---|---|
| 3-agent Red / 3-agent Blue | `orchestrator.py:41-50`; models `agents/config.py:31-39` |
| Models `claude-sonnet-4-6` / `claude-haiku-4-5-20251001` | `agents/config.py:31-39` |
| Path A = orchestrator; Path B = Prom → AM → bridge → Grok | `orchestrator.py`; `prometheus.yml` + `alertmanager.yml` + `app.py` |
| Traffic POSTs api-gw at compose `RPS_TARGET` default **20**; module default **25** if unset | `docker-compose.yml:125`; `load_generator.py:9` |
| api-gw reverse-proxies `/api/orders*` and `/api/payments*` (prefix stripped) | `api-gw/main.py:92-132` |
| Order-service writes Redis + Postgres and POSTs `/payments` | `order-service/main.py` create-order |
| Prometheus scrape 1s, three jobs | `prometheus.yml:2,22-33` |
| Grafana not on alert path; Prom published `127.0.0.1:9090`; AWS also binds private IP for k3s | `docker-compose.yml` loopback; `docker-compose.prom-lan.yml` `${PROMETHEUS_BIND:?…}` + host `.env` `COMPOSE_FILE`; Grafana depends_on prometheus only |
| Fault CLI scenarios and substring dispatch | `orchestrator.py:69-74`; `infra_disruptor.py:8-17` |
| Detection: `/health` ×3, p99/5xx PromQL, SLO 1200ms / 2%, HTTP >= 500, max 9 ticks of 1s; then `FAULT_HOLD_SECONDS` (default 120) before remediation | `monitor.py`; `orchestrator.py` `range(1, 10)` + `hold_fault_for_alerts` |
| Alertmanager `group_wait: 5s`, `group_interval: 15s`, `repeat_interval: 1h`, compose target `alertmanager:9093`, host `127.0.0.1:9093` | `alertmanager.yml:7-9`; `prometheus.yml:20`; `docker-compose.yml:161` |
| Bridge drop if URL empty; dedupe 300s; payload ~100KB; source `resilienceops` | `app.py:130-132`; `settings.py:56-58`; `forwarding.py:16-17,107` |
| Forward failure: ERROR log, dead-letter, retry queue, no ASGI crash | `app.py:164-187`; `forwarding.py:242-310`; ASGI wrapper `app.py:214-218` |
| httpx must not log `GROK_WEBHOOK_URL` | `app.py:31-32` `logging.getLogger("httpx").setLevel(logging.WARNING)` |
| `agent_activity` empty unless agents profile / host orchestrator | compose `agent-sandbox` `profiles: [agents]` `docker-compose.yml:232-234`; logger writes `logs/agent_activity.jsonl` `structured_logger.py:13-33` |
| Path A verify_recovery max 5, latency < 800ms; always `reset_environment` | `remediator.py`; orchestrator holds `FAULT_HOLD_SECONDS` then resets in `finally` so no-incident cycles cannot pile faults |
| Path A writes `reports/incident_*.md`; does not open GitHub issues | `orchestrator.py` phase 7 writes `reports/` |
| Bot has no lab control path (webhooks in, GitHub issues out); duplicate fingerprint comments; resolved comments; critical owner ping | Imported template (not in this repo). Documented as template behavior. Samples: issues #4 and #5 |

---

## 6. README — AWS resources

| Claim | Evidence |
|---|---|
| Terraform `>= 1.5.0`, AWS provider `~> 5.0` | `terraform/main.tf:14-21` |
| VPC `aws_vpc.sre_vpc` Name `sre-enterprise-vpc` CIDR default `10.0.0.0/16` | `terraform/main.tf:62-65,88-96` |
| IGW `sre-enterprise-igw` | `terraform/main.tf:99-104` |
| Public RT `sre-public-route-table`, `0.0.0.0/0` via IGW, assoc **only** `public_ingress` | `terraform/main.tf:145-160` |
| Subnet `public_ingress` `10.0.1.0/24` **used** (`map_public_ip_on_launch`, EC2 `subnet_id`) | `terraform/main.tf:108-118,413` |
| Subnet `app_workloads` `10.0.10.0/24` created unused | `terraform/main.tf:121-130` |
| Subnet `data_persistence` `10.0.20.0/24` created unused | `terraform/main.tf:133-142` |
| SG `ingress_sg` / `sre-ingress-sg`: Grafana 3000 + API 8000 from `allowed_cidr` | `terraform/main.tf:168-189` |
| SG `internal_app_sg` / `sre-internal-app-sg`: 8001–8002 from ingress SG; self scrape | `terraform/main.tf:208-227` |
| No SSH/22; no Prometheus 9090 on ingress SG | Comments `terraform/main.tf`; no `from_port = 22` / `9090` ingress rules. k3s uses host private IP via local delivery |
| `allowed_cidr` rejects `0.0.0.0/0` | `terraform/main.tf:68-75` |
| IAM `sre-platform-host-role` + `AmazonSSMManagedInstanceCore` + instance profile + inline GetParameter/S3/logs | `terraform/main.tf:245-326` |
| EC2 `sre-enterprise-platform-host` default `t3.medium` (`instance_type` variable; t3.small optional) | `terraform/main.tf:52-59,410-412` |
| user_data: Docker Compose **v2** (`docker-compose-v2`) + awscli + unzip + 2G swap + k3s (`https://get.k3s.io`) | `terraform/main.tf:437-456` |
| IMDS hop limit 2, IMDSv2 required | `terraform/main.tf:423-428` |
| S3 deploy bucket `sre-resilienceops-deploy-<account>-<region>`, 1-day expiry | `terraform/main.tf:336-380` |
| Outputs `instance_id`, `region`, `deploy_bucket`, `private_ip`, `api_gateway_url` `:8000`, `grafana_url` `:3000`, Prometheus host-local | `terraform/main.tf:482-520` |
| Operator IAM: customer managed policy `ResilienceOpsDeployer` via `create-policy` + `attach-user-policy` / `attach-role-policy` (inline user policies cap at 2,048 chars); teardown `detach-*-policy` + `delete-policy` | `terraform/deployer-policy.json` minified `< 6144`; README prerequisites + `teardown.sh` / `teardown.ps1` |
| Host `.env` from Parameter Store SecureString, not SendCommand | `scripts/put_lab_secrets.py`; `deploy_remote.py` `build_host_env_script` (`get-parameter --with-decryption`) |
| No NAT Gateway / no EKS in this Terraform | No `aws_nat_gateway` / `aws_eks_cluster` resources in `terraform/main.tf` |
| CloudWatch **log groups** + audit **stream** are Terraform; **dashboards** are not | Groups + `aws_cloudwatch_log_stream.audit` name `audit-stream` in `terraform/main.tf`. Logger `structured_logger.py` `CreateLogStream` if missing then `PutLogEvents`. Compose `agent-sandbox` gets `AWS_REGION`. Host inline `logs:CreateLogStream`/`PutLogEvents`. Helpers `create_cw_dashboard.py` name `SRE-Autonomous-Agent-Security-Audit`; `test_grafana_proxy.py` name `SRE-fault-Vectors-Live-Telemetry` |
| Figure 3 is a dated console map | PNG `docs/images/aws_vpc_resource_map.png`. Console “Subnets (5)” ≠ Terraform’s 3 subnets — prefer `main.tf` |

---

## 7. README — install, ports, env, commands

| Claim | Evidence |
|---|---|
| Python 3.10+ for host; images are `python:3.11-slim` | service Dockerfiles `FROM python:3.11-slim`; CI `python-version: "3.11"` `.github/workflows/ci.yml:23` |
| Grafana admin vars required (`:?Set GRAFANA_ADMIN_USER`) | `docker-compose.yml:214-215` |
| Compose interpolates Grafana, Postgres, Grok, bridge tunables, RPS, sandbox key, SLO | `docker-compose.yml` `${…}` + `.env.example`; enforced by `tests/test_docs_consistency.py` |
| `GROK_WEBHOOK_AUTH_SCHEME-Bearer` (present-but-empty sends raw key) | `docker-compose.yml:183`; `settings.py:23-27` |
| Host URLs default localhost:8000/8001/8002/9090 | `agents/config.py:4-9`; `.env.example:22-27` |
| Bridge container Prometheus `http://prometheus:9090` | `docker-compose.yml:185`; `.env.example:28` |
| Ports: api-gw 8000, order 8001, payment 8002, Grafana 3000, Prom `127.0.0.1:9090` (+ private IP on AWS), AM `127.0.0.1:9093`, bridge `127.0.0.1:8088`→8080 | `docker-compose.yml`; `docker-compose.prom-lan.yml` |
| Redis 6379 / Postgres 5432 published | `docker-compose.yml:93-94,104-105` |
| `RPS_TARGET` compose 20 / module 25; `CONCURRENCY` compose 8 / module 10 | `docker-compose.yml:125-126`; `load_generator.py:9-10` |
| `agent-sandbox` profile opt-in; CMD injects faults | `docker-compose.yml:232-234`; `Dockerfile.agent-sandbox` |
| `curl 127.0.0.1:8088/healthz` → `webhook_configured` | `app.py:198-203` |
| `send_test_alert.py --target alertmanager` → `127.0.0.1:9093/api/v2/alerts` | `scripts/send_test_alert.py:70-77` |
| `--target bridge` → `127.0.0.1:8088/webhook` | `send_test_alert.py:72,79-80` |
| Full demo `POST http://127.0.0.1:8001/fault/redis-starvation` then `/fault/reset` | `order-service/main.py:277,352`; alert `RedisConnectionSaturation` `alerts.yml:178-187` (`for: 5s`, `>= 48`) |
| Live timing **12.1 s** fault→webhook, **~61 s** to issue #5 | Operator hops `examples/live_run_issue5_timeline.md` (21:50:59 fault → 21:51:11.134 webhook 200; 21:51:05.886 `startsAt` → 21:52:06 issue). Redacted bridge lines `examples/live_run_issue5_bridge.log`. Public issue https://github.com/ritvikindupuri/ResilienceOps/issues/5. Warning inhibited (`inhibit_rules`). Default compose: **no `agents`**, so `agent_activity` empty |
| Issue #5 screenshots (public crops, no webhook key) | `docs/images/sample-incident-issue-5-{1,2,3}.png`; fingerprint `279c3ab8f16c75be`; “Agent activity: none attached” |
| `orchestrator.py --cycles 1 --scenario MEMORY_EXHAUSTION` | `orchestrator.py:9-10,118-123` |
| `deploy_remote.py` zip omits `.env`; includes `reports/` | `deploy_remote.py` `should_exclude` / `INCLUDE_PATHS`; `tests/test_deploy_archive.py` |
| SSM session, no SSH | `terraform/main.tf:191-192`; README step 10 (`--region`) |
| `teardown.sh` → `terraform destroy -auto-approve` + verify describe-instances / S3 / log groups | `teardown.sh` |
| k3s sandbox: `deploy_k8s_sandbox.py` applies `namespace-rbac.yaml` then `agent-sandbox.yaml`; copies repo code; `--target-ip` is host private IP | `deploy_k8s_sandbox.py`; `k8s/apps/microservices.yaml` is opt-in `--apply-microservices` |
| Host pip is **not** required for Compose-only | Service images `pip install -r requirements.txt` in Dockerfiles |
| Regen PNG: `scripts/render_architecture.sh` / `rsvg-convert` **2×** (3200×2720) | `scripts/render_architecture.sh`; `build_architecture.py` viewBox 1600×1360 |

Env-var inventory: every `os.getenv` / `_env_int` / `_env_float` name is in `.env.example` and mentioned in the README table — `tests/test_docs_consistency.py:57-72`.

---

## 8. README — sandbox, Grafana, troubleshooting

| Claim | Evidence |
|---|---|
| Namespace `sre-agent-sandbox`, limits `500m` / `512Mi` | `k8s/agents/agent-sandbox.yaml:8-11,75-78,121-124` |
| NetworkPolicy: DNS 53, victim ns `arena.sre.io/role=victim`, TCP 443, VPC Compose 8000–8002/9090 | `k8s/agents/agent-sandbox.yaml:129-172`; victim label `k8s/base/namespace-rbac.yaml:3-6` |
| Red Role `get/list/watch` on `pods` + `pods/exec` in `sre-target-apps` | `k8s/agents/agent-sandbox.yaml:23-31` |
| Blue Role pods/logs/events/deployments in `sre-target-apps` | `k8s/base/namespace-rbac.yaml:32-51` |
| Operator `kubectl exec` uses **operator** kubeconfig, not the sandbox SA | Host commands in README step 10; Role has no `create` on `pods/exec` |
| Grafana folder `SRE & Reliability`, dashboard title `SRE Infrastructure & Reliability Performance Monitor` | `dashboards.yaml:6`; `sre-dashboard.json:8` |
| `liveNow: true`, `refresh: 1s`, window `now-5m` | `sre-dashboard.json:17-21` |
| Availability threshold 99.9 | `sre-dashboard.json:69` |
| Memory panel vs 256MB cgroup (compose `memory: 256M`) | compose `docker-compose.yml:47,77`; dashboard query `/ 1024 / 1024` and threshold `256` `sre-dashboard.json:273-312` |
| Eight panels listed in README | Eight `"title"` entries `sre-dashboard.json:44,85,112,153,200,240,272,327` |
| FastAPI `0.111.0`, HTTPX `0.27.0`, Pydantic `2.8.2` | `services/api-gw/requirements.txt`; `services/order-service/requirements.txt:1-7` |
| Prometheus `v2.52.0`, Alertmanager `v0.27.0`, Grafana `10.4.2` | compose image tags |
| Redis 7 / Postgres 16 | `redis:7-alpine`, `postgres:16-alpine` |
| Compose healthchecks + `service_healthy` | `docker-compose.yml` `healthcheck` / `condition: service_healthy` |
| order-service `/ready` requires Redis + Postgres connected | `order-service/main.py:170-181`; `/health` stays 200 during faults `:135-167` |
| Postgres retry/backoff | `order-service/main.py:78-113` |
| Containers cannot reach each other (FORWARD / iptables) | Operational; check commands use compose DNS as in `prometheus.yml:25-33` and `alertmanager.yml:14` |
| Webhook 401/403 = bot rejected auth | `forwarding.py:215-216` does not retry 401; README troubleshooting |
| Dedupe 5 minutes, resolved is a different status | `forwarding.py:69-77`; `DEDUPE_TTL_SECONDS` default 300 `settings.py:57` |

---

## 9. Intentional simplifications (not bugs)

| Simplification | Why |
|---|---|
| Unused subnets are a caption, not empty boxes | Avoids blank green rectangles; CIDRs are on the VPC title row (not the `public_ingress` header) |
| IAM has no arrow | Terraform creates the role + instance profile; drawing Terraform→IAM would cross the account strip |
| One Red flyover + `faults` pill | Covers four order-service `/fault/*` plus two payment-service `tc netem` endpoints without six arrows |
| Prometheus node has no caption | Space under the observability row is Grafana; scrape/rule detail is the `3 scrape jobs` / `alerts` pills |
| One scrape edge + `3 scrape jobs` | Three Prometheus jobs share one merge bar under the service captions, then one gutter drop into Prometheus. Separate from Blue’s health/reset bus |
| Grok `incident` label, duplicate-comment, owner ping | Implemented by the **imported** Grok template, not this repository. Samples #4/#5 show the behavior |
| “Eliminates NAT ($32/mo) / EKS ($72/mo)” | Cost comparison: those resources are not in `main.tf`. Not a bill guarantee |
| Teardown “under 60 seconds” / “100% protected” host daemons | Timing and absolute guarantees are not asserted by tests |
| Figure 3 AWS console screenshot | Dated live capture; subnet count in the console chrome may not match Terraform |

---

## 10. Out of scope / not claimed by the code

- Grok Bot internals (prompt, GitHub app permissions, chat ping routing) live on x.ai, not in this git tree.
- `k8s/apps/microservices.yaml` is an alternate in-cluster deploy of the apps; the documented AWS lab runs Compose on the EC2 host plus k3s **sandbox**.
- Historical PDF `docs/ResilienceOps_Technical_Documentation.pdf` is not the source of truth (`README.md` overview).
