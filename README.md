# ResilienceOps - Autonomous Multi-Agent SRE & Chaos Engineering Platform

> An enterprise-grade autonomous Site Reliability Engineering (SRE) platform where coordinated Red Team Chaos Agents launch real infrastructure faults against a live microservices cluster, and Blue Team SRE Agents autonomously detect, diagnose with Claude 3.7 Extended Thinking, and remediate incidents in real time—monitored second-by-second on a live streaming Grafana dashboard.

---

## Overview

Modern distributed systems require continuous resilience validation, yet standard chaos testing is either purely manual or decoupled from automated remediation workflows. **ResilienceOps** closes this loop with an autonomous, production-grade multi-agent architecture.

The platform runs an authentic containerized microservices stack under live, concurrent automated user traffic. A coordinated **3-Agent Red Team** analyzes the topology and executes kernel-level and network-level faults (Linux cgroup memory leaks, CPU CFS quota exhaustion, network transit delays, and TCP packet drops). Simultaneously, a **3-Agent Blue Team** continuously watches the SRE Golden Signals, declares incidents upon Service Level Objective (SLO) breaches, executes deep root-cause analysis (RCA) via **Claude 3.7 Sonnet with Extended Thinking**, triggers automated recovery runbooks, and authors standardized post-mortem reports.

All telemetry is streamed in **100% real-time (1-second tick interval)** to an auto-provisioned Grafana dashboard.

📖 **For exhaustive technical specifications, math models, and agent communication protocols, read the [Technical Documentation](TECHNICAL_DOCUMENTATION.md).**

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
  - **AWS CloudWatch (Agent Logs & Fault Telemetry)**: Dedicated observability dashboards (`Agent-Command-Audit` and `System-Fault-Metrics`) logging every exact command executed by Red Team and Blue Team agents alongside their exact execution outputs streamed into CloudWatch Logs (`/sre/autonomous-agent-audit`).
- **Kubernetes Agent Sandbox & Security Quarantine**:
  - Agents run inside an isolated `sre-agent-sandbox` namespace constrained by Kubernetes resource limits (`cpu: 500m`, `memory: 512Mi`), audited RBAC roles, and egress NetworkPolicies.
  - Interactive operator shell access via `kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- /bin/bash` with direct cluster connectivity to microservice targets.
- **Enterprise Cost-Optimized Cloud Deployment**:
  - Single-file Terraform architecture (`terraform/main.tf`) deploying to AWS with multi-tier VPC segmentation, segregated security groups, and an EC2 host (`t3.small` / `t4g.small` at ~\$0.02/hr).
  - Eliminates AWS NAT Gateways (\$32/mo) and EKS control plane fees (\$72/mo).
  - 1-command deploy and 1-command clean teardown ensuring zero orphan charges.

---

## System Architecture

```mermaid
flowchart TB
    subgraph TrafficLayer ["⚡ LIVE PRODUCTION WORKLOAD TRAFFIC LAYER"]
        TG["Automated Workload Engine (k6 / asyncio)<br/>20 RPS Continuous Browse, Order, Pay Journeys"]
    end

    subgraph InfraBoundary ["☁️ INFRASTRUCTURE BOUNDARY (Docker / Kubernetes / AWS)"]
        
        subgraph TargetTier ["📦 Namespace: sre-target-apps (The Production Workload)"]
            APIGW["API Gateway (:8000)<br/>FastAPI / Reverse Proxy / Prometheus Metrics"]
            OrderSvc["Order Service (:8001)<br/>State Management / cgroup Quotas"]
            PaymentSvc["Payment Service (:8002)<br/>Payment Gateway / Async Latency"]
            
            APIGW -->|Proxy HTTP /orders| OrderSvc
            APIGW -->|Proxy HTTP /payments| PaymentSvc
        end

        subgraph SandboxTier ["🛡️ Namespace: sre-agent-sandbox (Security Quarantine)"]
            subgraph RedSquad ["🔴 Red Team: Offensive Testing Squad"]
                R1["Resilience Attack Planner<br/>(Claude Sonnet)"]
                R2["Server Resource Stresser<br/>(Claude Sonnet)"]
                R3["Network Delay Injector<br/>(Claude Haiku)"]
                R1 --> R2 & R3
            end

            subgraph BlueSquad ["🔵 Blue Team: Defensive Recovery Squad"]
                B1["Health & Uptime Monitor<br/>(Claude Haiku)"]
                B2["Root Cause Investigator<br/>(Claude Sonnet Extended Thinking)"]
                B3["Automated Recovery Fixer<br/>(Claude Sonnet)"]
                B1 --> B2 --> B3
            end
        end

        subgraph ObsTier ["📊 Observability Tier (Real-Time 1s Stream)"]
            Prom["Prometheus Server (:9090)<br/>1-Second High-Resolution Scrape Engine"]
            Grafana["Grafana SRE Infra Monitor (:3000)<br/>Pure Infra Telemetry & cgroup Saturation"]
            Prom --> Grafana
        end
    end

    subgraph CloudAudit ["☁️ AWS CLOUDWATCH OBSERVABILITY TIER"]
        CWLogs["CloudWatch Logs: /sre/autonomous-agent-audit<br/>Stream: audit-stream"]
        CWDash["Dashboards: Agent-Command-Audit & System-Fault-Metrics<br/>Exact Commands & Execution Outputs"]
        CWLogs --> CWDash
    end

    subgraph CloudAI ["🧠 ANTHROPIC CLOUD (API / HTTPS 443)"]
        ClaudeAPI["Anthropic Messages API<br/>(Claude 3.7 Sonnet & Claude 3.5 Sonnet)"]
    end

    TG ==>|HTTP Requests| APIGW
    TargetTier -.->|Scrapes /metrics every 1s| Prom
    R2 & R3 ==>|Kernel & Network Chaos Injections| TargetTier
    TargetTier -.->|Telemetry & Anomaly Signals| B1
    B3 ==>|Executes Remediations & Pod Restarts| TargetTier
    SandboxTier -.->|Streams Exact Commands & Output JSON| CWLogs
    SandboxTier <===>|HTTPS 443 (Zero Bare-Metal Access)| ClaudeAPI
```

<p align="center"><b>Figure 1: ResilienceOps End-to-End System & Runtime Architecture</b></p>

### Flow-by-Flow Explanation of the Architecture

1. **Baseline Traffic Generation**:
   The Automated Traffic Generator runs concurrent asynchronous worker sessions executing real consumer workflows (browsing products, checking inventory, submitting checkout orders, and settling credit card transactions) against the API Gateway (`:8000`).
2. **Telemetry Ingestion & Scraping**:
   The API Gateway instrumented with the Prometheus client records request duration histograms, status counters (2xx, 4xx, 5xx), and error ratios. Prometheus scrapes the `/metrics` endpoints across all containers at an uncompromising **1-second interval**, feeding Grafana's pure infrastructure live streaming dashboard.
3. **Offensive Campaign Planning (Red Team)**:
   The **Resilience Attack Planner** inspects the topology and current SLO burn rate, prompting Claude Sonnet to devise a tactical failure mode. It delegates the execution to either the **Server Resource Stresser** (for cgroup OOMKill or CPU starvation) or the **Network Delay Injector** (for downstream latency and packet drops).
4. **Failure Propagation & Kernel Stress**:
   The targeted microservice receives the fault. Memory chunks are physically populated in RAM until the Linux kernel cgroup OOMKiller issues `SIGKILL` (Exit 137), or CPU compute loops saturate CPU limits. Upstream connection pools starve, causing the API Gateway to emit HTTP 504 timeouts.
5. **SLO Breach Detection (Blue Team)**:
   The **Health & Uptime Monitor** continuously evaluates the 4 Golden Signals. When p99 latency breaches 1200ms or 5xx errors exceed 2.0%, it triggers `INCIDENT_DECLARED` with an escalated severity rating (`SEV-1`).
6. **Chain-of-Thought Root Cause Analysis (RCA)**:
   The **Root Cause Investigator** sends telemetry metrics, error patterns, and Kubernetes events to **Claude Sonnet with Extended Thinking**. Claude generates three competing hypotheses, refutes false leads through deductive reasoning, and confirms the primary root cause with an exact confidence score.
7. **Automated Remediation & Verification**:
   The **Automated Recovery Fixer** retrieves the diagnosed runbook (e.g., clearing leaked buffers, issuing a rolling pod bounce, or scaling replicas). It executes the recovery commands, polls health endpoints to verify latency has normalized below 800ms, and invokes the **Incident Report Writer** to archive a formal incident post-mortem in `reports/`.
8. **CloudWatch Command & Fault Logging**:
   Every agent action, the exact command launched, and the raw execution output are dispatched as structured events to CloudWatch Logs (`/sre/autonomous-agent-audit`), rendered live across the `Agent-Command-Audit` and `System-Fault-Metrics` dashboards.

---

## Tech Stack

| Domain | Technology / Tool | Version | Purpose |
|---|---|---|---|
| **AI Frontier Models** | Anthropic Claude 3.7 Sonnet | `claude-3-7-sonnet-latest` | Chaos Strategy, Extended Thinking RCA, Auto-Remediation |
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
- *(Optional)* **Docker Desktop** (only if you want to run an offline local sandbox before cloud deployment).

---

### Step 1: Clone and Navigate to the Repository

```bash
git clone https://github.com/your-username/sre-colosseum.git
cd sre-colosseum
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
<p align="center"><b>Figure 4.1: Live AWS Enterprise VPC Resource Map (3-Tier Subnet Segmentation & Ingress Routing)</b></p>
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

## How to Use the App (Step-by-Step Guide)

Follow this click-by-click walkthrough to monitor live metrics, inspect security audits, trigger autonomous agent cycles against your AWS infrastructure, and review post-mortems.

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

<p align="center">
  <img src="docs/images/grafana_sre_performance_monitor.png" alt="Grafana SRE Performance Monitor" width="950" />
</p>
<p align="center"><b>Figure 1.1: Live AWS Grafana Infrastructure & Reliability Performance Monitor (Streaming 1-Second Telemetry)</b></p>
---

### Step 2: Open the AWS CloudWatch Dashboards
To inspect the exact security actions, injected attack vectors, and raw command outputs:
1. Open the **AWS Console** in your browser and switch to `us-east-1`.
2. Navigate to **CloudWatch** -> **Dashboards**.
3. You will find two clear, dedicated CloudWatch dashboards:
   - **`Agent-Command-Audit`**: Real-time audit log stream capturing exact commands executed by Red Team and Blue Team agents alongside raw terminal outputs from `/sre/autonomous-agent-audit`:
     - *Header*: `# Agent Command Log` (Live audit trail of test commands and recovery fixes).
     - *Left Table*: **Red Team: Injected Commands & Outputs** (Tracks exact kernel `tc netem`, Redis starvation, and memory allocation commands).
     - *Right Table*: **Blue Team: Remediation Commands & Outputs** (Tracks exact runbook actions and recovery statuses).
     - *Bottom Table*: **Unified Agent Command & Security Audit Stream** (Full chronologically sorted audit ledger).
   - **`System-Fault-Metrics`**: Dedicated visual telemetry dashboard tracking active and resolved resilience attack vectors:
     - *Header*: `# System Faults & Recovery` (Visual tracking of active attack vectors and remediation velocity).
     - *Graph 1*: **📈 Fault Injections by Vector** (Time-series line charts tracking kernel `tc netem` latency, Redis starvation, and memory leaks).
     - *Graph 2*: **🛡️ Incident Rate vs Remediation Recovery Velocity** (Direct time-series comparison between active SEV-1 incidents and resolved remediations).
     - *Graph 3*: **📊 Attack Vector Distribution Share** (Interactive pie chart showing the percentage breakdown across all tested fault vectors).
     - *Audit Table*: **📋 Active vs Resolved Fault Lifecycle Audit** (Live status log showing faults transitioning from `FAULT_ACTIVE` to `RESOLVED`).

<p align="center">
  <img src="docs/images/cloudwatch_agent_command_audit.png" alt="AWS CloudWatch Agent Command Log" width="950" />
</p>
<p align="center"><b>Figure 2.1: AWS CloudWatch Agent-Command-Audit Dashboard (Dual-Pane Red vs. Blue Team Command Logs)</b></p>
<p align="center">
  <img src="docs/images/cloudwatch_system_faults_recovery.png" alt="AWS CloudWatch System Faults and Recovery" width="950" />
</p>
<p align="center"><b>Figure 2.2: AWS CloudWatch System-Fault-Metrics Dashboard (Visual Attack Vectors & Remediation Velocity)</b></p>
---

### Step 3: Launch the Autonomous SRE Agents Against AWS

You can run the multi-agent resilience cycle either directly from your workstation or from inside the quarantined Kubernetes agent sandbox pod:

#### Option A: Direct Terminal Execution (Targeting AWS Public IP)
```bash
python orchestrator.py --target-ip <YOUR_AWS_PUBLIC_IP> --cycles 1 --scenario MEMORY_EXHAUSTION
```

#### Option B: Quarantined Execution (Inside Kubernetes Sandbox Pod on AWS)
```bash
kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- \
  python3 orchestrator.py --target-ip api-gw.sre-target-apps.svc.cluster.local --cycles 1 --scenario MEMORY_EXHAUSTION
```

#### What you will observe in the terminal:
- **Phase 1**: **Health & Uptime Monitor** performs a baseline health check on AWS (`HTTP 200`, Latency `<300ms`).
- **Phase 2**: Red Team **Resilience Attack Planner** (`Claude Sonnet`) evaluates the AWS topology and formulates an attack campaign.
- **Phase 3**: Red Team **Server Resource Stresser** executes physical memory allocation in container RAM on your AWS host.
- **Phase 4**: Blue Team **Health & Uptime Monitor** detects the SLO breach as latency exceeds 1200ms (`🚨 INCIDENT DECLARED | MTTD: 2.14s`).
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

Target different failure mechanisms on your AWS cluster using the `--scenario` argument:

```bash
# Test Linux Kernel tc netem Packet Latency on eth0:
python orchestrator.py --target-ip <YOUR_AWS_PUBLIC_IP> --cycles 1 --scenario KERNEL_TC_NETEM_LATENCY

# Test Linux Kernel tc netem Packet Loss (35% frame drops on eth0):
python orchestrator.py --target-ip <YOUR_AWS_PUBLIC_IP> --cycles 1 --scenario KERNEL_TC_NETEM_PACKET_LOSS

# Test Redis Connection Pool Starvation (saturating maxclients limit):
python orchestrator.py --target-ip <YOUR_AWS_PUBLIC_IP> --cycles 1 --scenario REDIS_CONNECTION_STARVATION

# Test CPU CFS Quota Saturation & Thread Starvation:
python orchestrator.py --target-ip <YOUR_AWS_PUBLIC_IP> --cycles 1 --scenario CPU_SATURATION

# Run multiple back-to-back resilience rounds:
python orchestrator.py --target-ip <YOUR_AWS_PUBLIC_IP> --cycles 3 --delay 5
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
   Open **CloudWatch** -> **Dashboards** -> **`Agent-Command-Audit`**. The middle table (*"Blue Team SRE Agents: Exact Remediation Commands & Outputs"*) streams the exact `GENERATE_POST_MORTEM` commands, MTTR calculation metrics, and report storage confirmations in real time.

#### Sample Live Incident Post-Mortem Report:
👉 **[View Sample Incident Report: `reports/incident_20261006_010119_unknown_fault.md`](reports/incident_20261006_010119_unknown_fault.md)**

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

### Optional: Local Offline Sandbox Mode
If you want to run an offline local sandbox on your laptop without touching AWS:

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

👉 **[Complete Technical Documentation](TECHNICAL_DOCUMENTATION.md)**
