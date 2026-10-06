import sys
import os
import time
import argparse
from datetime import datetime

# Parse arguments first so environment variables are applied before submodules import config
parser = argparse.ArgumentParser(description="Autonomous SRE Resilience & Incident Response Platform")
parser.add_argument("--cycles", type=int, default=2, help="Number of resilience cycles to execute")
parser.add_argument("--scenario", type=str, default=None, help="Specific scenario: MEMORY_EXHAUSTION, NETWORK_LATENCY, CPU_SATURATION, PACKET_LOSS")
parser.add_argument("--delay", type=int, default=4, help="Cooldown delay between cycles in seconds")
parser.add_argument("--target-ip", type=str, default=None, help="AWS EC2 Public IP address where the infrastructure is deployed")
cli_args, _ = parser.parse_known_args()

if cli_args.target_ip:
    os.environ["API_GATEWAY_URL"] = f"http://{cli_args.target_ip}:8000"
    os.environ["ORDER_SERVICE_URL"] = f"http://{cli_args.target_ip}:8001"
    os.environ["PAYMENT_SERVICE_URL"] = f"http://{cli_args.target_ip}:8002"
    os.environ["PROMETHEUS_URL"] = f"http://{cli_args.target_ip}:9090"
    print(f"[*] Configured active target -> AWS Host at http://{cli_args.target_ip}:8000")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Red Team (Offensive Squad)
from agents.fault_injector.strategist import ChaosStrategistAgent
from agents.fault_injector.infra_disruptor import InfraDisruptorAgent
from agents.fault_injector.network_adversary import NetworkAdversaryAgent

# Blue Team (Defensive Squad)
from agents.incident_response.monitor import IncidentMonitor
from agents.incident_response.diagnostician import DiagnosticAgent
from agents.incident_response.remediator import RemediatorAgent
from agents.incident_response.post_mortem import PostMortemGenerator

def run_resilience_cycle(cycle_id: int, forced_scenario: str = None):
    print("\n" + "="*80)
    print(f"[*] RESILIENCE TESTING CYCLE #{cycle_id} INITIALIZED - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*80)

    # Initialize 3 Red Team Agents
    red_strategist = ChaosStrategistAgent()
    red_infra = InfraDisruptorAgent()
    red_network = NetworkAdversaryAgent()

    # Initialize 3 Blue Team Agents
    blue_monitor = IncidentMonitor()
    blue_diagnostician = DiagnosticAgent()
    blue_remediator = RemediatorAgent()
    blue_post_mortem = PostMortemGenerator()

    # Phase 1: Pre-test Baseline Check
    print("\n[PHASE 1] Pre-test Baseline Telemetry Check...")
    telemetry = blue_monitor.inspect_telemetry()
    print(f"    Gateway Health: HTTP {telemetry['gateway_status']} | Base Latency: {telemetry['latency_ms']}ms")

    # Phase 2: Red Team Campaign Planning (Resilience Attack Planner)
    print("\n[PHASE 2 - RED TEAM] Resilience Attack Planner Formulating Campaign...")
    target_services = ["api-gw", "order-service", "payment-service"]
    campaign = red_strategist.plan_campaign(telemetry, target_services)
    print(f"    Attack Planner Model: {campaign['llm_model']}")
    print(f"    Attack Strategy: {campaign['strategic_intent']}")

    # Phase 3: Red Team Tactical Execution (Server Resource Stresser OR Network Delay Injector)
    print("\n[PHASE 3 - RED TEAM] Dispatching Tactical Stress Agent...")
    scenario = forced_scenario or ("NETWORK_LATENCY" if cycle_id % 2 == 0 else "MEMORY_EXHAUSTION")
    t_start = time.time()
    
    if "NETWORK" in scenario or "PACKET" in scenario or "LATENCY" in scenario:
        print("    [Operative: Network Delay Injector] Injected downstream transit delay & connection stress.")
        fault_event = red_network.execute_fault(scenario)
    else:
        print("    [Operative: Server Resource Stresser] Injected container memory allocation / cgroup stress.")
        fault_event = red_infra.execute_fault(scenario)

    # Phase 4: Blue Team Telemetry Monitoring (Health & Uptime Monitor)
    print("\n[PHASE 4 - BLUE TEAM] Health & Uptime Monitor Scanning Telemetry for SLO Breaches...")
    incident = None
    mttd = 0.0
    for tick in range(1, 10):
        time.sleep(1.0)
        curr = blue_monitor.inspect_telemetry()
        incident = blue_monitor.evaluate_slos(curr)
        if incident:
            mttd = time.time() - t_start
            print(f"[!] INCIDENT DECLARED | MTTD: {mttd:.2f}s | Severity: {incident['severity']}")
            for v in incident["violations"]:
                print(f"    - Violation: {v}")
            break
        else:
            print(f"    [t+{tick}s] Latency: {curr['latency_ms']}ms | Gateway HTTP: {curr['gateway_status']}")

    if not incident:
        print("[-] Service absorbed degradation within SLO error budget. Cycle complete.")
        return

    # Phase 5: Blue Team Diagnostic RCA with Extended Thinking (Root Cause Investigator)
    print("\n[PHASE 5 - BLUE TEAM] Root Cause Investigator Running Deep Step-by-Step Diagnosis...")
    time.sleep(0.5)
    diagnosis = blue_diagnostician.analyze(incident)
    print(f"    Identified Root Cause: {diagnosis['primary_root_cause']} (Confidence: {diagnosis['confidence_score']*100:.1f}%)")
    print(f"    Claude Reasoning: {diagnosis.get('llm_reasoning', 'Analyzed')}")
    print(f"    Prescribed Fix: {diagnosis['recommended_runbook']}")

    # Phase 6: Blue Team Automated Remediation & Verification (Automated Recovery Fixer)
    print("\n[PHASE 6 - BLUE TEAM] Automated Recovery Fixer Executing Recovery Fix...")
    remediation = blue_remediator.execute_runbook(diagnosis)
    print(f"    Actions Executed: {remediation['actions_taken']}")
    mttr = time.time() - (t_start + mttd)
    print(f"[OK] Recovery Validated | MTTR: {mttr:.2f}s | Status: {remediation['verification']['status']}")

    # Phase 7: Incident Report Generation (Incident Report Writer)
    print("\n[PHASE 7 - BLUE TEAM] Incident Report Writer Compiling Summary Report...")
    report = blue_post_mortem.generate(fault_event, incident, diagnosis, remediation, mttd, mttr)
    print("    Report generated and archived to reports/ directory.")
    print("="*80 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Autonomous SRE Resilience & Incident Response Platform")
    parser.add_argument("--cycles", type=int, default=2, help="Number of resilience cycles to execute")
    parser.add_argument("--scenario", type=str, default=None, help="Specific scenario: MEMORY_EXHAUSTION, NETWORK_LATENCY, CPU_SATURATION, PACKET_LOSS")
    parser.add_argument("--delay", type=int, default=4, help="Cooldown delay between cycles in seconds")
    parser.add_argument("--target-ip", type=str, default=None, help="AWS EC2 Public IP address where the infrastructure is deployed")
    args = parser.parse_args()

    # If targeting AWS infrastructure directly
    if args.target_ip:
        import agents.config as cfg
        cfg.API_GATEWAY_URL = f"http://{args.target_ip}:8000"
        cfg.ORDER_SERVICE_URL = f"http://{args.target_ip}:8001"
        cfg.PAYMENT_SERVICE_URL = f"http://{args.target_ip}:8002"
        cfg.PROMETHEUS_URL = f"http://{args.target_ip}:9090"
        print(f"[*] Configured active target -> AWS Host at http://{args.target_ip}:8000")

    print("""
================================================================================
  AUTONOMOUS SRE PLATFORM: 3 RED TEAM AGENTS VS 3 BLUE TEAM AGENTS
================================================================================
  RED TEAM:  1. Resilience Attack Planner | 2. Server Resource Stresser | 3. Network Delay Injector
  BLUE TEAM: 1. Health & Uptime Monitor   | 2. Root Cause Investigator  | 3. Automated Recovery Fixer
================================================================================
    """)

    for c in range(1, args.cycles + 1):
        run_resilience_cycle(c, forced_scenario=args.scenario)
        if c < args.cycles:
            print(f"[*] Cooling down for {args.delay} seconds before next cycle...")
            time.sleep(args.delay)

if __name__ == "__main__":
    main()
