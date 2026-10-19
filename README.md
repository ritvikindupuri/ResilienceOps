# ResilienceOps — Autonomous Cloud Reliability & Self-Healing Platform

> An SRE lab where Red Team agents inject real infrastructure faults into a live microservices stack, Blue Team agents detect and remediate SLO breaches, and Prometheus alerts are diagnosed by an importable **Grok Bot** template that opens GitHub issues — monitored second-by-second on Grafana.

---

## Overview

Modern distributed systems require continuous resilience validation, yet conventional **chaos engineering** is either purely manual or disconnected from automated remediation workflows. **ResilienceOps** closes this loop with a containerized microservices lab, in-cluster agents, and an external AI incident-diagnosis bot.

The platform runs an authentic containerized stack under live traffic. A coordinated **3-Agent Red Team** analyzes the topology and executes kernel-level and network-level faults (cgroup memory leaks, CPU CFS quota exhaustion, network delays, TCP drops). A **3-Agent Blue Team** watches Golden Signals, declares SLO breaches, runs RCA, executes recovery runbooks, and writes post-mortems. In-cluster model IDs are set in [`agents/config.py`](agents/config.py) (defaults: `claude-sonnet-4-6` and `claude-haiku-4-5-20251001`; override with env vars).

In parallel, Prometheus alerting rules fire into Alertmanager. The **incident-bridge** enriches each alert and POSTs it to the importable Grok Bot template **[AI Incident Diagnosis](https://x.ai/bot/feQpDSeSki7HVgkDCBUaY)**. The bot diagnoses likely root cause from the evidence bundle plus recent commits in the watched GitHub repo, then opens an `incident`-labeled GitHub issue (or comments on an existing one). That path is **read-only**: the bot never restarts, scales, rolls back, or pushes code. Self-healing from the bot is a v2 roadmap item.

All telemetry is streamed in **real time (1-second scrape)** to Grafana.

**This README is the current source of truth** for setup, model IDs, alerting, and the Grok Bot. The [technical documentation PDF](docs/ResilienceOps_Technical_Documentation.pdf) is a historical brief — prefer the README when they disagree. For a dated telemetry snapshot, see [RESULTS.md](RESULTS.md).

---

## Key Features

- **Enterprise Infrastructure & Linux Kernel Execution**:
  - Manipulates raw Linux network interfaces (`eth0`) via **Linux Traffic Control (`tc netem`)** to inject genuine packet queuing delays and random frame drops directly in the container kernel network stack.
  - State persistence and distributed caching tier featuring **Redis 7** and **PostgreSQL 16**.
  - Real connection pool starvation faults exhausting Redis `maxclients` limits, creating authentic connection timeouts.
  - Binary chunks are allocated directly in container heap memory to physically trigger the Linux kernel **cgroup OOMKiller (Exit 137)**.
  - CPU starvation executes real mathematical compute loops triggering **CFS quota throttling**.
- **Balanced 3-vs-3 Multi-Agent Architecture** (model IDs from `agents/config.py`):
  - **Red Team (Offensive Testing Squad)**:
    - *Resilience Attack Planner* (`claude-sonnet-4-6`): Decides which system components to test and designs the overall attack plan.
    - *Server Resource Stresser* (`claude-sonnet-4-6`): Tests server limits by filling memory (RAM), exhausting Redis connection pools, and maxing out CPU compute cores.
    - *Network Delay Injector* (`claude-haiku-4-5-20251001`): Tests network resilience by programming Linux kernel `tc netem` rules to delay or drop packets on `eth0`.
  - **Blue Team (Defensive Recovery Squad)**:
    - *Health & Uptime Monitor* (`claude-haiku-4-5-20251001`): Continuously watches website response times and flags whenever services slow down or fail.
    - *Root Cause Investigator* (`claude-sonnet-4-6`): Investigates errors and pinpoints why things broke.
    - *Automated Recovery Fixer & Report Writer* (`claude-sonnet-4-6`): Executes automated recovery runbooks and generates post-incident reports.
- **AI Incident Diagnosis (Grok Bot template)**:
  - Import **[AI Incident Diagnosis](https://x.ai/bot/feQpDSeSki7HVgkDCBUaY)**. Alerts flow services → Prometheus rules → Alertmanager → incident-bridge → Grok Bot webhook → GitHub `incident` issue and (for firing critical alerts) an owner chat ping.
  - The bot is read-only. Duplicate fingerprints comment on the open issue; resolved alerts comment when the alert clears.
- **Dual-Pane Observability Separation (Infrastructure vs. Security)**:
  - **Grafana (Pure Infrastructure Monitoring)**: 100% real-time streaming (1s tick interval, `liveNow: true`, rolling 2-minute window) displaying Google SRE Golden Signals, Availability SLO % (99.9% target), Latency percentiles (p50, p95, p99), Ingress RPS vs 5XX error area charts, Service traffic shares, and live Microservice Memory Usage plotted directly against the 256MB cgroup ceiling. Free of audit clutter and emojis.
  - **AWS CloudWatch (Agent Logs & Fault Telemetry)**: Dedicated observability dashboards (`Agent-Command-Log` and `System-Fault-Metrics`) logging every exact command executed by Red Team and Blue Team agents alongside their exact execution outputs streamed into CloudWatch Logs (`/sre/autonomous-agent-audit`).
- **Kubernetes Agent Sandbox & Security Quarantine**:
  - Agents run inside an isolated `sre-agent-sandbox` namespace constrained by Kubernetes resource limits (`cpu: 500m`, `memory: 512Mi`), audited RBAC roles, and egress NetworkPolicies.
  - Interactive operator shell access via `kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- /bin/bash` with direct cluster connectivity to microservice targets.
- **Enterprise Cost-Optimized Cloud Deployment**:
  - Single-file Terraform architecture (`terraform/main.tf`) deploying to AWS with multi-tier VPC segmentation, segregated security groups, and an EC2 host (`t3.small` / `t4g.small` at ~\$0.02/hr).
  - Eliminates AWS NAT Gateways (\$32/mo) and EKS control plane fees (\$72/mo).
  - 1-command deploy and 1-command clean teardown ensuring zero orphan charges.

---

## System Architecture

<p align="center">
  <img src="docs/images/infraattack_platform_architecture.png" alt="How ResilienceOps + AI Incident Diagnosis works" width="950" />
</p>
<p align="center"><b>Figure 1: How ResilienceOps + AI Incident Diagnosis works</b></p>
<p align="center">The bottom cards are Path B (alert → bridge → bot → GitHub). Red/Blue on k3s is Path A. Compose lab and k3s run on the EC2 host. Grafana only <em>reads</em> Prometheus. order-service owns Redis and <code>orders_db</code>. The figure uses one Red arrow (<em>faults</em>) and one Blue arrow (<em>health / reset</em>); endpoint details (<code>POST /fault/*</code>, <code>tc netem</code>, <code>GET /health</code>, reset) are in the step-by-step below.</p>
<p align="center">Source: <a href="docs/architecture.svg"><code>docs/architecture.svg</code></a> (rebuild + render with <code>scripts/render_architecture.sh</code> / <code>scripts/build_architecture.py</code>). Companion mermaid: <a href="docs/architecture.mmd"><code>docs/architecture.mmd</code></a>.</p>

### Step-by-step flow (matches the code)

Traffic always runs: compose `traffic-generator` POSTs `api-gw:8000` at `RPS_TARGET` (compose default **20**; `traffic-generator/load_generator.py` defaults to **25** only if you run it on the host with no env). `api-gw` reverse-proxies `/api/orders*` to `order-service:8001` and `/api/payments*` to `payment-service:8002`. Order-service writes Redis + PostgreSQL and POSTs `/payments`. Prometheus (`dashboards/prometheus.yml`) scrapes `/metrics` every **1s** from those three jobs and evaluates `dashboards/alerts.yml`. Grafana (`:3000`) is a PromQL dashboard only — it is **not** on the alert path. Prometheus is published as `127.0.0.1:9090` only.

After a fault, **two code paths** run. Path A is `orchestrator.py`. Path B is Prometheus → Alertmanager → incident-bridge → Grok Bot. Stages below are what the code actually does.

1. **Fault injection** (`orchestrator.py` phases 2–3) — `faultStrategistAgent.plan_campaign` then either `InfraDisruptorAgent.execute_fault` (order-service `POST /fault/leak-memory`, `/fault/redis-starvation`, `/fault/cpu-burn`, `/fault/crash`) or `NetworkAdversaryAgent.execute_fault` (payment-service `tc netem` via `/fault/latency` or `/fault/drop-rate`). `--scenario` strings the CLI documents: `MEMORY_EXHAUSTION`, `REDIS_CONNECTION_STARVATION`, `CPU_SATURATION`, `NETWORK_LATENCY`, `PACKET_LOSS`. Dispatch is substring-based: `NETWORK` / `PACKET` / `LATENCY` → network agent; `REDIS` / `CPU` / `CRASH` → infra agent; anything else → memory leak. The catalog records network faults as `KERNEL_TC_NETEM_LATENCY` / `KERNEL_TC_NETEM_PACKET_LOSS` (those names also work as `--scenario` because they contain `LATENCY` / `PACKET`).
2. **Detection** (phase 4, in parallel with Prometheus) — `IncidentMonitor.inspect_telemetry` `GET`s `/health` on api-gw (4s timeout), order-service, and payment-service. If `PROMETHEUS_URL` answers, it also queries p99 of `http_request_duration_seconds` and the 5xx share of `http_requests_total`. `evaluate_slos` declares an incident when p99/probe latency > `SLO_MAX_P99_LATENCY_MS` (1200), error rate > `SLO_MAX_ERROR_RATE_PERCENT` (2), or a service returns HTTP >= 500. The loop is at most **9 ticks of 1s** (`for tick in range(1, 10)`). Prometheus evaluates the same SLO/infra/payment rules in `dashboards/alerts.yml` every 1s independently of the orchestrator.
3. **Alert** — when a rule stays true for its `for:` window, Prometheus sends it to Alertmanager (`127.0.0.1:9093`). Alertmanager groups (`group_wait: 5s`, `group_interval: 15s`, `repeat_interval: 1h`) and POSTs to `http://incident-bridge:8080/webhook` with `send_resolved: true`.
4. **Enrichment** — `incident-bridge` (`services/incident-bridge/app.py`) builds an evidence bundle (PromQL range summaries for `EVIDENCE_WINDOW_SECONDS` default 600, tailed `AGENT_ACTIVITY_LOG`, optional k8s events), caps the payload at `PAYLOAD_MAX_BYTES` (~100KB), and POSTs `{status, alerts, evidence, source: "resilienceops"}` using `GROK_WEBHOOK_*`. Same `fingerprint`+`status` is forwarded at most once per `DEDUPE_TTL_SECONDS` (300). If `GROK_WEBHOOK_URL` is empty, the bridge logs `GROK_WEBHOOK_URL is unset; dropping alert payload` and returns `"dropped_unconfigured"` — the rest of the lab keeps running. The webhook key is never logged.
5. **Diagnosis** — Path A: `DiagnosticAgent.analyze` uses telemetry plus optional k8s events and `EnterpriseLLMEngine` (`MODEL_DIAGNOSTIC_RCA`, default `claude-sonnet-4-6`) to pick a root cause and runbook (e.g. `MEMORY_EXHAUSTION_OOM` → `EVICT_CONTAINER_AND_PURGE_LEAK`). Path B: the imported Grok Bot template **AI Incident Diagnosis** diagnoses from the evidence bundle **plus recent commits** in the watched GitHub repo. The bot is read-only (no restart/scale/rollback/push).
6. **Issue** — the Grok Bot opens a GitHub issue labeled `incident`. If an issue for that fingerprint is already open, it **comments** there instead of opening a duplicate. Firing **critical** alerts also chat-ping the owner (per the ping preference set at import). Path A does not open GitHub issues; it writes `reports/incident_*.md` after remediation.
7. **Resolution** — Path A: `RemediatorAgent.execute_runbook` always calls `FaultCatalog.reset_environment()` (`POST /fault/reset` on order-service and payment-service) and may restart/scale via k8s if the toolkit is available. `verify_recovery` GETs api-gw `/health` up to **5** times; success is HTTP 200 and probe latency **< 800ms**. `PostMortemGenerator.generate` writes `reports/incident_*.md`. StructuredLogger appends `logs/agent_activity.jsonl` and best-effort CloudWatch. Path B: when the PromQL rule clears, Alertmanager sends `status: resolved`. The bridge forwards it (resolved is a different status, so the 5-minute dedupe does not drop it). The bot comments on the GitHub issue. The bot does not reset the fault.

```mermaid
flowchart LR
  services[Microservices] --> prom[Prometheus]
  prom --> rules[Alert rules]
  rules --> am[Alertmanager]
  am --> bridge[incident-bridge]
  bridge --> grok[Grok Bot webhook]
  grok --> gh[GitHub incident issue]
  grok --> chat[Owner chat ping]
```

---

## Kubernetes Agent Sandbox Architecture & Security Quarantine

To ensure completely safe autonomous operations in production, all offensive testing and defensive recovery agents execute inside a dedicated, isolated Kubernetes sandbox container (`sre-agent-sandbox` namespace). Operators trigger resilience campaigns remotely, while the sandbox enforces strict hardware limits, least-privilege API permissions, and granular network filtering.

<p align="center">
  <img src="docs/images/agent_sandbox_architecture.png" alt="Kubernetes Agent Sandbox Architecture & Security Boundary" width="950" />
</p>
<p align="center"><b>Figure 2: Kubernetes Agent Sandbox Pod Architecture, Resource Limits & Egress Network Rules</b></p>

### What Purpose Does the Agent Sandbox Solve?

Deploying autonomous AI agents directly onto host systems creates severe reliability and security risks: runaway script loops could exhaust server compute, faulty remediation logic could disrupt system daemons, and unmonitored network sockets could probe unintended services.

The **Kubernetes Agent Sandbox** provides a zero-blast-radius containment boundary with 3 core security pillars:

| Security Pillar | Concrete Enforcement Mechanism | SRE & Platform Protection Guarantee |
|:---|:---|:---|
| **1. Agent Resource Limits (CPU / RAM)** | Hard cgroup limits enforced per pod: `0.5 CPU (500m)` and `512 MiB RAM`. | If an agent experiences a runaway loop or memory leak, the Linux kernel cgroup OOMKiller immediately terminates the sandbox container (`Exit 137`). **Host node stability and system daemons are 100% protected**. Importantly, sandbox resource constraints cap agent compute—they do not limit or dampen the authentic fault impact injected into target microservices. |
| **2. API Permissions (ServiceAccount + RBAC)** | Scoped Kubernetes ServiceAccount and RoleBinding restricted to target namespaces with minimal verbs (`get`, `list`, `watch`, `pods/exec`). | Agents have **zero cluster-admin privileges**. They cannot inspect `kube-system`, cannot view cluster secrets, and cannot alter cluster or node configurations. |
| **3. Network Rules (Egress Policies)** | Declarative `NetworkPolicy` controlling pod ingress and egress traffic. | Workload selectors enforce secure communication channels: CoreDNS for in-cluster name resolution (`UDP 53`), direct API calls to target microservices (`sre-target-apps`), and outbound HTTPS (`Port 443`) for model APIs and the Grok Bot webhook. |

### How the Sandbox Operates During Incident Cycles

1. **Operator Trigger**: An SRE engineer launches a resilience test cycle remotely via `kubectl exec` into the sandbox pod (`python3 orchestrator.py`).
2. **Sandbox Pod Execution**:
   - **Red Team Agents**: Select and trigger surgical faults against target services (e.g., cgroup memory leaks on `order-service`, Linux kernel `tc netem` latency on `payment-service`).
   - **Blue Team Agents**: Continuously monitor golden signals, check service health, invoke the configured diagnostic model over outbound HTTPS (port 443) for root-cause analysis, and execute automated runbook resets.
3. **Target Services Tier**: The live microservices cluster (`Order`, `Payment`, `API Gateway`) receives the injected faults and resets while keeping underlying host OS and cluster system pods completely isolated.

---

## Tech Stack

| Domain | Technology / Tool | Version | Purpose |
|---|---|---|---|
| **AI Frontier Models** | Anthropic Claude Sonnet 4.6 | `claude-sonnet-4-6` (from `agents/config.py`) | Attack planning, RCA, auto-remediation, post-mortems |
| | Anthropic Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | Incident monitoring and network-adversary actions |
| | Grok Bot template | [AI Incident Diagnosis](https://x.ai/bot/feQpDSeSki7HVgkDCBUaY) | Read-only alert diagnosis, GitHub `incident` issues, critical chat pings |
| **Backend / Services** | Python / FastAPI / Uvicorn | `3.11` / `0.111.0` | High-throughput asynchronous target microservices & API Gateway |
| | HTTPX | `0.27.0` | Asynchronous inter-service HTTP client and proxy router |
| | Pydantic | `2.8.2` | Data validation and JSON schema enforcement |
| **Observability** | Prometheus | `v2.52.0` | 1-second high-resolution metric collection, PromQL engine, and alerting rules |
| | Alertmanager | `v0.27.0` | Groups SLO/infra alerts and posts them to the incident bridge (localhost only) |
| | Incident Bridge | FastAPI | Enriches alerts with Prometheus/log evidence and forwards them to an AI diagnosis webhook |
| | Grafana | `10.4.2` | Pure infrastructure monitoring dashboard (:3000) |
| | AWS CloudWatch | Native AWS | Dedicated security audit dashboard tracking exact agent commands and outputs |
| **Load Testing** | Python Async Worker Engine / k6 | Custom / `0.50+` | Concurrent multi-step consumer workflow traffic generator |
| **Container & Cloud** | Docker & Docker Compose | `v2.24+` | Container runtime, resource isolation, and local orchestration |
| | Certified Kubernetes (`k3s`) | `v1.29+` | Production container orchestration, cgroups, and RBAC sandboxes |
| | Terraform | `v1.7+` | All-in-one Infrastructure-as-Code for AWS cloud deployment |
| | AWS (VPC, EC2, IAM, SSM, CloudWatch) | Provider `~> 5.0` | Multi-tier cloud infrastructure host with zero NAT Gateway overhead |

---

## Installation and quick start

Follow these steps in order: **local lab first** (clone, `.env`, Docker Compose, Grok Bot), then AWS + k3s if you want the cloud host (steps 8–10). After Terraform and the sandbox are up, use [Operating the lab on AWS](#operating-the-lab-on-aws) for Grafana, CloudWatch, `orchestrator.py` cycles, and teardown. Skip that section if you are only running Compose on your laptop.

### 1. Prerequisites

- **Git**, **Python 3.10+**, and **Docker** with Docker Compose v2 (`docker compose version`).
- Commands below use **`python3`**. Ubuntu/Debian typically have no `python` alias; if `python3` is missing, install it (`sudo apt-get install python3 python3-pip`).
- **Anthropic API key** for the in-cluster Red/Blue agents (models listed in `agents/config.py`).
- **Grok Bot** access to import the [AI Incident Diagnosis](https://x.ai/bot/feQpDSeSki7HVgkDCBUaY) template (GitHub must be connected to the bot).
- For AWS: **AWS CLI** (`aws sts get-caller-identity`) and **Terraform 1.5+**.
- Regenerating the architecture PNG: `librsvg2-bin` (`rsvg-convert`) or Google Chrome; then `./scripts/render_architecture.sh`.

### 2. Clone the repository

```bash
git clone https://github.com/ritvikindupuri/ResilienceOps.git
cd ResilienceOps
```

### 3. Create `.env` from `.env.example`

```bash
# On Linux / macOS / Git Bash:
cp .env.example .env

# On Windows PowerShell:
Copy-Item .env.example .env
```

Edit `.env`. There is **no** default Grafana password. **`GRAFANA_ADMIN_USER` and `GRAFANA_ADMIN_PASSWORD` must be non-empty** before any compose command: the compose file uses `${GRAFANA_ADMIN_USER:?Set GRAFANA_ADMIN_USER}` and interpolation fails otherwise. Do not commit `.env` (see [SECURITY.md](SECURITY.md)).

Every `os.getenv` / `_env_int` / `_env_float` name in the Python tree is listed in [`.env.example`](.env.example). Compose interpolates Grafana, Postgres, Grok webhook, bridge tunables, `RPS_TARGET` / `CONCURRENCY`, agent-sandbox `ANTHROPIC_API_KEY`, and SLO thresholds from the same file.

| Variable | Used by | Notes |
|---|---|---|
| `GRAFANA_ADMIN_USER` | compose Grafana | **Required.** Empty → `docker compose config` exits non-zero: `GRAFANA_ADMIN_USER: Set GRAFANA_ADMIN_USER` |
| `GRAFANA_ADMIN_PASSWORD` | compose Grafana | **Required.** No `admin`/`admin` default |
| `ANTHROPIC_API_KEY` | `agents/common/llm_engine.py`, compose `agent-sandbox` | Required for in-cluster Claude calls. Compose uses `${ANTHROPIC_API_KEY:-}` so an empty value still starts the sandbox |
| `POSTGRES_PASSWORD` | compose postgres + order-service | `${POSTGRES_PASSWORD:-sre_password}` |
| `EC2_INSTANCE_ID` | `agents.config.require_ec2_instance_id`, `deploy_remote.py` | Required before remote deploy; no default |
| `SRE_EC2_INSTANCE_ID` | same helper | Alias for `EC2_INSTANCE_ID` |
| `AWS_REGION` | `agents/config.py` | Default `us-east-1` |
| `GROK_WEBHOOK_URL` | incident-bridge | Empty = drop alerts locally (`webhook_configured: false`) |
| `GROK_WEBHOOK_KEY` | incident-bridge | Never logged; copy from the routine in the bot info pane |
| `GROK_WEBHOOK_AUTH_HEADER` | incident-bridge | Default `Authorization`; must match the panel |
| `GROK_WEBHOOK_AUTH_SCHEME` | incident-bridge | Default `Bearer`. Compose uses `${GROK_WEBHOOK_AUTH_SCHEME-Bearer}` so a present-but-empty value sends the raw key |
| `API_GATEWAY_URL` | `agents/config.py` | Host default `http://localhost:8000`. Compose sandbox sets `http://api-gw:8000` |
| `ORDER_SERVICE_URL` | `agents/config.py`, order/payment clients | Host default `http://localhost:8001` |
| `PAYMENT_SERVICE_URL` | `agents/config.py`, api-gw, order-service | Host default `http://localhost:8002` |
| `PROMETHEUS_URL` | `agents/config.py`, incident-bridge | Host default `http://localhost:9090`. Bridge container uses `BRIDGE_PROMETHEUS_URL` |
| `BRIDGE_PROMETHEUS_URL` | compose → bridge `PROMETHEUS_URL` | Default `http://prometheus:9090` (compose DNS) |
| `LOGS_DIR` | `agents/config.py` | Default `logs` |
| `AGENT_ACTIVITY_LOG` | incident-bridge | Compose hardcodes `/app/logs/agent_activity.jsonl` (the `./logs` volume). Host default in `.env.example` is `logs/agent_activity.jsonl` |
| `EVIDENCE_WINDOW_SECONDS` | incident-bridge | Default `600` |
| `PAYLOAD_MAX_BYTES` | incident-bridge | Default `102400` |
| `DEDUPE_TTL_SECONDS` | incident-bridge | Default `300` |
| `WEBHOOK_TIMEOUT_SECONDS` | incident-bridge | Default `10` |
| `WEBHOOK_MAX_RETRIES` | incident-bridge | Default `3` |
| `LOG_TAIL_LINES` | incident-bridge | Default `40` |
| `K8S_EVIDENCE_ENABLED` | incident-bridge | Default `true`; `0`/`false`/`no` disables |
| `SLO_MAX_P99_LATENCY_MS` | `agents/config.py`, compose `agent-sandbox` | Default `1200.0` (must match `dashboards/alerts.yml` `> 1.2`) |
| `SLO_MAX_ERROR_RATE_PERCENT` | `agents/config.py`, compose `agent-sandbox` | Default `2.0` |
| `MODEL_fault_STRATEGIST` | `agents/config.py` | Default `claude-sonnet-4-6` (name is spelled this way in code) |
| `MODEL_INFRA_DISRUPTOR` | `agents/config.py` | Default `claude-sonnet-4-6` |
| `MODEL_NETWORK_ADVERSARY` | `agents/config.py` | Default `claude-haiku-4-5-20251001` |
| `MODEL_INCIDENT_MONITOR` | `agents/config.py` | Default `claude-haiku-4-5-20251001` |
| `MODEL_DIAGNOSTIC_RCA` | `agents/config.py` | Default `claude-sonnet-4-6` |
| `MODEL_AUTO_REMEDIATOR` | `agents/config.py` | Default `claude-sonnet-4-6` |
| `MODEL_POST_MORTEM` | `agents/config.py` | Default `claude-sonnet-4-6` |
| `DEFAULT_MODEL` | `agents/config.py` | Default = `MODEL_DIAGNOSTIC_RCA` |
| `AI_PROVIDER` | `agents/config.py` | Default `anthropic` |
| `GEMINI_API_KEY` | `agents/config.py` | Unused by default; kept so `arena_runner` imports |
| `OPENAI_API_KEY` | `agents/config.py` | Unused by default; kept so `arena_runner` imports |
| `CW_LOG_GROUP_ATTACKER` | `agents/config.py` | Default `/sre/autonomous-agent-audit` |
| `CW_LOG_GROUP_DEFENDER` | `agents/config.py` | Default `/sre/autonomous-agent-audit` |
| `CW_LOG_GROUP_INCIDENTS` | `agents/config.py` | Default `/sre/autonomous-agent-incidents` |
| `GATEWAY_URL` | `traffic-generator/load_generator.py`; fallback in `structured_logger.py` | Compose hardcodes `http://api-gw:8000` inside the generator container |
| `RPS_TARGET` | traffic-generator | Compose default **20**. Module default is **25** if unset |
| `CONCURRENCY` | traffic-generator | Compose default **8**. Module default is **10** if unset |
| `REDIS_HOST` / `REDIS_PORT` | order-service | Compose sets `redis` / `6379` |
| `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_USER` / `POSTGRES_DB` | order-service | Compose sets `postgres` / `5432` / `sre_user` / `orders_db` |

Terraform ingress is **not** an env var. Copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars` and set `allowed_cidr` to your `/32` or office CIDR. `0.0.0.0/0` is rejected.

`orchestrator.py` loads `.env` via `python-dotenv` in `agents/common/llm_engine.py` (`load_dotenv()` does not override variables already in the process environment). Compose interpolates `.env` itself.

### 4. Install Python dependencies

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -r services/incident-bridge/requirements.txt
```

`requirements.txt` covers host-side agents, pytest, and `scripts/send_test_alert.py` (`httpx`). The bridge file adds FastAPI/Uvicorn if you run the bridge without Compose.

### 5. Import the Grok Bot template and copy webhook credentials

1. Import **[AI Incident Diagnosis](https://x.ai/bot/feQpDSeSki7HVgkDCBUaY)**.
2. The bot's first conversation asks for the **GitHub repo** to file incidents in (GitHub must already be connected), the **alert source**, and the **ping preference**.
3. Open the bot's chat. Click the bot's name in the chat header (or press **Cmd+Shift+I**) to open its info pane.
4. Under **Routines**, open **ResilienceOps incident diagnosis** (or whatever routine the template created).
5. Copy **Webhook URL** into `GROK_WEBHOOK_URL` and **Webhook key** into `GROK_WEBHOOK_KEY`. Check the **Authorization** header setting — that maps to `GROK_WEBHOOK_AUTH_HEADER` / `GROK_WEBHOOK_AUTH_SCHEME` (scheme may be empty).

<!-- screenshot: bot chat header → info pane → Routines → ResilienceOps incident diagnosis (Webhook URL, Webhook key, Authorization) -->

Details: [AI incident diagnosis](#ai-incident-diagnosis).

### 6. Start the local Docker Compose lab

Grafana, Alertmanager, and the incident-bridge are part of this stack. Alertmanager (`127.0.0.1:9093`) and the bridge (`127.0.0.1:8088`) are localhost-only.

Validate interpolation (this **fails** if Grafana admin vars are still empty):

```bash
docker compose config >/dev/null
```

Expected: no output, exit 0. If you skipped Grafana vars, Compose exits non-zero and prints:

```text
error while interpolating services.grafana.environment.[]: required variable GRAFANA_ADMIN_USER is missing a value: Set GRAFANA_ADMIN_USER
```

```bash
docker compose up --build -d
```

Wait until `docker compose ps` shows `incident-bridge` as running (first build compiles the FastAPI images plus Redis, Postgres, Prometheus, Alertmanager, Grafana, and traffic-generator). A warning `Docker Compose is configured to build using Bake, but buildx isn't installed` is harmless — Compose falls back to the classic builder.

On AWS after install steps 8–10, Grafana and sandbox cycles are in [Operating the lab on AWS](#operating-the-lab-on-aws).

`agent-sandbox` is **opt-in**. Its image `CMD` is `python orchestrator.py --cycles 5 --delay 10`, which injects real faults. It does **not** start on a plain `docker compose up`. To include it (needs `ANTHROPIC_API_KEY`):

```bash
docker compose --profile agents up -d --build agent-sandbox
```

Then:

```bash
curl -sS http://127.0.0.1:8088/healthz
```

Expected JSON when `GROK_WEBHOOK_URL` is still empty:

```json
{"status":"ok","webhook_configured":false}
```

After you set `GROK_WEBHOOK_URL`, recreate the bridge (`docker compose up -d incident-bridge`) and expect `"webhook_configured":true`.

Optional local agent cycle on the host (needs `ANTHROPIC_API_KEY` in `.env`; `llm_engine.py` calls `load_dotenv()`), instead of the compose profile:

```bash
python3 orchestrator.py --cycles 1 --scenario MEMORY_EXHAUSTION
```

### 7. Fire a synthetic alert and confirm a GitHub issue

```bash
python3 scripts/send_test_alert.py --target alertmanager
```

Expected from Alertmanager: HTTP 200 with an empty body. The script prints:

```text
200
```

That only means Alertmanager **accepted** the alert. Confirm the bridge received it:

```bash
docker compose logs --tail 20 incident-bridge
```

- If `GROK_WEBHOOK_URL` is empty you will see `GROK_WEBHOOK_URL is unset; dropping alert payload`.
- If the URL is set you will see `forwarded N alert(s) status=firing source=resilienceops`, then a GitHub `incident` issue in the repo you configured with the bot (or a comment on an existing fingerprint).
- If Alertmanager logs `Notify for alerts failed ... context deadline exceeded`, container-to-container traffic on the compose network is blocked. That is an environment/firewall issue, not a missing config file. Use `--target bridge` (host `127.0.0.1:8088`) to prove the bridge itself.

If the stack is not running, the script prints `request failed: ConnectError` (or `ConnectTimeout`) on stderr and exits 1. Use `--target bridge` to POST `http://127.0.0.1:8088/webhook` directly; expected:

```text
200 {"accepted":true}
```

Equivalent curl:

```bash
curl -sS -H 'Content-Type: application/json' \
  -d '[{"labels":{"alertname":"SyntheticTestAlert","severity":"warning","service":"api-gw"},"annotations":{"summary":"Synthetic test alert"},"startsAt":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"}]' \
  http://127.0.0.1:9093/api/v2/alerts
```

Stop the lab with `docker compose down -v`.

### 8. Deploy AWS infrastructure (Terraform)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # set allowed_cidr to YOUR /32 or office CIDR
terraform init
terraform apply
```

Grafana (`3000`) and the API gateway (`8000`) are limited to `allowed_cidr`. Prometheus (`9090`) and SSH (`22`) are **not** opened — use AWS Systems Manager for host access and SSM port forwarding for Prometheus (`127.0.0.1:9090`).

Typical outputs:

```text
api_gateway_url = "http://54.xxx.xxx.xxx:8000"
grafana_url     = "http://54.xxx.xxx.xxx:3000"
prometheus_url  = "http://127.0.0.1:9090 (host-local; AWS SSM port forwarding)"
public_ip       = "54.xxx.xxx.xxx"
```

Save `public_ip` / `grafana_url`. Put the instance id in `.env` as `EC2_INSTANCE_ID`.

<p align="center">
  <img src="docs/images/aws_vpc_resource_map.png" alt="AWS Enterprise VPC Resource Map" width="950" />
</p>
<p align="center"><b>Figure 3: Live AWS Enterprise VPC Resource Map (3-Tier Subnet Segmentation & Ingress Routing)</b></p>

### 9. Push the app to the host (`deploy_remote.py`)

`deploy_remote.py` builds a payload zip from the current tree (compose services, dashboards, agents, incident-bridge) **without** `.env`, then sends it with AWS SSM.

```bash
export EC2_INSTANCE_ID=i-xxxxxxxxxxxxxxxxx
export AWS_REGION=us-east-1
# On the host, set ANTHROPIC_API_KEY, GRAFANA_ADMIN_*, POSTGRES_PASSWORD,
# and GROK_WEBHOOK_* via SSM Parameter Store, Secrets Manager, or instance env.
python3 deploy_remote.py
```

### 10. k3s agent sandbox

Red and Blue agents run in `sre-agent-sandbox` on the AWS host (`500m` CPU, `512Mi` RAM, egress NetworkPolicy).

Connect with SSM (no SSH / port 22):

```bash
aws ssm start-session --target "$EC2_INSTANCE_ID"
```

Or: AWS Systems Manager → Fleet Manager → instance `sre-enterprise-platform-host` → Start terminal session.

On the host:

```bash
k3s kubectl get pods,roles,rolebindings,networkpolicies -n sre-agent-sandbox
k3s kubectl logs -f deployment/red-team-sandbox -n sre-agent-sandbox
k3s kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- /bin/bash
```

Example cycle:

```bash
k3s kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- \
  python3 orchestrator.py --target-ip api-gw.sre-target-apps.svc.cluster.local --cycles 1 --scenario MEMORY_EXHAUSTION
```

---


## Operating the lab on AWS

Do [Installation and quick start](#installation-and-quick-start) first. Local Compose (including Alertmanager, incident-bridge, and Grafana on `:3000`) is steps 3–7 of that section. This walkthrough assumes the AWS host and `sre-agent-sandbox` are already deployed and you want to watch Grafana, CloudWatch, and in-cluster cycles.

> [!TIP]
> **Dashboard screenshots**:  
> For high-resolution Grafana/CloudWatch captures and a **dated** telemetry snapshot, see [**RESULTS.md**](RESULTS.md). Some reports quoted there still use the pre-fix `UNKNOWN_FAULT` title; the current generator is [`reports/example_incident_memory_exhaustion.md`](reports/example_incident_memory_exhaustion.md).

### Step 1: Open the Live AWS Grafana Dashboard (Pure Infra Monitoring)
1. Open your web browser and navigate to your AWS Grafana URL:
   ```text
   http://<YOUR_AWS_PUBLIC_IP>:3000
   ```
2. Sign in with the Grafana admin user and password you set in `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD`. There is no default `admin`/`admin` password.
3. In the left navigation menu, click **Dashboards** -> **SRE & Reliability** -> click **SRE Infrastructure & Reliability Performance Monitor**.
4. Observe the 8 focused operational panels streaming every **1 second**:
   - **Real-Time Availability SLO %**: High-precision gauge (Target: 99.9%).
   - **Live Request Throughput (RPS)**: Real-time traffic volume (~20-80 RPS).
   - **Live HTTP 5XX Error Rate %**: Tracks server degradation with color-coded thresholds.
   - **Real-Time System State**: Clean high-contrast indicator (`HEALTHY` or `ACTIVE INCIDENT`).
   - **Real-Time Latency Profiles (p50, p95, p99)**: Live latency curves.
   - **Live Ingress RPS vs 5XX Server Errors**: Direct visual correlation between traffic peaks and errors.
   - **Microservice Memory Usage vs Cgroup Ceiling (MB)**: Full-width telemetry showing live resident memory against the 256MB cgroup hard ceiling.
   - **Service Traffic Ingress Share**: Real-time traffic distribution across microservices.

*(See [RESULTS.md#1-live-infrastructure--reliability-performance-monitoring](RESULTS.md#1-live-infrastructure--reliability-performance-monitoring) for the full-resolution screenshot and panel-by-panel metric breakdown).*

---

### Step 2: Open the AWS CloudWatch Dashboards
To inspect the exact security actions, injected attack vectors, and raw command outputs:
1. Open the **AWS Console** in your browser and switch to `us-east-1`.
2. Navigate to **CloudWatch** -> **Dashboards**.
3. You will find two clear, dedicated CloudWatch dashboards:
   - **`Agent-Command-Log`**: Real-time audit log stream capturing exact commands executed by Red Team and Blue Team agents alongside raw terminal outputs from `/sre/autonomous-agent-audit`:
     - *Header*: `# Agent Command Log` (Live audit trail of test commands and recovery fixes).
     - *Left Table*: **Red Team: Injected Commands & Outputs** (Tracks exact kernel `tc netem`, Redis starvation, and memory allocation commands).
     - *Right Table*: **Blue Team: Remediation Commands & Outputs** (Tracks exact runbook actions and recovery statuses).
     - *Bottom Table*: **Unified Agent Command & Security Audit Stream** (Full chronologically sorted audit ledger).
   - **`System-Fault-Metrics`**: Dedicated visual telemetry dashboard tracking active and resolved resilience attack vectors:
     - *Header*: `# System Faults & Recovery` (Visual tracking of active attack vectors and remediation velocity).
     - *Graph 1*: **Fault Injections by Vector** (Time-series line charts tracking kernel `tc netem` latency, Redis starvation, and memory leaks).
     - *Graph 2*: **Incident Rate vs Remediation Recovery Velocity** (Direct time-series comparison between active SEV-1 incidents and resolved remediations).
     - *Graph 3*: **Attack Vector Distribution Share** (Interactive pie chart showing the percentage breakdown across all tested fault vectors).
     - *Audit Table*: **Active vs Resolved Fault Lifecycle Audit** (Live status log showing faults transitioning from `FAULT_ACTIVE` to `RESOLVED`).

*(See [RESULTS.md#2-autonomous-agent-security-audit-stream](RESULTS.md#2-autonomous-agent-security-audit-stream) and [RESULTS.md#3-system-faults--remediation-recovery-velocity](RESULTS.md#3-system-faults--remediation-recovery-velocity) for high-resolution captures and telemetry analysis).*

---

### Step 3: Launch the Resilience Agents Inside the Quarantined Kubernetes Sandbox

All Red Team and Blue Team agents execute inside the hardened **Kubernetes Agent Sandbox Pod** (`sre-agent-sandbox` namespace) on AWS. This enforces strict cgroup resource isolation (`500m` CPU, `512Mi` RAM) and least-privilege RBAC controls:

#### 1. Execute the Resilience Cycle Inside the Sandbox Pod:
Run the orchestrator directly inside the quarantined Kubernetes pod over AWS Systems Manager or terminal:

```bash
k3s kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- \
  python3 orchestrator.py --target-ip api-gw.sre-target-apps.svc.cluster.local --cycles 1 --scenario MEMORY_EXHAUSTION
```

#### What you will observe in the terminal (illustrative; timings are not guaranteed):

Printed MTTD/MTTR vary with load, scrape lag, and whether Prometheus is reachable. They are measured per cycle, not fixed.

- **Phase 1**: **Health & Uptime Monitor** probes `GET /health` on api-gw, order-service, and payment-service. A healthy baseline is usually HTTP 200 with probe latency well under the 1200ms SLO.
- **Phase 2**: Red Team **Resilience Attack Planner** (`claude-sonnet-4-6`) evaluates topology and formulates a campaign.
- **Phase 3**: Red Team **Server Resource Stresser** POSTs `order-service /fault/leak-memory` (this `--scenario MEMORY_EXHAUSTION` path).
- **Phase 4**: Blue Team **Health & Uptime Monitor** loops up to 9 ticks of 1s. It declares an incident when p99/probe latency > 1200ms, error rate > 2%, or a probe returns HTTP >= 500 (`INCIDENT DECLARED | MTTD: …` — MTTD is that loop duration).
- **Phase 5**: Blue Team **Root Cause Investigator** (`MODEL_DIAGNOSTIC_RCA`, default `claude-sonnet-4-6`) plus rule-based heuristics. `MEMORY_EXHAUSTION_OOM` is used when order-service is 5xx **and** recent k8s events mention oom; otherwise you may see `ORDER_PROCESS_FAILURE` or another cause. The OOM runbook is `EVICT_CONTAINER_AND_PURGE_LEAK`.
- **Phase 6**: Blue Team **Automated Recovery Fixer** (`RemediatorAgent.execute_runbook`) **always** calls `FaultCatalog.reset_environment()` — `POST /fault/reset` on order-service and payment-service. It restarts `order-service` (or scales it to 3 replicas on CPU runbooks) **only if** `K8sToolKit.k8s_available`. It does not unconditionally bounce the container. `verify_recovery` GETs api-gw `/health` up to 5 times; success is HTTP 200 and probe latency < 800ms. Printed MTTR is measured there.
- **Phase 7**: Blue Team **Incident Report Writer** writes `reports/incident_*.md` (title from `resolve_fault_title()`, e.g. `MEMORY_EXHAUSTION`).

---

### Step 4: Watch the Live AWS Grafana Dashboard React in Real Time
Keep the AWS Grafana dashboard open while running the cycle. The following times are **typical of a fast memory-leak lab run**, not a promise:
1. Shortly after injection, the **Real-Time System State** gauge often flips from `HEALTHY` to `ACTIVE INCIDENT`.
2. **Latency Profiles** may spike (sometimes above 2000ms) while the leak or reset is in flight.
3. **5XX Error Rate** can climb if upstream timeouts accumulate.
4. After `POST /fault/reset` (and a k8s restart **if** the toolkit is available), latency usually returns toward baseline and the gauge turns green. How many seconds that takes depends on the fault and whether k8s restart ran.

---

### Step 5: Test Additional Enterprise Failure Scenarios

Target different failure mechanisms on your AWS cluster using the `--scenario` argument directly through the sandbox pod:

```bash
# Test Linux Kernel tc netem Packet Latency on eth0 (Inside Sandbox Pod).
# CLI name NETWORK_LATENCY; catalog records KERNEL_TC_NETEM_LATENCY.
k3s kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- \
  python3 orchestrator.py --target-ip api-gw.sre-target-apps.svc.cluster.local --cycles 1 --scenario NETWORK_LATENCY

# Test Linux Kernel tc netem Packet Loss (35% frame drops on eth0).
# CLI name PACKET_LOSS; catalog records KERNEL_TC_NETEM_PACKET_LOSS.
k3s kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- \
  python3 orchestrator.py --target-ip api-gw.sre-target-apps.svc.cluster.local --cycles 1 --scenario PACKET_LOSS

# Test Redis Connection Pool Starvation (saturating maxclients limit):
k3s kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- \
  python3 orchestrator.py --target-ip api-gw.sre-target-apps.svc.cluster.local --cycles 1 --scenario REDIS_CONNECTION_STARVATION

# Test CPU CFS Quota Saturation & Thread Starvation:
k3s kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- \
  python3 orchestrator.py --target-ip api-gw.sre-target-apps.svc.cluster.local --cycles 1 --scenario CPU_SATURATION

# Run multiple back-to-back resilience rounds:
k3s kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- \
  python3 orchestrator.py --target-ip api-gw.sre-target-apps.svc.cluster.local --cycles 3 --delay 5
```

---

### Step 6: Review Generated Remediation & Post-Mortem Reports

Every time an autonomous resilience cycle runs, the Blue Team's **Incident Report Writer** generates a standardized markdown SRE post-mortem report and archives it directly into the `reports/` folder.

#### How to Locate and View Reports:

1. **Locally in Your Repository**:
   All generated reports are stored in the [`reports/`](reports/) directory.
   ```bash
   # On Linux / macOS:
   cat reports/incident_*.md

   # On Windows PowerShell:
   Get-ChildItem reports\*.md | Get-Content
   ```

2. **Live on AWS CloudWatch**:
   Open **CloudWatch** -> **Dashboards** -> **`Agent-Command-Log`**. The middle table (*"Blue Team SRE Agents: Exact Remediation Commands & Outputs"*) streams the exact `GENERATE_POST_MORTEM` commands, MTTR calculation metrics, and report storage confirmations in real time.

#### Example post-mortem (current generator)

The file below is **not a live incident**. It was produced by `python3 scripts/generate_example_post_mortem.py`, which calls `PostMortemGenerator` with representative `MEMORY_EXHAUSTION` inputs (title via `resolve_fault_title()`, fixed in PR #1). MTTD/MTTR in it are example values.

**[View example: `reports/example_incident_memory_exhaustion.md`](reports/example_incident_memory_exhaustion.md)**

```markdown
# Incident Post-Mortem Report: MEMORY_EXHAUSTION
**Incident Timestamp**: 2026-10-18 23:17:46 UTC
**Classification**: Production Incident (`SEV-1`)
**Impacted Service**: `order-service`
**Incident State**: `RESOLVED`

## 1. Executive Summary
... identified `MEMORY_EXHAUSTION_OOM` with **98.0% confidence** and triggered
remediation runbook `EVICT_CONTAINER_AND_PURGE_LEAK` ...

### Key Metrics
- Mean Time To Detect (MTTD): `3.81 seconds` (example)
- Mean Time To Remediate (MTTR): `5.26 seconds` (example)
```

Files named `reports/incident_*_unknown_fault.md` are **pre-fix historical samples** from before PR #1. Do not treat `UNKNOWN_FAULT` as current output.

---

### Step 7: Clean Teardown (Zero Lingering Cost)

When you are finished testing, cleanly destroy all AWS cloud resources to guarantee zero ongoing charges.

You can use the automated root teardown scripts:

```bash
# On Linux / macOS:
./teardown.sh

# On Windows PowerShell:
.\teardown.ps1
```

Or execute directly with Terraform:

```bash
cd terraform
terraform destroy -auto-approve
```

*This cleanly purges 100% of the AWS VPC, subnets, route tables, security groups, IAM roles, and EC2 host in under 60 seconds, guaranteeing zero ongoing charges.*

---

Back to the local lab: Docker Compose (including Alertmanager and incident-bridge) is [Installation step 6](#6-start-the-local-docker-compose-lab).

---

## AI incident diagnosis

Incident diagnosis for Prometheus alerts is delivered by the importable Grok Bot template **[AI Incident Diagnosis](https://x.ai/bot/feQpDSeSki7HVgkDCBUaY)**. ResilienceOps does not embed the bot; you import the template, point the incident-bridge at its webhook, and the bot files GitHub issues.

### What the bot does

- Receives enriched alerts at its webhook (`source: resilienceops`).
- Diagnoses likely root cause from the evidence bundle (Prometheus metric summaries, recent `logs/agent_activity.jsonl` lines, optional Kubernetes events) **plus recent commits** in the watched GitHub repo.
- Opens a GitHub issue labeled `incident`. If an issue for the **same fingerprint** is already open, it **comments on that issue** instead of opening a duplicate.
- When the alert **resolves**, it comments on the issue (`send_resolved: true` on Alertmanager).
- Messages the owner in chat for **firing critical** alerts (per the ping preference set at import).
- Is **read-only**: it never restarts, scales, rolls back, or pushes code.

**Roadmap (v2):** bot-driven self-healing. Not in this template.

### Alert flow

```mermaid
flowchart LR
  services[Microservices] --> prom[Prometheus]
  prom --> rules[Alert rules]
  rules --> am[Alertmanager]
  am --> bridge[incident-bridge]
  bridge --> grok[Grok Bot webhook]
  grok --> gh[GitHub incident issue]
  grok --> chat[Owner chat ping]
```

1. **Prometheus** (`dashboards/prometheus.yml`) scrapes api-gw, order-service, and payment-service every 1s and evaluates `dashboards/alerts.yml`.
2. Firing rules go to **Alertmanager** (`dashboards/alertmanager.yml`, `127.0.0.1:9093` only): `group_wait: 5s`, `group_interval: 15s`, `repeat_interval: 1h`, `send_resolved: true`.
3. Alertmanager POSTs to **incident-bridge** (`127.0.0.1:8088/webhook`). The bridge attaches a compact evidence bundle (last ~10 minutes of PromQL snapshots as min/max/avg/last — not raw series), then POSTs:

```json
{
  "status": "firing",
  "alerts": [{"labels": {}, "annotations": {}, "fingerprint": "", "startsAt": "", "endsAt": ""}],
  "evidence": {},
  "source": "resilienceops"
}
```

4. The Grok Bot diagnoses and opens or comments on a GitHub `incident` issue.
5. If `GROK_WEBHOOK_URL` is unset, the bridge logs that the webhook is unconfigured and **drops** the payload. The rest of the lab keeps running.

The webhook key is never logged. Evidence is secret-stripped. Payloads are capped at ~100KB.

### Setup (match the bot panel)

1. Import the template: https://x.ai/bot/feQpDSeSki7HVgkDCBUaY
2. Complete the first conversation: GitHub repo (GitHub connected), alert source, ping preference.
3. Copy webhook credentials from the routine as in [install step 5](#5-import-the-grok-bot-template-and-copy-webhook-credentials) (info pane → **Routines** → **ResilienceOps incident diagnosis**).
4. Put them in `.env`:

| Variable | Default | Purpose |
|---|---|---|
| `GROK_WEBHOOK_URL` | empty (drop) | Bot webhook URL from the routine in the bot info pane |
| `GROK_WEBHOOK_KEY` | empty | Webhook key; never committed or logged |
| `GROK_WEBHOOK_AUTH_HEADER` | `Authorization` | Header **name** from the panel |
| `GROK_WEBHOOK_AUTH_SCHEME` | `Bearer` | Scheme prefix. Empty string sends the raw key as the header value |

5. Start (or recreate) the stack **including alertmanager + incident-bridge**, then test:

```bash
docker compose up -d
python3 scripts/send_test_alert.py --target alertmanager
```

Confirm an `incident` issue appears in the configured repo. To hit the bridge only: `python3 scripts/send_test_alert.py --target bridge`.

Restart compose after changing `.env`:

```bash
docker compose up -d --build incident-bridge alertmanager prometheus
```

---

## Troubleshooting

### No GitHub issue after an alert

1. `curl -sS http://127.0.0.1:8088/healthz` — `webhook_configured` should be `true`.
2. Bridge logs: `docker compose logs incident-bridge`. If URL is unset you will see a drop message. The key is never printed.
3. Confirm `GROK_WEBHOOK_URL` and `GROK_WEBHOOK_KEY` match the routine (no trailing whitespace). See [install step 5](#5-import-the-grok-bot-template-and-copy-webhook-credentials).
4. Confirm `GROK_WEBHOOK_AUTH_HEADER` and `GROK_WEBHOOK_AUTH_SCHEME` match the routine's Authorization setting. See [Webhook 401 / 403](#webhook-401--403).
5. Confirm **GitHub is connected** in the Grok Bot and the first-run conversation named the repo that should receive issues.
6. Confirm Alertmanager is up (`curl -sS http://127.0.0.1:9093/-/healthy`) and the synthetic alert returned HTTP 200.

### Webhook 401 / 403

The bot rejected the request. The usual cause is a wrong `GROK_WEBHOOK_KEY`, or `GROK_WEBHOOK_AUTH_HEADER` / `GROK_WEBHOOK_AUTH_SCHEME` that does not match the **Authorization** setting on the routine. Re-open **ResilienceOps incident diagnosis** (install step 5), copy URL, key, and header/scheme again, then recreate the bridge: `docker compose up -d incident-bridge`.

### Duplicate issues vs comments

The bot comments on an **already-open** issue for the same alert fingerprint instead of opening another. If you expected a new issue, close or check the existing `incident` issue.

### 5-minute dedupe (bridge)

The incident-bridge forwards the same `fingerprint` + `status` at most **once per 5 minutes**. Flapping firing alerts in that window are dropped at the bridge (resolved is a different status, so a resolve can still go through). Alertmanager `repeat_interval` is 1h.

### Compose will not start Grafana

`GRAFANA_ADMIN_USER` and `GRAFANA_ADMIN_PASSWORD` must be set. There is no default password.

### `docker compose config` fails immediately

If Grafana vars are still empty, Compose prints:

```text
error while interpolating services.grafana.environment.[]: required variable GRAFANA_ADMIN_USER is missing a value: Set GRAFANA_ADMIN_USER
```

and exits non-zero. Fill those two values in `.env` and re-run `docker compose config >/dev/null`.

### Alertmanager 200 but the bridge never logs the webhook

`python3 scripts/send_test_alert.py --target alertmanager` talks to `127.0.0.1:9093`. Alertmanager then POSTs to `http://incident-bridge:8080/webhook` **on the compose network**. Host binds (`curl 127.0.0.1:8088/healthz`, `--target bridge`) can succeed even when container-to-container TCP is blocked.

Check:

```bash
docker compose logs alertmanager | tail
docker exec "$(docker compose ps -q alertmanager)" wget -T 3 -qO- http://incident-bridge:8080/healthz
```

If that wget times out, Docker bridge forwarding is broken on the host (nested VMs sometimes do this). The lab still answers on localhost ports; Prometheus scrapes (`api-gw:8000`, etc.) will also fail until the engine can route between containers. On Docker Desktop or a normal Linux Engine install this path works without extra flags.

### Bake / buildx warning

`Docker Compose is configured to build using Bake, but buildx isn't installed` is a Compose v2 message. The stack still builds with the default docker driver.

---

## Detailed Technical Documentation

**This README is the current source of truth.** For a historical architecture brief (SLO notes, sandbox diagrams, AWS topology), see:

**[Technical Documentation (PDF)](docs/ResilienceOps_Technical_Documentation.pdf)**

Prefer this README — and `agents/config.py` for model IDs — when the PDF disagrees. See also [docs/README.md](docs/README.md).
