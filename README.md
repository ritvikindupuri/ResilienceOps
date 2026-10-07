# ResilienceOps — Autonomous Cloud Reliability & Self-Healing Platform

> An enterprise-grade autonomous Site Reliability Engineering (SRE) platform where coordinated Offensive Testing Agents safely inject real infrastructure faults into a live microservices cluster, while defensive SRE Agents autonomously detect, diagnose using Claude 3.7 Extended Thinking, and remediate incidents in real time—monitored second-by-second on a live streaming Grafana dashboard.

---

## Overview

Modern distributed systems require continuous resilience validation, yet conventional **chaos engineering** is either purely manual or disconnected from automated remediation workflows. **ResilienceOps** closes this loop with an autonomous, production-grade multi-agent architecture.

The platform runs an authentic containerized microservices stack under live, concurrent automated user traffic. A coordinated **3-Agent Red Team** analyzes the topology and executes kernel-level and network-level faults (Linux cgroup memory leaks, CPU CFS quota exhaustion, network transit delays, and TCP packet drops). Simultaneously, a **3-Agent Blue Team** continuously watches the SRE Golden Signals, declares incidents upon Service Level Objective (SLO) breaches, executes deep root-cause analysis (RCA) via **Claude 3.7 Sonnet with Extended Thinking**, triggers automated recovery runbooks, and authors standardized post-mortem reports.

All telemetry is streamed in **100% real-time (1-second tick interval)** to an auto-provisioned Grafana dashboard.
 
📊 **For deep performance metrics, high-resolution dashboard breakdowns, and an authentic SRE post-mortem, view the [SRE Results & Incident Telemetry Report (RESULTS.md)](RESULTS.md).**  
📖 **For technical specifications, math models, and agent communication protocols, read the [Technical Documentation (PDF)](docs/ResilienceOps_Technical_Documentation.pdf).**

---

## Key Features

- **Enterprise Infrastructure & Linux Kernel Execution**:
  - Manipulates raw Linux network interfaces (`eth0`) via **Linux Traffic Control (`tc netem`)** to inject genuine packet queuing delays and random frame drops directly in the container kernel network stack.
  - State persistence and distributed caching tier featuring **Redis 7** and **PostgreSQL 16**.
  - Real connection pool starvation faults exhausting Redis `maxclients` limits, creating authentic connection timeouts.
  - Binary chunks are allocated directly in container heap memory to physically trigger the Linux kernel **cgroup OOMKiller (Exit 137)**.
  - CPU starvation executes real mathematical compute loops triggering **CFS quota throttling**.
- **Balanced 3-vs-3 Multi-Agent Architecture**:
  - **Red Team (Offensive Testing Squad)**:
    - *Resilience Attack Planner* (`Claude Sonnet`): Decides which system components to test and designs the overall attack plan.
    - *Server Resource Stresser* (`Claude Sonnet`): Tests server limits by filling memory (RAM), exhausting Redis connection pools, and maxing out CPU compute cores.
    - *Network Delay Injector* (`Claude Haiku`): Tests network resilience by programming Linux kernel `tc netem` rules to delay or drop packets on `eth0`.
  - **Blue Team (Defensive Recovery Squad)**:
    - *Health & Uptime Monitor* (`Claude Haiku`): Continuously watches website response times and flags whenever services slow down or fail.
    - *Root Cause Investigator* (`Claude Sonnet with Extended Thinking`): Uses deep step-by-step thinking to investigate errors and pinpoint why things broke.
    - *Automated Recovery Fixer & Report Writer* (`Claude Sonnet`): Executes automated recovery fixes (clearing jammed memory, restarting broken containers) and generates executive post-incident reports.
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
  <img src="docs/images/infraattack_platform_architecture.png" alt="Autonomous SRE Resilience Platform Architecture" width="950" />
</p>
<p align="center"><b>Figure 1: End-to-End System & Runtime Architecture</b></p>

### Architecture Execution Lifecycle

The platform executes a closed-loop resilience lifecycle from user traffic ingress down to kernel manipulation, sub-second telemetry, LLM reasoning, automated recovery, and CloudWatch logging:

1. **Step 1 — Client Traffic Generation & Ingress Routing**:
   The **Traffic Generator** simulates realistic production traffic (20 RPS) consisting of asynchronous multi-step consumer journeys (catalog search, cart creation, checkout submission, payment settlement). Requests enter through the **AWS Internet Gateway** and hit the **API Gateway** (`:8000`), which manages reverse-proxy routing, timeout thresholds, and request rate-limiting.

2. **Step 2 — Microservice Request Propagation & Stateful Processing**:
   The API Gateway forwards business requests downstream to the **Order Service** (`:8001`) and **Payment Service** (`:8002`):
   - The **Order Service** queries and updates session state in **Redis 7** (in-memory caching & client connection pool) and commits order records to **PostgreSQL 16**.
   - The **Payment Service** executes payment authorizations and async credit card validations across network sockets.

3. **Step 3 — High-Resolution Telemetry Scraping (1-Second Polling Engine)**:
   All microservices continuously expose RED golden signals (Rate, Errors, Duration) and process memory allocations via `/metrics`. **Prometheus** scrapes every container on a 1-second interval and feeds real-time telemetry into the **Grafana SRE Performance Monitor** dashboard (`:3000`), tracking p50/p95/p99 latencies, error percentages, and cgroup memory limits.

4. **Step 4 — Offensive Attack Planning & Kernel-Level Execution (Red Team)**:
   Inside the quarantined **Kubernetes Agent Sandbox** (`sre-agent-sandbox`), the **Resilience Attack Planner** queries current platform health and invokes **Claude Sonnet** to devise an attack vector. The planner delegates execution:
   - **tc netem Adversary**: Injects Linux kernel queuing discipline delays (`tc qdisc add dev eth0 root netem delay 2500ms 100ms`) or packet drops onto the Payment Service.
   - **Resource Stresser**: Squeezes the Order Service through cgroup memory spikes or triggers Redis connection pool exhaustion (`curl -X POST /fault/redis-starvation?connections=55`).

5. **Step 5 — Real-Time SLO Breach Detection (Blue Team Sentinel)**:
   As the fault manifests in production, upstream connection pools starve and payment latency spikes. The **Health & Uptime Sentinel** ingests Prometheus anomaly signals. When p99 latency breaches 1200ms or 5XX error rates cross 2.0%, the Sentinel declares an incident (`SEV-1`) and activates the Blue Team response pipeline.

6. **Step 6 — Chain-of-Thought Root Cause Analysis (Blue Team + Claude AI)**:
   The **Root Cause Investigator** extracts live metric anomalies, process memory stats, socket states, and container events, querying **Claude Sonnet with Extended Thinking** over secure outbound HTTPS (port 443). Claude synthesizes competing hypotheses, eliminates false leads through deductive reasoning, pinpointing the exact fault (e.g., Linux kernel tc netem delay or Redis client pool starvation) with an associated confidence score.

7. **Step 7 — Automated Remediation & Stateful Recovery**:
   The **Automated Recovery Fixer** validates the RCA findings against hardened operational runbooks. It issues surgical recovery commands directly to the affected service:
   - Purging raw Linux kernel traffic control queuing disciplines (`tc qdisc del dev eth0 root netem`).
   - Flusing starving client sockets and resetting the Redis connection pool.
   - Reclaiming allocated memory buffers or triggering an orchestrated rolling pod restart.

8. **Step 8 — Health Verification & Incident Post-Mortem Archival**:
   The Blue Team polls the health and metrics endpoints for 10 consecutive ticks, confirming that p99 latency drops back below 800ms, 5XX errors return to 0.00%, and memory returns beneath the cgroup quota. Once normalized, the **Incident Post-Mortem Agent** auto-generates a structured Markdown post-mortem detailing timeline, root cause, and recovery actions in `reports/`.

9. **Step 9 — CloudWatch Audit Logging & Operational Dashboards**:
   Throughout the entire lifecycle, every single shell command executed by Red and Blue team agents, along with exit codes and raw stdout/stderr, is streamed synchronously to **AWS CloudWatch Logs** (`/sre/autonomous-agent-audit`). The dual CloudWatch dashboards (**Agent-Command-Log** and **System-Fault-Metrics**) update in real-time to provide a permanent, auditable operational trail.

---

## Kubernetes Agent Sandbox Architecture & Security Quarantine

To ensure completely safe autonomous operations in production, all offensive and defensive LLM agents execute inside an isolated Kubernetes sandbox namespace (`sre-agent-sandbox`). Autonomous AI agents are never given unconstrained host access, root permissions, or broad network visibility.

<p align="center">
  <img src="docs/images/agent_sandbox_architecture.png" alt="Kubernetes Agent Sandbox Architecture & Security Boundary" width="950" />
</p>
<p align="center"><b>Figure 2: Kubernetes Agent Sandbox Architecture, cgroup Limits & NetworkPolicy Security Boundary</b></p>

### What Purpose Does the Agent Sandbox Solve?

Deploying autonomous agents directly onto production nodes presents significant security and reliability risks: runaway agent loops could exhaust host memory, flawed remediation logic could accidentally reboot the wrong host systems, and unconstrained network access could allow unintentional network scanning or AWS metadata extraction.

The **Kubernetes Agent Sandbox** solves these exact risks through a 4-pillar containment architecture:

| Security Pillar | Concrete Enforcement Mechanism | SRE & Platform Protection Guarantee |
|:---|:---|:---|
| **1. Zero Blast Radius (cgroups v2)** | Hard container limits enforced in Kubernetes manifest: `limits.cpu: 500m`, `limits.memory: 512Mi`. | If an agent experiences a runaway loop or memory leak during chaos testing, the Linux kernel cgroup OOMKiller terminates only the agent pod (`Exit 137`). **Host node stability and system daemons are 100% protected**. |
| **2. Least-Privilege RBAC Quarantine** | Dedicated ServiceAccounts (`red-agent-sa`, `sre-defender-sa`) bound strictly to `sre-target-apps` namespace with scoped verbs (`get`, `list`, `watch`, `pods/exec`). | Agents have **zero cluster-admin privileges**. They cannot inspect `kube-system`, cannot view cluster secrets, and cannot modify node configurations. |
| **3. Strict Network Isolation** | Declarative `NetworkPolicy` (`agent-sandbox-isolation`) with default egress deny. Explicitly allows only: (1) CoreDNS (`UDP 53`), (2) Target microservices (`sre-target-apps`), and (3) Anthropic API (`HTTPS 443`). | Agents **cannot perform lateral network scanning**, cannot access the internet beyond LLM inference, and cannot query AWS instance metadata (`169.254.169.254`). |
| **4. Synchronous CloudWatch Audit Trail** | Every shell command, script invocation, and return code is synchronously streamed to CloudWatch Logs (`/sre/autonomous-agent-audit`). | Complete forensic auditability: every fault injection and automated remediation is recorded in an immutable ledger with zero tampering risk. |

### How the Sandbox Operates During Incident Cycles

1. **Offensive Agent Pod (`red-team-sandbox`)**: Houses the Red Team testing squad. The agents formulate test plans and issue surgical fault injections against microservices inside `sre-target-apps` via Kubernetes exec hooks. Even under maximum stress, the pod cannot exceed 500m CPU or 512Mi RAM.
2. **Defensive Operator Pod (`blue-team-operator`)**: Houses the Blue Team sentinel and recovery squad. When SLO breaches occur, agents query Claude 3.7 Sonnet over outbound HTTPS (port 443) for root-cause analysis and execute approved declarative runbooks against target containers.
3. **Target Microservices Namespace (`sre-target-apps`)**: Houses the live business workload (`api-gw`, `order-service`, `payment-service`, `redis`, `postgres`). This workload is exercised and recovered safely without ever exposing the underlying cloud node or other cluster workloads to disruption.

---

## Tech Stack

| Domain | Technology / Tool | Version | Purpose |
|---|---|---|---|
| **AI Frontier Models** | Anthropic Claude 3.7 Sonnet | `claude-3-7-sonnet-latest` | Test Strategy, Extended Thinking RCA, Auto-Remediation |
| | Anthropic Claude 3.5 Sonnet | `claude-3-5-sonnet-latest` | Sub-second Incident Monitoring & Network Adversary actions |
| **Backend / Services** | Python / FastAPI / Uvicorn | `3.11` / `0.111.0` | High-throughput asynchronous target microservices & API Gateway |
| | HTTPX | `0.27.0` | Asynchronous inter-service HTTP client and proxy router |
| | Pydantic | `2.8.2` | Data validation and JSON schema enforcement |
| **Observability** | Prometheus | `v2.52.0` | 1-second high-resolution metric collection and PromQL engine |
| | Grafana | `10.4.2` | Pure infrastructure monitoring dashboard (:3000) |
| | AWS CloudWatch | Native AWS | Dedicated security audit dashboard tracking exact agent commands and outputs |
| **Load Testing** | Python Async Worker Engine / k6 | Custom / `0.50+` | Concurrent multi-step consumer workflow traffic generator |
| **Container & Cloud** | Docker & Docker Compose | `v2.24+` | Container runtime, resource isolation, and local orchestration |
| | Certified Kubernetes (`k3s`) | `v1.29+` | Production container orchestration, cgroups, and RBAC sandboxes |
| | Terraform | `v1.7+` | All-in-one Infrastructure-as-Code for AWS cloud deployment |
| | AWS (VPC, EC2, IAM, SSM, CloudWatch) | Provider `~> 5.0` | Multi-tier cloud infrastructure host with zero NAT Gateway overhead |

---

## Detailed Setup Instructions

The platform's infrastructure lives directly on **Amazon Web Services (AWS)**, provisioned cleanly via Terraform. Follow these copy-and-paste commands to deploy and run the system.

### Prerequisites

- **AWS CLI** installed and configured with valid credentials (`aws sts get-caller-identity`).
- **Terraform 1.5+** installed.
- **Python 3.10+** installed.
- **Anthropic API Key** (for Claude 3.7 Sonnet & 3.5 Sonnet).
- **Docker** (installed locally or via host).

---

### Step 1: Clone and Navigate to the Repository

```bash
git clone https://github.com/ritvikindupuri/ResilienceOps.git
cd ResilienceOps
```

---

### Step 2: Configure Your Anthropic API Key

Create your local `.env` configuration file from the provided template:

```bash
# On Linux / macOS / Git Bash:
cp .env.example .env

# On Windows PowerShell:
Copy-Item .env.example .env
```

Open `.env` in any text editor and insert your Anthropic API key:

```ini
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_ACTUAL_KEY_HERE
```

*(Note: `.env` is already included in `.gitignore` to prevent committing secrets).*

---

### Step 3: Install Agent Dependencies

Install the core Python libraries required by the multi-agent engine:

```bash
pip install -r requirements.txt
```

---

### Step 4: Deploy the Production Infrastructure to AWS (Terraform)

Deploy the multi-tier VPC, subnets, security groups, IAM instance profile, and cloud host to AWS:

```bash
cd terraform
terraform init
terraform apply -auto-approve
```

Terraform automatically provisions the entire cloud topology in ~60 seconds and outputs your live AWS public endpoints:

```text
Outputs:
api_gateway_url = "http://54.xxx.xxx.xxx:8000"
grafana_url     = "http://54.xxx.xxx.xxx:3000"
prometheus_url  = "http://54.xxx.xxx.xxx:9090"
public_ip       = "54.xxx.xxx.xxx"
```

Save your `public_ip` (or `grafana_url`) from the output.

<p align="center">
  <img src="docs/images/aws_vpc_resource_map.png" alt="AWS Enterprise VPC Resource Map" width="950" />
</p>
<p align="center"><b>Figure 3: Live AWS Enterprise VPC Resource Map (3-Tier Subnet Segmentation & Ingress Routing)</b></p>
---

### Step 5: Quarantined Kubernetes Agent Sandbox Pod Access & Live Logs

The Red Team and Blue Team agents run inside a hardened Kubernetes sandbox environment (`sre-agent-sandbox` namespace) on the AWS cluster, configured with cgroup limits (`500m` CPU, `512Mi` RAM) and strict egress policies.

#### 1. Connect to the AWS Host (Zero-SSH via AWS Systems Manager):
No SSH keys or open port 22 are needed. You can connect securely from your browser:
- Open **AWS Systems Manager** -> **Fleet Manager** -> Select instance `sre-enterprise-platform-host` -> Click **Start terminal session**.
- Or run in your terminal:
  ```bash
  aws ssm start-session --target <YOUR_EC2_INSTANCE_ID>
  ```

#### 2. Verify Sandbox Pod Status & Quarantine:
Inside the host shell:
```bash
k3s kubectl get pods,roles,rolebindings,networkpolicies -n sre-agent-sandbox
```

Output:
```text
NAME                                  READY   STATUS    RESTARTS   AGE
pod/red-team-sandbox-978bfdddd-phvv4  1/1     Running   0          2m
```

#### 3. View Live Agent Sandbox Pod Logs:
To stream real-time logs generated inside the quarantined container:
```bash
k3s kubectl logs -f deployment/red-team-sandbox -n sre-agent-sandbox
```

#### 4. Attach an Interactive Shell Inside the Sandbox Pod:
You can attach directly inside the isolated sandbox container to inspect environment variables, run tests, or execute curl calls:
```bash
k3s kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- /bin/bash
```

---

## Operational Runbook & Quickstart

Follow this operational walkthrough to monitor live metrics, inspect security audits, trigger autonomous agent cycles against your AWS infrastructure, and review post-mortems.

> [!TIP]
> **Detailed Telemetry & Metrics Report**:  
> For comprehensive high-resolution dashboard screenshots, detailed per-panel metric breakdowns, and an authentic SRE post-mortem report, see [**RESULTS.md**](RESULTS.md).

### Step 1: Open the Live AWS Grafana Dashboard (Pure Infra Monitoring)
1. Open your web browser and navigate to your AWS Grafana URL:
   ```text
   http://<YOUR_AWS_PUBLIC_IP>:3000
   ```
2. Enter the default credentials:
   - **Username**: `admin`
   - **Password**: `admin`
3. Click **Log In**. (Click **Skip** when prompted to change password).
4. In the left navigation menu, click **Dashboards** -> **SRE & Reliability** -> click **SRE Infrastructure & Reliability Performance Monitor**.
5. Observe the 8 focused operational panels streaming every **1 second**:
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

#### What you will observe in the terminal:
- **Phase 1**: **Health & Uptime Monitor** performs a baseline health check on AWS (`HTTP 200`, Latency `<300ms`).
- **Phase 2**: Red Team **Resilience Attack Planner** (`Claude Sonnet`) evaluates the AWS topology and formulates an attack campaign.
- **Phase 3**: Red Team **Server Resource Stresser** executes physical memory allocation in container RAM on your AWS host.
- **Phase 4**: Blue Team **Health & Uptime Monitor** detects the SLO breach as latency exceeds 1200ms (`INCIDENT DECLARED | MTTD: 2.14s`).
- **Phase 5**: Blue Team **Root Cause Investigator** invokes **Claude Sonnet with Extended Thinking**, outputs step-by-step reasoning, isolates `MEMORY_EXHAUSTION_OOM`, and prescribes `EVICT_CONTAINER_AND_PURGE_LEAK`.
- **Phase 6**: Blue Team **Automated Recovery Fixer** purges leaked memory buffers, bounces the container on AWS, and verifies recovery within `<800ms` (`✅ Recovery Validated | MTTR: 3.42s`).
- **Phase 7**: Blue Team **Incident Report Writer** compiles and archives a formal post-mortem report to `reports/`.

---

### Step 4: Watch the Live AWS Grafana Dashboard React in Real Time
Keep the AWS Grafana dashboard open while running the cycle:
1. **At T+2s**: Watch the **Real-Time System State** gauge flip from `HEALTHY` to `ACTIVE INCIDENT`.
2. **At T+3s**: Watch the **Latency Profiles** chart spike into the red (>2000ms).
3. **At T+5s**: Observe the **5XX Error Rate** climb as upstream connection timeouts accumulate.
4. **At T+8s**: As Claude's remediation executes on AWS, watch the latency line plummet immediately back to baseline and the status gauge turn green.

---

### Step 5: Test Additional Enterprise Failure Scenarios

Target different failure mechanisms on your AWS cluster using the `--scenario` argument directly through the sandbox pod:

```bash
# Test Linux Kernel tc netem Packet Latency on eth0 (Inside Sandbox Pod):
k3s kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- \
  python3 orchestrator.py --target-ip api-gw.sre-target-apps.svc.cluster.local --cycles 1 --scenario KERNEL_TC_NETEM_LATENCY

# Test Linux Kernel tc netem Packet Loss (35% frame drops on eth0):
k3s kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- \
  python3 orchestrator.py --target-ip api-gw.sre-target-apps.svc.cluster.local --cycles 1 --scenario KERNEL_TC_NETEM_PACKET_LOSS

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

#### Sample Live Incident Post-Mortem Report:
**[View Sample Incident Report: `reports/incident_20261006_010119_unknown_fault.md`](reports/incident_20261006_010119_unknown_fault.md)**

```markdown
# Incident Post-Mortem Report: UNKNOWN_FAULT
**Incident Timestamp**: 2026-10-06 01:01:19 UTC  
**Classification**: Production Incident (`SEV-1`)  
**Impacted Service**: `order-service`  
**Incident State**: `RESOLVED`  
**Handling Agents**: Health & Uptime Monitor, Root Cause Investigator, Automated Recovery Fixer, Incident Report Writer  

## 1. Executive Summary
At 2026-10-06 01:01:19 UTC, an automated reliability breach was detected impacting `order-service`. Telemetry monitoring identified SLO violations across request latency and error rates. The autonomous diagnostic system identified `DOWNSTREAM_PAYMENT_LATENCY` with 95.0% confidence and triggered remediation runbook `RESET_PAYMENT_PARAMETERS`, restoring normal operations.

### Key Metrics
- Mean Time To Detect (MTTD): 52.98 seconds
- Mean Time To Remediate (MTTR): 57.55 seconds
- Total Incident Duration: 110.53 seconds
- Service Level Objective (SLO): Preserved

## 2. Chronological Timeline
- T0 (+0.0s): Fault injected into order-service.
- T1 (+53.0s): SLO breach detected by Incident Monitor. Severity classified as SEV-1.
- T2 (+53.8s): Root Cause Analysis completed (DOWNSTREAM_PAYMENT_LATENCY).
- T3 (+54.8s): Runbook RESET_PAYMENT_PARAMETERS executed by Auto-Remediator.
- T4 (+110.5s): Latency and error rates verified within baseline thresholds. Incident resolved.
```

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

### Offline Development Mode (Local Docker Sandbox)
To run an offline sandbox on your workstation without cloud infrastructure:

```bash
# Start local containers and offline agent sandbox
docker compose up --build -d

# Run local agent resilience cycle
python orchestrator.py --cycles 1 --scenario MEMORY_EXHAUSTION

# Teardown local containers and clean volumes
docker compose down -v
```

---

## Detailed Technical Documentation

For the comprehensive technical specification covering mathematical SLO formulations, cgroup kernel limits, Claude 3.7 prompt architectures, Kubernetes agent sandbox security, and AWS network topology, refer to:

📖 **[Complete Technical Documentation (PDF)](docs/ResilienceOps_Technical_Documentation.pdf)**
