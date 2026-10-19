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
| Terraform / IAM / SSM / IGW drawn inside `public_ingress` | Terraform + `deploy_remote.py` are operator-side (above the VPC). IAM + SSM sit in an **AWS account** strip outside the VPC, with `deploy_remote.py → SSM → EC2`. IGW sits on the VPC border. Inside `public_ingress`: k3s, Compose, and a dashed SG around the host (`build_architecture.py:362-400,437-441`) |
| Blue Team arrow landed on order-service only | Three ticks: `health ×3` into api-gw, order-service, payment-service (`monitor.py:52-95`); `reset ×2` into order-service and payment-service (`fault_catalog.py:122-132`) |
| AWS README listed only `sts:GetCallerIdentity`; apply 403'd on a read-only principal | Checked-in operator policy `terraform/deployer-policy.json` (EC2/VPC create+delete, IAM CreateRole/DeleteRole/PassRole/instance-profile, SSM SendCommand/GetCommandInvocation/DescribeInstanceInformation/PutParameter, S3 deploy bucket, CW log groups) |
| `deploy_remote.py` started a subset of Compose services (no alertmanager / incident-bridge); inline ~98 KB base64 vs 100 KB SSM limit; no `reports/`; printed CommandId only; no SSM Online wait; API-key check read empty SSM env | S3 + presigned GET; `docker compose up --build -d` (all default services) + `--profile agents`; archive includes `reports/`; `wait_for_ssm_online` + `cloud-init status --wait`; `GetCommandInvocation` fail-nonzero; host `.env` from Parameter Store SecureString (`scripts/put_lab_secrets.py`) |
| `user_data` installed Compose v1; default `t3.small`; no `instance_id`/`region` outputs; IMDS hop 1; instance role SSM-only | Compose v2 plugin (`docker-compose-v2`); default `t3.medium` (~$0.0416/hr + ~$0.005/hr IPv4); outputs `instance_id`, `region`, `deploy_bucket`, `private_ip`; hop limit 2; inline GetParameter / S3 GetObject / `logs:PutLogEvents`; Terraform **log groups** (dashboards still helper scripts) |
| k3s sandbox undocumented; `orchestrator.py` missing in the pod; `--target-ip` used k8s DNS for Compose apps; faults piled up when Blue did not declare in 9s | `deploy_k8s_sandbox.py` applies `namespace-rbac.yaml` + `agent-sandbox.yaml`, copies repo code, targets host private IP. Orchestrator `finally` always `FaultCatalog.reset_environment()`. Duplicate Path B fingerprint comments on the open GitHub issue |

---

## 1. Diagram groups

| Element | What the figure says | Evidence |
|---|---|---|
| Canvas | 1920×1200, title “How ResilienceOps + AI Incident Diagnosis works” | `scripts/build_architecture.py:360`, title in `build()` |
| Operator (outside AWS) | Terraform + `deploy_remote.py` above the VPC | `build_architecture.py:366,437-438`; Terraform is IaC on the operator laptop, not an ENI |
| AWS account strip | “AWS account  ·  outside the VPC” holds IAM + SSM | `build_architecture.py:367-368,379-383,439-440` |
| VPC group | Purple dashed, “VPC  sre-enterprise-vpc”, AWS VPC icon | `build_architecture.py:234-241`, `:375-378`; Name tag `terraform/main.tf:74-83` |
| Public subnet group | Green, “public_ingress  ·  one EC2 host”, public-subnet icon | `build_architecture.py:242-249`, `:388-392`; `terraform/main.tf:93-104` (only subnet with `map_public_ip_on_launch` and the only one associated with the public RT `:144-147`) |
| SG around host | Dashed red “SG  ingress + internal” wrapping k3s + Compose | `build_architecture.py:251-258,394-401`; SGs `terraform/main.tf:168-239` |
| k3s group | Nested “k3s on this host” | `build_architecture.py:413`; k3s installed on the **same** EC2 `user_data` `terraform/main.tf:437-456` (`https://get.k3s.io`) |
| Compose group | Nested “Compose lab on this host”, Docker icon | `build_architecture.py:414`; `docker-compose.yml` entire file; deploy zip includes compose (`deploy_remote.py` `INCLUDE_PATHS`) |
| Grok column | “Grok Bot  ·  local or AWS” | `build_architecture.py:374`. Bot is imported, not hosted in-repo. Works on laptop Compose or AWS as long as the bridge can POST HTTPS (`README.md:150`, `GROK_WEBHOOK_URL` in `docker-compose.yml:180`) |
| Unused subnets | Caption only (no empty boxes), top-right of `public_ingress`: `unused: 10.0.10.0/24 · 10.0.20.0/24` | `build_architecture.py` unused caption; created `terraform/main.tf:121-142`; **no** `aws_instance` / RT assoc / SG attachment uses them (instance `subnet_id` is `public_ingress` `:413`) |

---

## 2. Diagram nodes (boxes)

| Node | Caption on figure | Evidence |
|---|---|---|
| Terraform | “optional AWS” (outside the VPC) | `build_architecture.py:437`. AWS is not required for Compose. `terraform/main.tf` is the optional cloud host, run on the operator laptop |
| deploy_remote.py | “operator” (outside the VPC) | `build_architecture.py:438`; `deploy_remote.py` builds a zip, uploads to S3, `ssm.send_command` |
| IAM satellite | “role + instance profile” in the AWS account strip | `build_architecture.py:439`; `aws_iam_role.sre_host_role` name `sre-platform-host-role` `terraform/main.tf:245-262`; instance profile `sre-platform-instance-profile` `:323-326` |
| SSM satellite | “send_command” in the AWS account strip | `build_architecture.py:440`; `AmazonSSMManagedInstanceCore` `terraform/main.tf:265-267`; `deploy_remote.py` `send_and_wait` / `AWS-RunShellScript` |
| SG box | “ingress + internal” around the host, not a satellite in the subnet | `build_architecture.py:397-401`; `aws_security_group.ingress_sg` `sre-ingress-sg` `terraform/main.tf:168-205`; `internal_app_sg` `sre-internal-app-sg` `:208-239` |
| IGW satellite | “public RT only”, on the VPC border (outside the green subnet) | `build_architecture.py:429,441`; `aws_internet_gateway.igw` Name `sre-enterprise-igw` `terraform/main.tf:85-91`; public RT `0.0.0.0/0` via IGW `:131-137`; association **only** `public_ingress` `:144-147` |
| k3s | “Agent sandbox” | `k8s/agents/agent-sandbox.yaml:8-11` namespace `sre-agent-sandbox`; README step 10 |
| Red Team | “Injects faults” | `orchestrator.py:41-44`, `:64-74`; `agents/fault_injector/infra_disruptor.py:31-47`; `agents/fault_injector/network_adversary.py` |
| Blue Team | “Detects and resets” | `orchestrator.py:46-50`, `:76-114`; `monitor.py`; `remediator.py:24-49` always `FaultCatalog.reset_environment()` |
| Traffic | “Live load” | `docker-compose.yml:120-129` `traffic-generator`; `traffic-generator/load_generator.py:8-12` |
| api-gw | “Gateway” | `services/api-gw/main.py`; compose port `8000:8000` (`docker-compose.yml:6`); uvicorn `:136` |
| order-service | “Orders” | `services/order-service/main.py`; compose `8001:8001` (`docker-compose.yml:32`); uvicorn `:376` |
| payment-service | “Payments” | `services/payment-service/main.py`; compose `8002:8002` (`docker-compose.yml:70`); uvicorn `:135` |
| Redis | “order-service cache” | compose `redis:7-alpine` `docker-compose.yml:92-95` (`maxclients 50`); order-service `REDIS_HOST` `:25-32`, `setex` around create-order |
| PostgreSQL | “orders_db” | compose `postgres:16-alpine` `POSTGRES_DB=orders_db` `docker-compose.yml:103-109`; order-service `POSTGRES_DB` `:39` |
| Prometheus | “Scrapes + rules” | image `prom/prometheus:v2.52.0` `docker-compose.yml:132`; `dashboards/prometheus.yml:1-12` |
| Alertmanager | “Groups alerts” | image `prom/alertmanager:v0.27.0` `docker-compose.yml:153`; `dashboards/alertmanager.yml:4-16` |
| incident-bridge | “PromQL · jsonl · k8s” | `services/incident-bridge/app.py`; evidence in `evidence.py`; compose `127.0.0.1:8088:8080` `docker-compose.yml:178` |
| Grafana | (no caption; sits under Prometheus) | `grafana/grafana:10.4.2` `docker-compose.yml:210-212`; dashboard `sre-dashboard.json:8-22` |
| AI Incident Diagnosis | Grok hex avatar | Imported template; not source in this repo. README link `https://x.ai/bot/feQpDSeSki7HVgkDCBUaY` |
| GitHub issue | “label: incident” | Bot behavior (imported template). Sample: issue #5 label `incident`. Path A does **not** open issues (`orchestrator.py:112-115` writes `reports/`) |
| Owner ping | “Firing critical” | Bot template at import (not in this repo). README `:40`, `:666` |

---

## 3. Diagram arrows and pills

IAM has no chain arrow (Terraform creates the role + instance profile). SG is a box, not an arrow. Numbering matches comments in `build_architecture.py`.

| # | Arrow | Pill | Evidence |
|---|---|---|---|
| 1 | Terraform → public_ingress / EC2 host | (none) | Operator laptop, outside AWS. `terraform/main.tf:410-476`. `build_architecture.py:522-527` |
| 1b | deploy_remote.py → SSM → EC2 host | (none) | `deploy_remote.py` `send_and_wait`. `build_architecture.py:529-536` |
| 2 | Traffic → api-gw | `requests` | `load_generator.py:40`, `:58`, `:78`; compose `GATEWAY_URL=http://api-gw:8000` `docker-compose.yml:124` |
| 3 | api-gw → order-service | `/api/orders` | `api-gw/main.py:92-111` strips prefix and proxies to `ORDER_SERVICE_URL`; generator POSTs `/api/orders/orders` `load_generator.py:58` |
| 4 | order-service → payment-service | `POST /payments` | `order-service/main.py:250` `POST {PAYMENT_SERVICE_URL}/payments` |
| 5 | api-gw → payment-service U-turn | `/api/payments` | `api-gw/main.py:113-132`; generator `/api/payments/payments` `load_generator.py:78` |
| 6–7 | order-service → Redis / Postgres | (none; short drops) | Redis `setex` and Postgres INSERT in `order-service/main.py` create-order path; compose env `REDIS_HOST=redis`, `POSTGRES_DB=orders_db` |
| 8 | Red Team → order-service **and** payment-service | `faults` | Infra faults hit order-service (`infra_disruptor.py:40-47`, catalog `/fault/leak-memory`, `/fault/redis-starvation`, `/fault/cpu-burn`, `/fault/crash`). Network faults hit payment-service (`fault_catalog.py:45-80` `/fault/latency`, `/fault/drop-rate` on `eth0`). **Not** Traffic. One flyover + two ticks (`build_architecture.py:548-560`) instead of one arrow per endpoint |
| 9 | Blue Team → api-gw, order-service, payment-service | `health ×3` and `reset ×2` | `GET /health` on api-gw (4s), order, payment: `monitor.py:52-95`. Reset: `fault_catalog.py:122-132` POSTs `/fault/reset` on **order-service and payment-service only** (api-gw has no `/fault/reset`). Three ticks; two pills (`build_architecture.py:572-589`) |
| 10 | Blue Team → Prometheus | `query` | `monitor.py:15-25`, `:98-110` PromQL if `PROMETHEUS_URL` answers |
| 11 | Services → Prometheus | `3 scrape jobs` | `prometheus.yml:22-33` jobs `api-gw:8000`, `order-service:8001`, `payment-service:8002`; scrape `1s` `:2` |
| 12 | Prometheus → Alertmanager | `firing alerts` | `prometheus.yml:14-20` `alertmanager:9093`; rules `dashboards/alerts.yml` |
| 13 | Alertmanager → incident-bridge | `webhook` | `alertmanager.yml:14-16` `http://incident-bridge:8080/webhook` `send_resolved: true` |
| 14 | Prometheus → Grafana | `reads` | Grafana is **not** on the alert path. Datasource provisioning `dashboards/provisioning/datasources/prometheus.yaml`. Host Grafana `:3000` (`docker-compose.yml:212`) |
| 15 | incident-bridge ⇢ Prometheus (dashed) | `PromQL` | `evidence.py:29-67` range queries; `app.py` `collect_evidence` |
| 16 | incident-bridge → Grok avatar | `enriched JSON` | `app.py` outbound `{status, alerts, evidence, source: "resilienceops"}` (`:155-160`); HTTPS to `GROK_WEBHOOK_URL` |
| 17–18 | Grok → GitHub / owner ping | `read-only` | Imported bot. Path B never restarts/scales/pushes (`README.md:13`, gate `build_architecture.py:641-648`) |

---

## 4. Diagram chrome (gate + cards)

| Element | Text | Evidence |
|---|---|---|
| Gate line 1 | “Read-only: the bot never restarts, scales, or pushes” | `build_architecture.py:641-643`; bot template (not in-repo). Path A **does** reset/restart when k8s toolkit is available (`remediator.py:24-52`) — that is not the bot |
| Gate line 2 | “AWS/EC2 is optional: docker compose up is the same lab. The bot only needs outbound HTTPS from the bridge.” | `build_architecture.py:645-648`; local Compose `docker-compose.yml`; bridge POST `forwarding.py:178-236`; no inbound listener on the bot from this repo |
| Card 1 | “Fault or real outage trips a Prometheus alert rule.” | Fault injection is **optional**. Rules in `dashboards/alerts.yml`. Real `up==0` / SLO / Redis saturation fire without `/fault` |
| Card 2 | “Bridge adds evidence and posts enriched JSON to your bot.” | `app.py:143-187` |
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
| Grafana not on alert path; Prom published `127.0.0.1:9090` | `docker-compose.yml:135`; Grafana depends_on prometheus only |
| Fault CLI scenarios and substring dispatch | `orchestrator.py:69-74`; `infra_disruptor.py:8-17` |
| Detection: `/health` ×3, p99/5xx PromQL, SLO 1200ms / 2%, HTTP >= 500, max 9 ticks of 1s | `monitor.py:52-145`; `orchestrator.py:80` `range(1, 10)` |
| Alertmanager `group_wait: 5s`, `group_interval: 15s`, `repeat_interval: 1h`, compose target `alertmanager:9093`, host `127.0.0.1:9093` | `alertmanager.yml:7-9`; `prometheus.yml:20`; `docker-compose.yml:161` |
| Bridge drop if URL empty; dedupe 300s; payload ~100KB; source `resilienceops` | `app.py:130-132`; `settings.py:56-58`; `forwarding.py:16-17,107` |
| Forward failure: ERROR log, dead-letter, retry queue, no ASGI crash | `app.py:164-187`; `forwarding.py:242-310`; ASGI wrapper `app.py:214-218` |
| httpx must not log `GROK_WEBHOOK_URL` | `app.py:31-32` `logging.getLogger("httpx").setLevel(logging.WARNING)` |
| `agent_activity` empty unless agents profile / host orchestrator | compose `agent-sandbox` `profiles: [agents]` `docker-compose.yml:232-234`; logger writes `logs/agent_activity.jsonl` `structured_logger.py:13-33` |
| Path A verify_recovery max 5, latency < 800ms; always `reset_environment` | `remediator.py:24-83`; orchestrator also resets in `finally` (`orchestrator.py` cycle cleanup) so no-incident cycles cannot pile faults |
| Path A writes `reports/incident_*.md`; does not open GitHub issues | `orchestrator.py` phase 7 writes `reports/` |
| Bot read-only; duplicate fingerprint comments; resolved comments; critical owner ping | Imported template (not in this repo). Documented as template behavior. Samples: issues #4 and #5 |

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
| No SSH/22; no Prometheus 9090 on ingress SG | Comments `terraform/main.tf:191-192`; no `from_port = 22` / `9090` ingress rules |
| `allowed_cidr` rejects `0.0.0.0/0` | `terraform/main.tf:68-75` |
| IAM `sre-platform-host-role` + `AmazonSSMManagedInstanceCore` + instance profile + inline GetParameter/S3/logs | `terraform/main.tf:245-326` |
| EC2 `sre-enterprise-platform-host` default `t3.medium` (`instance_type` variable; t3.small optional) | `terraform/main.tf:52-59,410-412` |
| user_data: Docker Compose **v2** (`docker-compose-v2`) + awscli + unzip + 2G swap + k3s (`https://get.k3s.io`) | `terraform/main.tf:437-456` |
| IMDS hop limit 2, IMDSv2 required | `terraform/main.tf:423-428` |
| S3 deploy bucket `sre-resilienceops-deploy-<account>-<region>`, 1-day expiry | `terraform/main.tf:336-380` |
| Outputs `instance_id`, `region`, `deploy_bucket`, `private_ip`, `api_gateway_url` `:8000`, `grafana_url` `:3000`, Prometheus host-local | `terraform/main.tf:482-520` |
| Operator IAM: `terraform/deployer-policy.json` | File + README prerequisites |
| Host `.env` from Parameter Store SecureString, not SendCommand | `scripts/put_lab_secrets.py`; `deploy_remote.py` `build_host_env_script` (`get-parameter --with-decryption`) |
| No NAT Gateway / no EKS in this Terraform | No `aws_nat_gateway` / `aws_eks_cluster` resources in `terraform/main.tf` |
| CloudWatch **log groups** are Terraform; **dashboards** are not | Groups `terraform/main.tf:383-390`. Helpers `create_cw_dashboard.py:63-64` name `SRE-Autonomous-Agent-Security-Audit`; `test_grafana_proxy.py:5,102` name `SRE-fault-Vectors-Live-Telemetry`. Logger `structured_logger.py:84-88` |
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
| Ports: api-gw 8000, order 8001, payment 8002, Grafana 3000, Prom `127.0.0.1:9090`, AM `127.0.0.1:9093`, bridge `127.0.0.1:8088`→8080 | `docker-compose.yml:6,32,70,135,161,178,212` |
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
| Regen PNG: `scripts/render_architecture.sh` / `rsvg-convert` 1920×1200 | `scripts/render_architecture.sh:19-21`; `build_architecture.py:360` |

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
| Unused subnets are a caption, not empty boxes | Avoids blank green rectangles; CIDRs are on the figure (top-right of `public_ingress`) |
| IAM has no arrow | Terraform creates the role + instance profile; drawing Terraform→IAM would cross the account strip |
| One Red flyover + `faults` pill | Covers four order-service `/fault/*` plus two payment-service `tc netem` endpoints without six arrows |
| Prometheus node has no caption | Space under the observability row is Grafana; scrape/rule detail is the `3 scrape jobs` / `firing alerts` pills |
| One scrape arrow + `3 scrape jobs` | Three Prometheus jobs share one vertical |
| Grok `incident` label, duplicate-comment, owner ping | Implemented by the **imported** Grok template, not this repository. Samples #4/#5 show the behavior |
| “Eliminates NAT ($32/mo) / EKS ($72/mo)” | Cost comparison: those resources are not in `main.tf`. Not a bill guarantee |
| Teardown “under 60 seconds” / “100% protected” host daemons | Timing and absolute guarantees are not asserted by tests |
| Figure 3 AWS console screenshot | Dated live capture; subnet count in the console chrome may not match Terraform |

---

## 10. Out of scope / not claimed by the code

- Grok Bot internals (prompt, GitHub app permissions, chat ping routing) live on x.ai, not in this git tree.
- `k8s/apps/microservices.yaml` is an alternate in-cluster deploy of the apps; the documented AWS lab runs Compose on the EC2 host plus k3s **sandbox**.
- Historical PDF `docs/ResilienceOps_Technical_Documentation.pdf` is not the source of truth (`README.md` overview).
