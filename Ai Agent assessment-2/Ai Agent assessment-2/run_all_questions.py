"""
==============================================================================
MASTER RUNNER: APPLIED AGENTIC AI - CODING ASSIGNMENT 2
==============================================================================
Runs any or all 4 questions sequentially, displays full terminal output,
and writes structured outputs directly to the `outputs/` directory.

Questions:
  1. Document / PDF QA Agent
  2. Autonomous Research Agent
  3. Security Log & Threat Analyst Agent
  4. Collaborative Multi-Agent System (3 Agents)

Usage:
  python run_all_questions.py --all
  python run_all_questions.py --question 1
  python run_all_questions.py --question 2
  python run_all_questions.py --question 3
  python run_all_questions.py --question 4
==============================================================================
"""

import sys
import os
import argparse
import time

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from question_1_doc_qa import run_question_1
from question_2_research_agent import run_question_2
from question_3_security_analyst import run_question_3
from question_4_multi_agent import run_question_4


def main():
    parser = argparse.ArgumentParser(
        description="Run Applied Agentic AI Assignment 2 Solutions arranged per question.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--question",
        "-q",
        choices=["1", "2", "3", "4", "all"],
        default="all",
        help="Specify which question to execute (1, 2, 3, 4, or all). Default is all.",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Run all 4 questions sequentially.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="outputs",
        help="Directory to save generated outputs (default: outputs)",
    )

    args = parser.parse_args()
    selected_question = "all" if args.all else args.question

    print("\n" + "#" * 80)
    print("      APPLIED AGENTIC AI - CODING ASSIGNMENT 2 MASTER RUNNER")
    print("#" * 80 + "\n")

    start_time = time.time()
    results = {}

    if selected_question in ["1", "all"]:
        print("\n>>> EXECUTING QUESTION 1...")
        results["Question 1"] = run_question_1(output_dir=args.output_dir)

    if selected_question in ["2", "all"]:
        print("\n>>> EXECUTING QUESTION 2...")
        results["Question 2"] = run_question_2(output_dir=args.output_dir)

    if selected_question in ["3", "all"]:
        print("\n>>> EXECUTING QUESTION 3...")
        results["Question 3"] = run_question_3(output_dir=args.output_dir)

    if selected_question in ["4", "all"]:
        print("\n>>> EXECUTING QUESTION 4...")
        results["Question 4"] = run_question_4(output_dir=args.output_dir)

    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("                    EXECUTION SUMMARY")
    print("=" * 80)
    for q_name, res in results.items():
        status = "[SUCCESS]" if res.success else "[FAILED]"
        print(f"  {status} {q_name}: {res.agent_name} ({len(res.steps)} steps)")

    print(f"\n[+] Total Time Elapsed : {elapsed:.2f} seconds")
    print(f"[+] Output Directory   : {os.path.abspath(args.output_dir)}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
