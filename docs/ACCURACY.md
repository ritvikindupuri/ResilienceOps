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
| Figure 3 cropped to the resource-map cards | Cropped Figure 3 shows Terraform’s **three** subnets (`main.tf`) |
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
| Diagram at `0fcdcd2` crossed itself: SSM shaft through the label, Terraform/deploy arrows through the account box, faults/`/api/payments` buses through request arrows, verticals through health/reset/query/scrape, missing order-service→Redis/Postgres, Grafana on the bottom border, IGW caption on `operator :3000/:8000` | Orthogonal lanes in `build_architecture.py`. Dropped the operator-port edge (SG title `:3000 / :8000`) and the agents→api-gw edge (Agents caption `POST /api/agent-events · jsonl`). SSM is caption-only. `check_geometry()` refuses orange×grey crossings, line-through-text (10px halo; an edge may only clip its own source/target labels), shared collinear segments of *different* edges, and overlapping icon/text/pill boxes; `render_architecture.sh` still writes 2× |

---

## 1. Diagram groups

| Element | What the figure says | Evidence |
|---|---|---|
| Canvas | 1480×1280 with a 32px margin; title “How ResilienceOps works”; node names 28px, captions 24px, title 36px (effective ≥15px at 950px). Legend only: orange 1–6 diagnosis path, blue 7–10 remediator path, grey supporting. No arrow labels. Reading order: Figure 1 in [How it works](../README.md#how-it-works-step-by-step) (immediately after the intro), Figure 2 in [Agent sandbox](../README.md#agent-sandbox), Figure 3 on the AWS map. | `scripts/build_architecture.py` `build_scene()`; 2× PNG is 2960×2560. README caption is one short line; rebuild notes live under Reference → Figure source |
| Operator + AWS | One top band “Deploy (optional AWS)”. Two icons only: Terraform and EC2, plus a drop onto the host. S3 / SSM / Parameter Store / helper-script names stay in the README so the figure is not crowded | Laptop Terraform, not required for Compose. `terraform/main.tf`; `scripts/put_lab_secrets.py`; `deploy_remote.py`. Official AWS Architecture Icons + Terraform mark. IAM / CW / IGW / unused subnets are README prose |
| EC2 host | Purple dashed, “EC2 host · 10.0.1.0/24 · 10.0.0.0/16” + “Grafana and API ports from your IP”. Grey EC2→Stack drop is one straight vertical inside the host border. | `aws_instance` in `public_ingress`; VPC `sre-enterprise-vpc` `10.0.0.0/16`; `ingress_sg` 3000+8000 to the operator CIDR |
| k3s / Agents | Not on Figure 1. They live on Figure 2 (`docs/sandbox_architecture.svg`) and the README [Agent sandbox](../README.md#agent-sandbox) section | Only `red-team-sandbox` runs `orchestrator.py`. `deploy_k8s_sandbox.py`; namespace `sre-agent-sandbox`. Compose service `agent-sandbox` `profiles: [agents]` |
| Target services | Column group `api-gw` / `order-service` / `payment-service`. Orange ① is the scrape out of the services group | Compose services `api-gw`, `order-service`, `payment-service`; Prometheus scrape configs |
| Compose group | “Stack (Docker Compose)” wrapping Target services and observability | `docker-compose.yml`; deploy zip includes compose (`deploy_remote.py` `INCLUDE_PATHS`) |
| External column | Diagnosis hex and GitHub share the diagnosis row (arrow ⑤ is straight). Owner ping is above Diagnosis; Remediation is below it; Owner `/approve` and Actions sit on the bottom row | Diagnosis template `https://x.ai/bot/feQpDSeSki7HVgkDCBUaY` (no control path into the stack). Remediator template `https://x.ai/bot/8rxdqPVj5W-mksKhNfcw5` proposes one allowlisted action. Owner `/approve` is recorded by `.github/workflows/remediation-approve.yml`. Never “Your Grok bot” |
| Unused subnets | not on Figure 1 (README / this table) | Created `terraform/main.tf`; instance `subnet_id` is `public_ingress` only. CIDRs `app_workloads 10.0.10.0/24` and `data_persistence 10.0.20.0/24` |

---

## 2. Diagram nodes (boxes)

| Node | Caption on figure | Evidence |
|---|---|---|
| Terraform | (name only) | AWS is not required for Compose. `terraform/main.tf` is the optional cloud host, run on the operator laptop |
| Deploy script | “Deploy script” | `deploy_remote.py`: zip, S3 `put_object`, presigned GET, `ssm.send_command` |
| S3 satellite | “stores the app bundle” | `aws_s3_bucket.deploy`; `deploy_remote.py` `_upload_payload` `put_object` + `generate_presigned_url` (`get_object`, 3600s); host `curl` of that URL |
| Param Store satellite | “holds secrets” | `scripts/put_lab_secrets.py` SecureString; host `.env` via instance role `GetParameter` |
| IAM satellite | “role + profile” | `aws_iam_role.sre_host_role` name `sre-platform-host-role`; instance profile `sre-platform-instance-profile` |
| SSM satellite | “runs deploy commands” | `AmazonSSMManagedInstanceCore`; `deploy_remote.py` `send_and_wait` / `AWS-RunShellScript` |
| CW Logs satellite | “agents → CW” | `agents/common/structured_logger.py` `CreateLogStream` + `put_log_events` to `/sre/autonomous-agent-audit` stream `audit-stream` (Terraform + logger). Compose `agent-sandbox` `AWS_REGION` |
| Secrets script satellite | “Secrets script” | `scripts/put_lab_secrets.py`; not an AWS resource |
| SG box | “ingress + internal” around the host | `aws_security_group.ingress_sg` / `internal_app_sg` |
| IGW satellite | “public RT only”, straddling the VPC **right** border; labels in the VPC–Grok gutter | `aws_internet_gateway.igw`; public RT `0.0.0.0/0` via IGW; association **only** `public_ingress`. SG `ingress_sg` opens Grafana 3000 + API 8000 to `allowed_cidr` (SG title `:3000 / :8000`, no operator-port arrow) |
| k3s / Red / Blue | Figure 2 only: start options “Compose profile”, “host CLI” / `python3 orchestrator.py`, “k3s (optional)”; Target services `api-gw` / `order-service` / `payment-service` (no “all 3 services” node); orange badge ① on How to start; orange badge ② Red → order-service and payment-service; blue badge ③ Blue → Target services group; orange badge ④ Target services → Prometheus; “faults order + payment”, “watches and resets” | `deploy_k8s_sandbox.py`; `orchestrator.py`; `infra_disruptor.py` / `network_adversary.py`; `monitor.py`; `remediator.py` always `FaultCatalog.reset_environment()` after the hold |
| Traffic | not on Figure 1 (README only) | `docker-compose.yml:123-129` `traffic-generator`; `traffic-generator/load_generator.py:8-12` |
| api-gw | “api-gw” | `services/api-gw/main.py`; compose port `8000:8000` (`docker-compose.yml:6`); uvicorn `:136` |
| order-service | “order-” / “service” | `services/order-service/main.py`; compose `8001:8001` (`docker-compose.yml:34`); uvicorn `:376` |
| payment-service | “payment-” / “service” | `services/payment-service/main.py`; compose `8002:8002` (`docker-compose.yml:73`); uvicorn `:135` |
| Redis | not on Figure 1 (README only) | compose `redis:7-alpine` `docker-compose.yml:94-98` (`maxclients 50`); order-service `REDIS_HOST` `:25-32`, `setex` around create-order |
| PostgreSQL | not on Figure 1 (README only) | compose `postgres:16-alpine` `POSTGRES_DB=orders_db` `docker-compose.yml:105-112`; order-service `POSTGRES_DB` `:39` |
| Prometheus | (name only) | image `prom/prometheus:v2.52.0` `docker-compose.yml:135`; `dashboards/prometheus.yml:1-12` |
| Alertmanager | “Alert” / “manager” | image `prom/alertmanager:v0.27.0` `docker-compose.yml:159-160`; `dashboards/alertmanager.yml:4-16` |
| Alert forwarder | “Alert” / “forwarder” (no file/service name on the figure) | Compose service `incident-bridge`. `services/incident-bridge/app.py`; `evidence.py` PromQL + `collect_agent_activity`. Compose image has no `kubernetes` / kubeconfig. jsonl only with `--profile agents`. README names the service once at first mention (Quick start) |
| Grafana | (name only; grey edge from Prometheus) | `grafana/grafana:10.4.2` `docker-compose.yml:217-222`; dashboard `sre-dashboard.json:8-22` |
| AI Incident Diagnosis | Grok hex avatar | Imported template; not source in this repo. README link `https://x.ai/bot/feQpDSeSki7HVgkDCBUaY` |
| Incident Remediation | tilted orange capsule, two white capsule eyes (no pale tile) | Drawn in `remediator_avatar()` (same mark as `docs/icons/remediation-bot.png`). Template `https://x.ai/bot/8rxdqPVj5W-mksKhNfcw5`. Invoked only by Diagnosis (no webhook, no repo watch). Proposes; does not execute |
| GitHub issue | “GitHub” | Diagnosis bot files `incident` issues. Sample: issue #5. Path A does **not** open issues (`orchestrator.py` writes `reports/`) |
| Owner ping | centered above Diagnosis | Diagnosis-bot template at import (not in this repo). Firing critical alerts chat-ping the owner |
| Owner | “/approve” | `remediation/approval.py` `APPROVE_RE`; workflow `remediation-approve.yml` |
| Actions | “records” (GitHub icon) | `.github/workflows/remediation-approve.yml` records `/approve`; it does not run the fix |
| host poller | “or SSM” | `remediation/poll_and_apply.py` on the host, or `remediate.py --via-ssm` |

---

## 3. Diagram arrows and pills

IAM has no chain arrow (Terraform creates the role + instance profile). SG is a box, not an arrow. Figure 1 badges are ①–⑩ (orange diagnosis, blue remediator). Figure 2 badges ①–④ are a separate count. Request-path edges below are **not** drawn on Figure 1.

| # | Arrow | Pill | Evidence |
|---|---|---|---|
| (omitted from Figure 1) | Terraform → VPC border (prior figure) | (none) | Operator laptop, outside AWS. `terraform/main.tf`. Current Figure 1: grey Terraform → EC2, then a straight grey vertical into the host |
| (omitted from Figure 1) | deploy_remote.py → S3 / SSM (prior figure) | (none) | Zip upload `_upload_payload`; `ssm.send_command` `AWS-RunShellScript`. Not drawn on the current figure |
| (omitted from Figure 1) | put_lab_secrets.py → Param Store | (none) | `scripts/put_lab_secrets.py` SecureString; host `GetParameter` in `build_host_env_script`. Empty values stored as `__EMPTY__` |
| (omitted from Figure 1) | Traffic → api-gw | (none) | `load_generator.py:40`, `:58`, `:78`; compose `GATEWAY_URL=http://api-gw:8000` `docker-compose.yml:127` |
| (omitted from Figure 1) | api-gw → order-service | (none) | `api-gw/main.py:92-111` strips prefix and proxies to `ORDER_SERVICE_URL`; generator POSTs `/api/orders/orders` `load_generator.py:58` |
| (omitted from Figure 1) | order-service → payment-service | (none) | `order-service/main.py:250` `POST {PAYMENT_SERVICE_URL}/payments` |
| (omitted from Figure 1) | api-gw → payment-service | (none) | `api-gw/main.py:113-132`; generator `/api/payments/payments` `load_generator.py:78` |
| (omitted from Figure 1) | order-service → Redis / Postgres | (none) | Redis `setex` and Postgres INSERT in `order-service/main.py` create-order path; compose env `REDIS_HOST=redis`, `POSTGRES_DB=orders_db` |
| ② (orange; Figure 2) | Red Team → order-service **and** payment-service | badge ② | Infra faults hit order-service (`infra_disruptor.py:40-47`, catalog `/fault/leak-memory`, `/fault/redis-starvation`, `/fault/cpu-burn`, `/fault/crash`). Network faults hit payment-service (`fault_catalog.py:45-80` `/fault/latency`, `/fault/drop-rate` on `eth0`). **Not** Traffic |
| ③ (blue; Figure 2) | Blue Team → Target services group | badge ③ | `GET /health` on api-gw (4s), order, payment: `monitor.py:52-95`. Reset: `fault_catalog.py:125-128` POSTs `/fault/reset` on **order-service and payment-service only** |
| ① (orange; Figure 2) | How to start | badge ① on the “How to start” group label | Compose profile, host CLI (`python3 orchestrator.py`), or k3s |
| ④ (orange; Figure 2) | Target services → Prometheus | badge ④ | Continues on the diagnosis path (`orchestrator.py` hold, then Path B) |
| ① | Services group → Prometheus (scrape) | badge ① | `prometheus.yml:22-33` jobs `api-gw:8000`, `order-service:8001`, `payment-service:8002`; scrape `1s`. Orange pull into Prometheus |
| ② | Prometheus → Alertmanager | badge ② | `prometheus.yml` `alertmanager:9093`; rules `dashboards/alerts.yml` |
| ③ | Alertmanager → Alert forwarder | badge ③ | `alertmanager.yml:14-16` `http://incident-bridge:8080/webhook` `send_resolved: true` |
| ④ | Alert forwarder → Diagnosis | badge ④ | `app.py` outbound `{status, alerts, evidence, source: "resilienceops"}`; HTTPS to `GROK_WEBHOOK_URL` |
| ⑤ | Diagnosis → GitHub (straight, same row) | badge ⑤ | Imported diagnosis bot opens or comments on an `incident` issue |
| ⑥ | Diagnosis → owner ping | badge ⑥ | Firing critical alerts chat-ping the owner. That bot has no control path into the stack |
| ⑦ | Diagnosis hex bottom → Incident Remediation (straight vertical) | badge ⑦ (blue, on this shaft) | After filing or commenting on a firing `incident` issue, the Diagnosis bot asks its teammate to propose a fix. The Remediation bot has no webhook and does not watch the repo |
| ⑧ | Incident Remediation → GitHub issue | badge ⑧ (blue) | Remediator comments a proposal on the `incident` issue (`remediation/actions.py` `parse_proposal`) |
| ⑨ | Owner `/approve` → Actions | badge ⑨ (blue) | Workflow `remediation-approve.yml` records `/approve`; it does not run the fix |
| ⑩ | host poller → services group | badge ⑩ (blue) | Host poller `remediation/poll_and_apply.py` or `remediate.py --via-ssm` runs the allowlisted action. Arrow lands on the **services group** |
| (unnumbered, grey) | Prometheus → Grafana | (none) | Grafana is **not** on the alert path. Datasource provisioning `dashboards/provisioning/datasources/prometheus.yaml` |
| (omitted) | Alert forwarder ⇢ Prometheus | (none on the figure; README Reference) | `evidence.py` range queries; `app.py` `collect_evidence`. Kept off the figure so the diagnosis row stays a straight line |
| (omitted) | agents → api-gw `/api/agent-events`; agents → `agent_activity.jsonl` → bridge | Agents caption `POST /api/agent-events · jsonl`; bridge caption `PromQL · agent jsonl (Compose agents)`; CW `agents → CW`. No extra shaft | `structured_logger.py` POST `/api/agent-events` + jsonl; `evidence.py` `collect_agent_activity` |
| (omitted) | operator → SG `:3000 / :8000` | SG title `SG  ingress + internal  ·  :3000 / :8000`. No IGW→SG arrow | `ingress_sg` Grafana 3000 + API 8000 to `allowed_cidr` |

---

## 4. Diagram chrome (gate + cards)

| Element | Text | Evidence |
|---|---|---|
| Gate line 1 | “The bot has no control path into the stack: it only receives webhooks and writes GitHub issues.” | Bot template (not in-repo). Path A **does** reset/restart when k8s toolkit is available (`remediator.py`) — that is not the bot |
| Gate line 2 | “AWS/EC2 is optional: docker compose up runs the same stack (agents need --profile agents). The bridge needs outbound HTTPS to the bot; agents also call Anthropic.” | Local Compose `docker-compose.yml`; `agent-sandbox` profile; bridge POST `forwarding.py`; agents `llm_engine.py` |
| Card 1 | “Held fault (FAULT_HOLD_SECONDS, default 120) or a real outage trips a Prometheus alert rule.” | `FAULT_HOLD_SECONDS` default 120 (`orchestrator.py`). Rules in `dashboards/alerts.yml`. Real `up==0` / SLO / Redis saturation fire without `/fault` |
| Card 2 | “Bridge adds PromQL + jsonl and posts enriched JSON to the bot.” | `app.py` `collect_evidence`; jsonl only when agents write `logs/agent_activity.jsonl` |
| Card 3 | “Bot diagnoses and files or updates a GitHub issue.” | Imported template; samples issues #4 (synthetic) and #5 (live) |

---

## 5. README — architecture & dual path

| Claim | Evidence |
|---|---|
| 3-agent Red / 3-agent Blue | `orchestrator.py:41-50`; models `agents/config.py:31-39` |
| Models `claude-sonnet-4-6` / `claude-haiku-4-5-20251001` | `agents/config.py:31-39` |
| Path A = orchestrator; Path B = Prom → AM → Alert forwarder → Grok | `orchestrator.py`; `prometheus.yml` + `alertmanager.yml` + `app.py` |
| Traffic POSTs api-gw at compose `RPS_TARGET` default **20**; module default **25** if unset | `docker-compose.yml:128`; `load_generator.py:9` |
| api-gw reverse-proxies `/api/orders*` and `/api/payments*` (prefix stripped) | `api-gw/main.py:92-132` |
| Order-service writes Redis + Postgres and POSTs `/payments` | `order-service/main.py` create-order |
| Prometheus scrape 1s, three jobs | `prometheus.yml:2,22-33` |
| Grafana not on alert path; Prom published `127.0.0.1:9090`; AWS also binds private IP for k3s | `docker-compose.yml` loopback; `docker-compose.prom-lan.yml` `${PROMETHEUS_BIND:?…}` + host `.env` `COMPOSE_FILE`; Grafana depends_on prometheus only |
| Fault CLI scenarios and substring dispatch | `orchestrator.py:69-74`; `infra_disruptor.py:8-17` |
| Detection: `/health` ×3, p99/5xx PromQL, SLO 1200ms / 2%, HTTP >= 500, max 9 ticks of 1s; then `FAULT_HOLD_SECONDS` (default 120) before remediation | `monitor.py`; `orchestrator.py` `range(1, 10)` + `hold_fault_for_alerts` |
| Alertmanager `group_wait: 5s`, `group_interval: 15s`, `repeat_interval: 1h`, compose target `alertmanager:9093`, host `127.0.0.1:9093` | `alertmanager.yml:7-9`; `prometheus.yml:20`; `docker-compose.yml:159-168` |
| Bridge drop if URL empty; dedupe 300s; payload ~100KB; source `resilienceops` | `app.py:130-132`; `settings.py:55-58`; `forwarding.py:19-21,110` |
| Forward failure: ERROR log, dead-letter, retry queue, no ASGI crash | `app.py:164-187`; `forwarding.py:242-310`; ASGI wrapper `app.py:214-218` |
| httpx must not log `GROK_WEBHOOK_URL` | `app.py:31-32` `logging.getLogger("httpx").setLevel(logging.WARNING)` |
| `agent_activity` empty unless agents profile / host orchestrator | compose `agent-sandbox` `profiles: [agents]` `docker-compose.yml:239-241`; logger writes `logs/agent_activity.jsonl` `structured_logger.py:13-33` |
| Path A verify_recovery max 5, latency < 800ms; always `reset_environment` | `remediator.py`; orchestrator holds `FAULT_HOLD_SECONDS` then resets in `finally` so no-incident cycles cannot pile faults |
| Path A writes `reports/incident_*.md`; does not open GitHub issues | `orchestrator.py` phase 7 writes `reports/` |
| Diagnosis bot has no control path into the stack (webhooks in, GitHub issues out); duplicate fingerprint comments; resolved comments; critical owner ping | Imported template (not in this repo). Documented as template behavior. Samples: issues #4 and #5 |
| Path C = Diagnosis hands off → proposal → `/approve` → host poller / SSM; allowlist `reset_fault` / `restart_service` / `rollback_deploy` | Diagnosis teammate (not in-repo). `remediation/actions.py`; `.github/workflows/remediation-approve.yml`; `remediation/poll_and_apply.py`; `--via-ssm` reuses `deploy_remote.send_and_wait` |

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
| Operator IAM: customer managed policy `ResilienceOpsDeployer` via `create-policy` + `attach-user-policy` / `attach-role-policy` (inline user policies cap at 2,048 chars); teardown `detach-*-policy` + `delete-policy` | `terraform/deployer-policy.json` minified `< 6144`; README AWS → Two AWS identities + `teardown.sh` / `teardown.ps1` |
| Host `.env` from Parameter Store SecureString, not SendCommand | `scripts/put_lab_secrets.py`; `deploy_remote.py` `build_host_env_script` (`get-parameter --with-decryption`) |
| No NAT Gateway / no EKS in this Terraform | No `aws_nat_gateway` / `aws_eks_cluster` resources in `terraform/main.tf` |
| CloudWatch **log groups** + audit **stream** are Terraform; **dashboards** are not | Groups + `aws_cloudwatch_log_stream.audit` name `audit-stream` in `terraform/main.tf`. Logger `structured_logger.py` `CreateLogStream` if missing then `PutLogEvents`. Compose `agent-sandbox` gets `AWS_REGION`. Host inline `logs:CreateLogStream`/`PutLogEvents`. Helpers `create_cw_dashboard.py:63-65` name `SRE-Autonomous-Agent-Security-Audit`; `test_grafana_proxy.py:5` name `SRE-fault-Vectors-Live-Telemetry`. `dashboards/cloudwatch-dashboard.json` deleted (metrics `ResilienceOps/Agents` + `AWS/ApplicationELB` + `/aws/sre-arena/*` are not produced; no ALB in Terraform) |
| Figure 3 is a dated console map | PNG `docs/images/aws_vpc_resource_map.png`, cropped to the resource-map cards (VPC / subnets / route tables / IGW) so labels stay readable at README width. Shows Terraform’s 3 subnets. |

---

## 7. README — install, ports, env, commands

| Claim | Evidence |
|---|---|
| Python 3.10+ for host; images are `python:3.11-slim` | service Dockerfiles `FROM python:3.11-slim`; CI `python-version: "3.11"` `.github/workflows/ci.yml:23` |
| Grafana admin vars required (`:?Set GRAFANA_ADMIN_USER`) | `docker-compose.yml:221-222` |
| Compose interpolates Grafana, Postgres, Grok, bridge tunables, RPS, sandbox key, SLO | `docker-compose.yml` `${…}` + `.env.example`; enforced by `tests/test_docs_consistency.py` |
| `GROK_WEBHOOK_AUTH_SCHEME-Bearer` (present-but-empty sends raw key) | `docker-compose.yml:190`; `settings.py:23-27` |
| Host URLs default localhost:8000/8001/8002/9090 | `agents/config.py:4-9`; `.env.example:28-33` |
| Bridge container Prometheus `http://prometheus:9090` | `docker-compose.yml:191`; `.env.example:34` |
| Ports: api-gw 8000, order 8001, payment 8002, Grafana 3000, Prom `127.0.0.1:9090` (+ private IP on AWS), AM `127.0.0.1:9093`, bridge `127.0.0.1:8088`→8080 | `docker-compose.yml`; `docker-compose.prom-lan.yml` |
| Redis / Postgres published on loopback only | `docker-compose.yml:96-97,107-108` (`127.0.0.1:6379`, `127.0.0.1:5432`) |
| Local Grafana `http://127.0.0.1:3000`; login `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD`; folder `SRE & Reliability`; dashboard `SRE Infrastructure & Reliability Performance Monitor`; provisioned automatically | `docker-compose.yml:218-225`; `dashboards.yaml:6`; `sre-dashboard.json:9` |
| Alertmanager UI `http://127.0.0.1:9093` | compose bind `127.0.0.1:9093:9093` `docker-compose.yml:167-168` |
| api-gw `GET /health` + `POST /api/orders/orders` body `{item_id, quantity, amount, user_id}` | `api-gw/main.py:64-66,92-111`; `CreateOrderRequest` `order-service/main.py:129-133`; generator `load_generator.py:52-58` |
| payment-service `GET /health` returns `status` / `service` / `tc_*` | `payment-service/main.py:39-47` |
| Fault endpoints + code defaults + `alerts.yml` mapping | `order-service/main.py:277-372` (`connections=55`, `mb=50`, `seconds=15`, `delay=2.5`, `rate=0.5`, crash, reset); `payment-service/main.py:79-131` (`delay_ms=2500`, `jitter_ms=100`, `loss_percent=30.0`, `enabled=True`, reset); rules `dashboards/alerts.yml` |
| Any critical inhibits same-`service` warning (`/fault/latency` → **PaymentServiceP99LatencySLO** fires; **PaymentServiceLatencyHigh** inhibited) | `alertmanager.yml:18-23` `equal: ["service"]`. Redis row already notes the sibling warning is inhibited |
| `remediate.py` `--proposal-file` / `--proposal-text` / `--skip-verify` / `--verify-timeout` default 45 | `remediate.py:100-114` |
| `poll_and_apply.py` `--loop` / `--interval` default 20 (sleep `max(5, interval)`) / `--dry-run` | `poll_and_apply.py:93-118` |
| `send_test_alert.py` `--alertmanager-url` / `--bridge-url` | `send_test_alert.py:70-72` |
| `put_lab_secrets.py` `--prefix` / `--env-file` | `put_lab_secrets.py:61-63` |
| `deploy_remote.py` `--region` / `--bucket` / `--ssm-prefix` / `--profile agents` / `--skip-wait-ssm`; rerun after code changes | `deploy_remote.py:323-334,354-367` (`unzip -o` + `compose up --build -d`) |
| `deploy_k8s_sandbox.py` `--skip-copy` / `--skip-wait-ssm` | `deploy_k8s_sandbox.py:118-119` |
| SSM port-forward `AWS-StartPortForwardingSession` for 9090 / 8088 / 3000 | README AWS Terraform; Session Manager document name (not in Terraform) |
| `python3 -m pytest -q`; CI = pytest `tests/` + `validate_yaml.py` + promtool/amtool + gitleaks | `pytest.ini` `testpaths = tests`; `.github/workflows/ci.yml:31-55,75-78` |
| `RPS_TARGET` compose 20 / module 25; `CONCURRENCY` compose 8 / module 10 | `docker-compose.yml:128-129`; `load_generator.py:9-10` |
| `agent-sandbox` profile opt-in; CMD injects faults | `docker-compose.yml:239-241`; `Dockerfile.agent-sandbox` |
| `curl 127.0.0.1:8088/healthz` → `webhook_configured` | `app.py:198-203` |
| `send_test_alert.py --target alertmanager` → `127.0.0.1:9093/api/v2/alerts` | `scripts/send_test_alert.py:70-77` |
| `--target bridge` → `127.0.0.1:8088/webhook` | `send_test_alert.py:72,79-80` |
| Full demo `POST http://127.0.0.1:8001/fault/redis-starvation` then `/fault/reset` | `order-service/main.py:277,352`; alert `RedisConnectionSaturation` `alerts.yml:178-187` (`for: 5s`, `>= 48`) |
| Live timing **12.1 s** fault→webhook, **~61 s** to issue #5 | Operator hops `examples/live_run_issue5_timeline.md` (21:50:59 fault → 21:51:11.134 webhook 200; 21:51:05.886 `startsAt` → 21:52:06 issue). Redacted bridge lines `examples/live_run_issue5_bridge.log`. Public issue https://github.com/ritvikindupuri/ResilienceOps/issues/5. Warning inhibited (`inhibit_rules`). Default compose: **no `agents`**, so `agent_activity` empty |
| Issue #5 screenshots (public crops, no webhook key) | `docs/images/sample-incident-issue-5-{1,2,3}.png`; fingerprint `279c3ab8f16c75be`; “Agent activity: none attached” |
| `orchestrator.py --cycles 1 --scenario MEMORY_EXHAUSTION` | `orchestrator.py:9-10,118-123` |
| `deploy_remote.py` zip omits `.env`; includes `reports/` | `deploy_remote.py` `should_exclude` / `INCLUDE_PATHS`; `tests/test_deploy_archive.py` |
| SSM session, no SSH | `terraform/main.tf:191-196`; README [Agent sandbox](../README.md#agent-sandbox) (`--region`) |
| `teardown.sh` → `terraform destroy -auto-approve` + SSM `delete-parameters` under `/resilienceops` + verify describe-instances / S3 / log groups | `teardown.sh:33-44,47-53`; `teardown.ps1` |
| k3s sandbox: `deploy_k8s_sandbox.py` applies `namespace-rbac.yaml` then `agent-sandbox.yaml`; copies repo code; `--target-ip` is host private IP | `deploy_k8s_sandbox.py`; `k8s/apps/microservices.yaml` is opt-in `--apply-microservices` |
| Host pip is **not** required for Compose-only | Service images `pip install -r requirements.txt` in Dockerfiles |
| Regen PNG: `scripts/render_architecture.sh` / `rsvg-convert` **2×** (2960×2560 main; sandbox 2360×1560) | `scripts/render_architecture.sh`; `build_architecture.py` viewBox 1480×1280 and 1180×780 |

Env-var inventory: every `os.getenv` / `_env_int` / `_env_float` name is in `.env.example` and mentioned in the README table — `tests/test_docs_consistency.py:57-72,89-92`.

---

## 8. README — sandbox, Grafana, troubleshooting

| Claim | Evidence |
|---|---|
| Namespace `sre-agent-sandbox`, limits `500m` / `512Mi` | `k8s/agents/agent-sandbox.yaml:8-11,75-78,121-124` |
| NetworkPolicy: DNS 53, victim ns `arena.sre.io/role=victim`, TCP 443, VPC Compose 8000–8002/9090 | `k8s/agents/agent-sandbox.yaml:129-172`; victim label `k8s/base/namespace-rbac.yaml:3-6` |
| Red Role `get/list/watch` on `pods` + `pods/exec` in `sre-target-apps` | `k8s/agents/agent-sandbox.yaml:23-31` |
| Blue Role pods/logs/events/deployments in `sre-target-apps` | `k8s/base/namespace-rbac.yaml:32-51` |
| Operator `kubectl exec` uses **operator** kubeconfig, not the sandbox SA | Host commands in README [Agent sandbox](../README.md#agent-sandbox); Role has no `create` on `pods/exec` |
| Grafana folder `SRE & Reliability`, dashboard title `SRE Infrastructure & Reliability Performance Monitor` | `dashboards.yaml:6`; `sre-dashboard.json:9` |
| `liveNow: true`, `refresh: 1s`, window `now-5m` | `sre-dashboard.json:17-21` |
| Availability threshold 99.9 | `sre-dashboard.json:69` |
| Memory panel vs 256MB cgroup (compose `memory: 256M`) | compose `docker-compose.yml:49,80`; dashboard query `/ 1024 / 1024` and threshold `256` `sre-dashboard.json:273-312` |
| Grafana dashboard panels | Eight `"title"` entries in `sre-dashboard.json:44,85,112,153,200,240,272,327` |
| FastAPI `0.111.0`, HTTPX `0.27.0`, Pydantic `2.8.2` | `services/api-gw/requirements.txt`; `services/order-service/requirements.txt:1-7` |
| Prometheus `v2.52.0`, Alertmanager `v0.27.0`, Grafana `10.4.2` | compose image tags |
| Redis 7 / Postgres 16 | `redis:7-alpine`, `postgres:16-alpine` |
| Compose healthchecks + `service_healthy` | `docker-compose.yml` `healthcheck` / `condition: service_healthy` |
| order-service `/ready` requires Redis + Postgres connected | `order-service/main.py:170-181`; `/health` stays 200 during faults `:135-167` |
| Postgres retry/backoff | `order-service/main.py:78-113` |
| Containers cannot reach each other (FORWARD / iptables) | Operational; check commands use compose DNS as in `prometheus.yml:25-33` and `alertmanager.yml:14` |
| Webhook 401/403 = bot rejected auth | `forwarding.py:218` / `RETRYABLE_STATUS` (`forwarding.py:21`). Non-retryable statuses such as 401/403 are not retried. README troubleshooting |
| Dedupe 5 minutes, resolved is a different status | `forwarding.py:72-79`; `DEDUPE_TTL_SECONDS` default 300 `settings.py:57` |

---

## 9. Intentional simplifications (not bugs)

| Simplification | Why |
|---|---|
| Unused subnets are a caption, not empty boxes | Avoids blank green rectangles; CIDRs are on the VPC title row (not the `public_ingress` header) |
| IAM has no arrow | Terraform creates the role + instance profile; drawing Terraform→IAM would cross the account strip |
| Two Red forks on Figure 2 (orange badge ②); no `faults` pill | Covers four order-service `/fault/*` plus two payment-service `tc netem` endpoints without six arrows |
| Prometheus node has no caption | Space under the observability row is Grafana; scrape detail is orange badge ① on Figure 1 |
| One scrape edge (Figure 1 badge ①) | Three Prometheus jobs share one orange edge out of the services group. Separate from Figure 2’s Blue arrow (badge ③) onto the Target services group |
| Grok `incident` label, duplicate-comment, owner ping | Implemented by the **imported** Grok template, not this repository. Samples #4/#5 show the behavior |
| “Eliminates NAT ($32/mo) / EKS ($72/mo)” | Cost comparison: those resources are not in `main.tf`. Not a bill guarantee |
| Teardown “under 60 seconds” / “100% protected” host daemons | Timing and absolute guarantees are not asserted by tests |
| Figure 3 AWS console screenshot | Dated live capture; shows Terraform's 3 subnets. |

---

## 10. Out of scope / not claimed by the code

- Grok Bot internals (prompt, GitHub app permissions, chat ping routing) live on x.ai, not in this git tree.
- `k8s/apps/microservices.yaml` is an alternate in-cluster deploy of the apps; the documented AWS path runs Compose on the EC2 host plus k3s **sandbox**.
- Historical PDF `docs/ResilienceOps_Technical_Documentation.pdf` is not the source of truth (`README.md` overview).
