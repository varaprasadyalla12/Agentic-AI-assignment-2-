"""
==============================================================================
QUESTION 3: SECURITY LOG & THREAT INTELLIGENCE AGENT
==============================================================================
Requirement:
  Create an agent that analyzes security logs/alerts, identifies potential threats,
  classifies severity, and suggests mitigation steps.

Features:
  - Multi-source log parsing: Linux auth.log (SSH), Web access logs (Nginx/Apache),
    AWS CloudTrail JSON
  - MITRE ATT&CK technique mapping (T1110, T1190, T1098, T1567, etc.)
  - CVSS severity classification: LOW, MEDIUM, HIGH, CRITICAL
  - Immediate containment & remediation generation (executable bash scripts,
    firewall rules, account locks, AWS CLI revocation)
  - Exports to outputs/question_3_security_incident_report.md and .json

Usage:
  python question_3_security_analyst.py
  python question_3_security_analyst.py --log "data/sample_logs/ssh_bruteforce.log"
  python question_3_security_analyst.py --all-samples
==============================================================================
"""

import os
import sys
import json
import argparse

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.security_analyst import SecurityAnalystAgent


def run_question_3(
    log_path: str = "data/sample_logs/ssh_bruteforce.log",
    output_dir: str = "outputs",
):
    print("=" * 80)
    print("  QUESTION 3: SECURITY LOG ANALYZER & THREAT INTELLIGENCE AGENT")
    print("=" * 80)
    print(f"[*] Target Log File : {log_path}\n")

    if not os.path.exists(log_path):
        print(f"[-] Error: Target log file not found at: {log_path}")
        sys.exit(1)

    agent = SecurityAnalystAgent()

    # Analyze security logs
    print(f"[*] Ingesting logs, detecting MITRE ATT&CK indicators, scoring severity...")
    result = agent.analyze_file(log_path)

    print("\n" + "-" * 80)
    print("INCIDENT ASSESSMENT & MITIGATION REPORT:")
    print("-" * 80)
    print(result.output)
    print("-" * 80)

    print("\n[*] Incident Summary:")
    print(f"    - Peak Severity         : {result.metadata.get('peak_severity')}")
    print(f"    - Total Threat Patterns : {result.metadata.get('threat_count')}")
    print(f"    - Log Records Processed : {result.metadata.get('total_logs')}")

    print(f"\n[*] Execution Step Trace ({len(result.steps)} steps):")
    for idx, step in enumerate(result.steps, 1):
        print(f"    Step {idx} [{step.action}]: {step.thoughts}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(log_path))[0]
    md_output_path = os.path.join(output_dir, f"question_3_security_{base_name}_report.md")
    main_md_path = os.path.join(output_dir, "question_3_security_incident_report.md")
    json_output_path = os.path.join(output_dir, "question_3_security_incident_report.json")

    # Save Markdown report
    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write(result.output)
    with open(main_md_path, "w", encoding="utf-8") as f:
        f.write(result.output)

    # Save JSON raw trace
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)

    print(f"\n[+] Outputs successfully saved to:")
    print(f"    - Markdown Report : {main_md_path}")
    print(f"    - JSON Trace      : {json_output_path}")
    print("=" * 80 + "\n")

    return result


def run_all_security_samples(output_dir: str = "outputs"):
    samples = [
        "data/sample_logs/ssh_bruteforce.log",
        "data/sample_logs/web_sqli_attack.log",
        "data/sample_logs/cloudtrail_suspicious.json",
    ]
    print("=" * 80)
    print("  RUNNING QUESTION 3 ACROSS ALL 3 SECURITY SCENARIOS")
    print("=" * 80)
    for sample in samples:
        if os.path.exists(sample):
            run_question_3(sample, output_dir=output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Question 3: Security Log & Threat Analyst Agent")
    parser.add_argument(
        "--log",
        "-l",
        default="data/sample_logs/ssh_bruteforce.log",
        help="Path to security log file",
    )
    parser.add_argument(
        "--all-samples",
        action="store_true",
        help="Run against all 3 sample logs (SSH, Web SQLi, CloudTrail)",
    )
    args = parser.parse_args()

    if args.all_samples:
        run_all_security_samples()
    else:
        run_question_3(log_path=args.log)
