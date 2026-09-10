"""
==============================================================================
QUESTION 2: AUTONOMOUS RESEARCH AGENT
==============================================================================
Requirement:
  Develop an agent that searches for information, summarizes findings,
  and generates a structured research report with references.

Features:
  - Multi-query formulation and web search (DuckDuckGo ddgs + fallback)
  - Fact extraction and cross-source evidence synthesis
  - Comprehensive report generation with Executive Summary, Breakthroughs,
    Architectural Implications, and Strategic Challenges
  - Formal bibliography / reference list compilation
  - Exports to outputs/question_2_research_report.md, .html, and .json

Usage:
  python question_2_research_agent.py
  python question_2_research_agent.py --topic "Agentic AI in Enterprise Cybersecurity" --sources 5
==============================================================================
"""

import os
import sys
import json
import argparse

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.researcher import ResearchAgent


def run_question_2(
    topic: str = "Emerging Trends in Agentic AI and Autonomous Systems",
    sources: int = 4,
    output_dir: str = "outputs",
):
    print("=" * 80)
    print("  QUESTION 2: AUTONOMOUS RESEARCH & STRUCTURED REPORT AGENT")
    print("=" * 80)
    print(f"[*] Research Topic    : {topic}")
    print(f"[*] Max Web Sources   : {sources}\n")

    agent = ResearchAgent()

    # Execute Autonomous Research
    print(f"[*] Gathering multi-source intelligence & synthesizing report...")
    result = agent.research(topic=topic, max_sources=sources)

    print("\n" + "-" * 80)
    print("STRUCTURED RESEARCH REPORT GENERATED:")
    print("-" * 80)
    print(result.output)
    print("-" * 80)

    print("\n[*] Compiled References:")
    references = result.metadata.get("references", [])
    for ref in references:
        print(f"    [{ref['index']}] {ref['title']} - {ref['url']} ({ref['source']})")

    print(f"\n[*] Execution Step Trace ({len(result.steps)} steps):")
    for idx, step in enumerate(result.steps, 1):
        print(f"    Step {idx} [{step.action}]: {step.thoughts}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    md_output_path = os.path.join(output_dir, "question_2_research_report.md")
    html_output_path = os.path.join(output_dir, "question_2_research_report.html")
    json_output_path = os.path.join(output_dir, "question_2_research_report.json")

    # Save Markdown report
    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write(result.output)

    # Save HTML report
    html_content = result.metadata.get("html_export", "")
    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Save JSON raw trace
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)

    print(f"\n[+] Outputs successfully saved to:")
    print(f"    - Markdown Report : {md_output_path}")
    print(f"    - HTML Report     : {html_output_path}")
    print(f"    - JSON Trace      : {json_output_path}")
    print("=" * 80 + "\n")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Question 2: Autonomous Research Agent")
    parser.add_argument(
        "--topic",
        "-t",
        default="Emerging Trends in Agentic AI and Autonomous Systems",
        help="Research topic or question",
    )
    parser.add_argument(
        "--sources",
        "-s",
        type=int,
        default=4,
        help="Maximum sources to investigate",
    )
    args = parser.parse_args()
    run_question_2(topic=args.topic, sources=args.sources)
