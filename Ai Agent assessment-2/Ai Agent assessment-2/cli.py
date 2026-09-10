"""
Unified Command-Line Interface (CLI) for Applied Agentic AI Assignment 2.
Supports running all 4 agents directly from the terminal.

Usage:
  python cli.py doc-qa --file <path> --query "Your question"
  python cli.py research --topic "Your topic"
  python cli.py security --log <path>
  python cli.py multi-agent --task "Your goal"
"""
import argparse
import sys
import os
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.doc_qa import DocQAAgent
from agents.researcher import ResearchAgent
from agents.security_analyst import SecurityAnalystAgent
from agents.multi_agent import MultiAgentOrchestrator


def print_banner():
    print("=" * 70)
    print("       APPLIED AGENTIC AI - ASSIGNMENT 2 MULTI-AGENT SUITE        ")
    print("=" * 70)


def cmd_doc_qa(args):
    print_banner()
    print(f"[*] Initializing Document & PDF QA Agent (Requirement 1)...")
    agent = DocQAAgent()

    file_path = args.file or "data/sample_docs/agentic_ai_overview.pdf"
    if not os.path.exists(file_path):
        print(f"[-] Error: Document file not found: {file_path}")
        sys.exit(1)

    print(f"[*] Ingesting and indexing: {file_path}")
    num_chunks = agent.load_document(file_path)
    print(f"[+] Successfully indexed {num_chunks} document chunks.")

    query = args.query or "What are the core pillars of agentic architecture?"
    print(f"[*] Processing Query: '{query}'\n")

    result = agent.ask(query, top_k=args.top_k)
    print("-" * 50)
    print("AGENT RESPONSE:")
    print("-" * 50)
    print(result.output)
    print("-" * 50)
    print(f"Citations: {result.metadata.get('citations', [])}")
    print(f"Execution Steps: {len(result.steps)}")


def cmd_research(args):
    print_banner()
    topic = args.topic or "Emerging Trends in Agentic AI and Autonomous Systems"
    print(f"[*] Initializing Autonomous Research Agent (Requirement 2)...")
    print(f"[*] Investigating Topic: '{topic}'\n")

    agent = ResearchAgent()
    result = agent.research(topic=topic, max_sources=args.sources)

    print("-" * 50)
    print("STRUCTURED RESEARCH REPORT:")
    print("-" * 50)
    print(result.output)
    print("-" * 50)
    print(f"[+] Total References Compiled: {len(result.metadata.get('references', []))}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result.output)
        print(f"[+] Saved report to: {args.output}")


def cmd_security(args):
    print_banner()
    log_path = args.log or "data/sample_logs/ssh_bruteforce.log"
    if not os.path.exists(log_path):
        print(f"[-] Error: Log file not found: {log_path}")
        sys.exit(1)

    print(f"[*] Initializing Security Log & Threat Intelligence Agent (Requirement 3)...")
    print(f"[*] Analyzing Log Source: {log_path}\n")

    agent = SecurityAnalystAgent()
    result = agent.analyze_file(log_path)

    print("-" * 50)
    print("INCIDENT ASSESSMENT & MITIGATION REPORT:")
    print("-" * 50)
    print(result.output)
    print("-" * 50)
    print(f"[+] Peak Threat Severity: {result.metadata.get('peak_severity')}")
    print(f"[+] Total Threats Detected: {result.metadata.get('threat_count')}")


def cmd_multi_agent(args):
    print_banner()
    task = args.task or "Evaluate the Impact of Agentic AI on Enterprise Cloud Security"
    print(f"[*] Initializing Collaborative Multi-Agent System (Requirement 4)...")
    print(f"[*] Collaborative Goal: '{task}'")
    print("[*] Coordinating 3 Specialized Agents: ResearchAgent -> AnalystAgent -> ReportAgent\n")

    orchestrator = MultiAgentOrchestrator()
    result = orchestrator.run_collaborative_task(task)

    print("\n" + "=" * 50)
    print("COLLABORATIVE DIALOGUE & HANDOFFS:")
    print("=" * 50)
    for msg in result.metadata.get("dialogue", []):
        print(f"[{msg['phase']}] {msg['sender']} -> {msg['recipient']}:")
        print(f"  {msg['summary']}\n")

    print("=" * 50)
    print("FINAL EXECUTIVE DELIVERABLE:")
    print("=" * 50)
    print(result.output)
    print("=" * 50)
    print(f"[+] Total Collaborative Execution Steps: {len(result.steps)}")


def cmd_all(args):
    from run_all_questions import run_question_1, run_question_2, run_question_3, run_question_4
    print_banner()
    print("[*] Running all 4 questions sequentially...\n")
    run_question_1(output_dir=args.output_dir)
    run_question_2(output_dir=args.output_dir)
    run_question_3(output_dir=args.output_dir)
    run_question_4(output_dir=args.output_dir)
    print("\n[+] All 4 questions executed successfully.")


def cmd_server(args):
    import uvicorn
    print_banner()
    print(f"[*] Starting Web Dashboard & API Server at http://{args.host}:{args.port}")
    uvicorn.run("api.server:app", host=args.host, port=args.port)


def main():
    parser = argparse.ArgumentParser(
        description="Applied Agentic AI Assignment 2 - Unified Multi-Agent Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Agent Command")

    # 1. Doc QA
    p_doc = subparsers.add_parser("doc-qa", help="Run Document & PDF QA Agent (Req 1)")
    p_doc.add_argument("--file", "-f", help="Path to PDF or document file (default: sample PDF)")
    p_doc.add_argument("--query", "-q", help="Question to ask about the document")
    p_doc.add_argument("--top-k", "-k", type=int, default=3, help="Number of chunks to retrieve (default: 3)")
    p_doc.set_defaults(func=cmd_doc_qa)

    # 2. Research
    p_res = subparsers.add_parser("research", help="Run Autonomous Research Agent (Req 2)")
    p_res.add_argument("--topic", "-t", help="Research topic or question")
    p_res.add_argument("--sources", "-s", type=int, default=4, help="Maximum sources to investigate (default: 4)")
    p_res.add_argument("--output", "-o", help="Optional path to save markdown report")
    p_res.set_defaults(func=cmd_research)

    # 3. Security
    p_sec = subparsers.add_parser("security", help="Run Security Log & Threat Analyst Agent (Req 3)")
    p_sec.add_argument("--log", "-l", help="Path to security log file (SSH, Web, or CloudTrail)")
    p_sec.set_defaults(func=cmd_security)

    # 4. Multi-Agent
    p_multi = subparsers.add_parser("multi-agent", help="Run Collaborative Multi-Agent System (Req 4)")
    p_multi.add_argument("--task", "-g", help="High-level goal for the 3 agents to complete")
    p_multi.set_defaults(func=cmd_multi_agent)

    # 5. All
    p_all = subparsers.add_parser("all", help="Execute all 4 questions sequentially")
    p_all.add_argument("--output-dir", "-o", default="outputs", help="Directory to save generated outputs")
    p_all.set_defaults(func=cmd_all)

    # 6. Server
    p_srv = subparsers.add_parser("server", help="Launch interactive Web Dashboard & API Server")
    p_srv.add_argument("--host", default="127.0.0.1", help="Host address to bind to")
    p_srv.add_argument("--port", "-p", type=int, default=8000, help="Port to listen on")
    p_srv.set_defaults(func=cmd_server)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
