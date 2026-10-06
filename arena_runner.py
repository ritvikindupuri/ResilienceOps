import time
import sys
import os
import argparse

# Ensure utf-8 output on all platforms
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from agents.attacker.agent import RedTeamAttackerAgent
from agents.defender.sentinel import BlueTeamSentinel
from agents.defender.investigator import BlueTeamInvestigator
from agents.defender.operator import BlueTeamOperator
from agents.defender.post_mortem import PostMortemGenerator

def run_battle_round(round_num: int, vector_override: str = None):
    print("\n" + "="*80)
    print(f">> SRE COLOSSEUM: ARENA BATTLE ROUND #{round_num} STARTING <<")
    print("="*80)

    attacker = RedTeamAttackerAgent()
    sentinel = BlueTeamSentinel()
    investigator = BlueTeamInvestigator()
    operator = BlueTeamOperator()
    post_mortem_gen = PostMortemGenerator()

    # Step 1: Pre-Attack Baseline Check
    print("\n[*] Pre-battle baseline telemetry check...")
    telemetry = sentinel.inspect_telemetry()
    print(f"    Gateway: HTTP {telemetry['gateway_status']} | Latency: {telemetry['latency_ms']}ms")

    # Step 2: Red Team Attacks
    print("\n[RED TEAM] Selecting and deploying chaos attack...")
    t_attack = time.time()
    attack_event = attacker.launch_attack(forced_vector=vector_override)
    print(f"    Vector: {attack_event['vector']} -> Target: {attack_event['target']}")
    print(f"    Expected Impact: {attack_event['expected_impact']}")

    # Step 3: Blue Team Sentinel Observes & Detects
    print("\n[BLUE TEAM] Sentinel scanning telemetry for SLO breach...")
    incident = None
    mttd = 0.0
    for tick in range(1, 10):
        time.sleep(1.0)
        curr_telemetry = sentinel.inspect_telemetry()
        incident = sentinel.evaluate_slos(curr_telemetry)
        if incident:
            mttd = time.time() - t_attack
            print(f"[!] [INCIDENT DECLARED] MTTD: {mttd:.2f}s | Severity: {incident['severity']}")
            for breach in incident["breaches"]:
                print(f"    WARNING: {breach}")
            break
        else:
            print(f"    [t+{tick}s] Telemetry: Latency {curr_telemetry['latency_ms']}ms | Gate HTTP {curr_telemetry['gateway_status']}")

    if not incident:
        print("[-] Target remained within SLO limits. Round completed.")
        return

    # Step 4: Blue Team Investigator Diagnoses Root Cause
    print("\n[BLUE TEAM] Investigator initiating Root Cause Analysis (RCA)...")
    time.sleep(0.5)
    diagnosis = investigator.diagnose(incident)
    print(f"    Primary Root Cause: {diagnosis['primary_root_cause']} (Confidence: {diagnosis['confidence_score']*100:.1f}%)")
    print(f"    Recommended Runbook: {diagnosis['recommended_runbook']}")

    # Step 5: Blue Team Operator Remediates
    print("\n[BLUE TEAM] Operator executing automated remediation runbook...")
    remediation = operator.execute_remediation(diagnosis)
    print(f"    Actions Executed: {remediation['actions_taken']}")
    
    mttr = time.time() - (t_attack + mttd)
    print(f"[OK] [RECOVERY CONFIRMED] MTTR: {mttr:.2f}s | Status: {remediation['verification']['status']}")

    # Step 6: Post-Mortem Report Generation
    print("\n[SRE POST-MORTEM] Compiling incident report...")
    report = post_mortem_gen.generate(attack_event, incident, diagnosis, remediation, mttd, mttr)
    
    # Save post-mortem to reports directory
    os.makedirs("reports", exist_ok=True)
    report_file = f"reports/incident_round_{round_num}_{attack_event['vector'].lower()}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"    Report saved: {report_file}")
    print("="*80 + "\n")

def main():
    parser = argparse.ArgumentParser(description="SRE Colosseum Live Arena Runner")
    parser.add_argument("--rounds", type=int, default=3, help="Number of battle rounds to execute")
    parser.add_argument("--vector", type=str, default=None, help="Force specific chaos vector (e.g. MEMORY_LEAK_OOM, CASCADING_NETWORK_LATENCY)")
    parser.add_argument("--delay", type=int, default=5, help="Seconds to wait between rounds")
    args = parser.parse_args()

    print(r"""
   _____ _____  ______    _____ ____  _      ____   _____ _____ ______ _    _ __  __ 
  / ____|  __ \|  ____|  / ____/ __ \| |    / __ \ / ____/ ____|  ____| |  | |  \/  |
 | (___ | |__) | |__    | |   | |  | | |   | |  | | (___| (___ | |__  | |  | | \  / |
  \___ \|  _  /|  __|   | |   | |  | | |   | |  | |\___ \\___ \|  __| | |  | | |\/| |
  ____) | | \ \| |____  | |___| |__| | |___| |__| |____) |___) | |____| |__| | |  | |
 |_____/|_|  \_\______|  \_____\____/|______\____/|_____/_____/|______|\____/|_|  |_|
                                                                                      
             [+] Autonomous AI Red-vs-Blue SRE Chaos Arena on Kubernetes [+]
    """)

    for r in range(1, args.rounds + 1):
        run_battle_round(r, vector_override=args.vector)
        if r < args.rounds:
            print(f"[*] Cooling down for {args.delay} seconds before next round...")
            time.sleep(args.delay)

if __name__ == "__main__":
    main()
