"""
==============================================================================
QUESTION 4: COLLABORATIVE MULTI-AGENT SYSTEM
==============================================================================
Requirement:
  Build a system with 2–3 specialized agents (e.g., Research Agent, Analyst Agent,
  Report Agent) that collaborate to complete a given task automatically.

Specialized Agents:
  1. LeadResearchAgent   : Information discovery, factual synthesis, web investigation
  2. SeniorAnalystAgent  : Critical evaluation, risk assessment, SWOT analysis
  3. ExecutiveReportAgent: Strategic synthesis, executive deliverable formulation

Coordination Mechanism:
  - SharedBlackboard message bus tracking inter-agent dialogue, artifacts, and handoffs
  - 4-phase sequential collaborative workflow
  - Exports to outputs/question_4_multi_agent_collaboration.md and .json

Usage:
  python question_4_multi_agent.py
  python question_4_multi_agent.py --task "Autonomous Agent Governance and Safety in Production"
==============================================================================
"""

import os
import sys
import json
import argparse

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.multi_agent import MultiAgentOrchestrator


def run_question_4(
    task: str = "Evaluate the Impact of Agentic AI on Enterprise Cloud Security",
    output_dir: str = "outputs",
):
    print("=" * 80)
    print("  QUESTION 4: COLLABORATIVE MULTI-AGENT SYSTEM")
    print("=" * 80)
    print(f"[*] Collaborative Goal: '{task}'")
    print("[*] Participating Agents:")
    print("    1. LeadResearchAgent    (Domain Discovery & Evidence)")
    print("    2. SeniorAnalystAgent   (SWOT & Strategic Risk Critique)")
    print("    3. ExecutiveReportAgent (Actionable Executive Briefing)")
    print("[*] Coordination Architecture: Shared Blackboard Message Bus\n")

    orchestrator = MultiAgentOrchestrator()

    # Optional: live streaming listener
    def on_message(msg):
        print(f"[{msg.timestamp}] >>> [{msg.phase}] {msg.sender} -> {msg.recipient}:")
        print(f"    {msg.summary}\n")

    orchestrator.add_message_listener(on_message)

    print("-" * 80)
    print("INTER-AGENT COLLABORATION & HANDOFF STREAM:")
    print("-" * 80)
    result = orchestrator.run_collaborative_task(task)

    print("\n" + "=" * 80)
    print("FINAL MULTI-AGENT SYNTHESIZED DELIVERABLE:")
    print("=" * 80)
    print(result.output)
    print("=" * 80)

    print(f"\n[*] Total Collaborative Steps Executed : {len(result.steps)}")
    print(f"[*] Blackboard Inter-Agent Messages   : {len(result.metadata.get('dialogue', []))}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    md_output_path = os.path.join(output_dir, "question_4_multi_agent_collaboration.md")
    json_output_path = os.path.join(output_dir, "question_4_multi_agent_collaboration.json")

    # Generate Markdown documentation including the blackboard dialogue
    dialogue = result.metadata.get("dialogue", [])
    dialogue_md = ""
    for d in dialogue:
        dialogue_md += f"""### Phase: `{d['phase']}`
- **Sender**: `{d['sender']}`  
- **Recipient**: `{d['recipient']}`  
- **Summary**: {d['summary']}  

```markdown
{d['content'][:500] + ('...' if len(d['content']) > 500 else '')}
```

"""

    full_md = f"""# Question 4: Collaborative Multi-Agent System Report

- **Collaborative Goal**: {task}
- **Participating Agents**: LeadResearchAgent, SeniorAnalystAgent, ExecutiveReportAgent
- **Coordination Mechanism**: Shared Blackboard Message Bus

---

## 1. Inter-Agent Collaboration & Dialogue Stream

{dialogue_md}

---

## 2. Final Collaborative Executive Deliverable

{result.output}

---

## 3. End-to-End Execution Trace
"""
    for idx, step in enumerate(result.steps, 1):
        full_md += f"- **Step {idx} [{step.agent_name} - {step.action}]**: {step.thoughts}\n"

    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write(full_md)

    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)

    print(f"\n[+] Outputs successfully saved to:")
    print(f"    - Markdown Report : {md_output_path}")
    print(f"    - JSON Raw Trace  : {json_output_path}")
    print("=" * 80 + "\n")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Question 4: Collaborative Multi-Agent System")
    parser.add_argument(
        "--task",
        "-t",
        default="Evaluate the Impact of Agentic AI on Enterprise Cloud Security",
        help="Collaborative task for the 3 agents",
    )
    args = parser.parse_args()
    run_question_4(task=args.task)
