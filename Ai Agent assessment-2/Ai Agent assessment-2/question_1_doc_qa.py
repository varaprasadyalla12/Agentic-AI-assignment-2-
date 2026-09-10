"""
==============================================================================
QUESTION 1: DOCUMENT / PDF QA AGENT
==============================================================================
Requirement:
  Build an agent that reads PDFs/documents, retrieves relevant content,
  and answers user queries using an LLM.

Features:
  - PDF & Text Document Ingestion (pypdf + chunking with overlap)
  - Hybrid BM25 & Semantic n-gram passage retrieval
  - Grounded QA with page and source citations: [Doc: <name>, Page: <page>]
  - Hallucination prevention: answers strictly from retrieved context
  - Exports output to outputs/question_1_doc_qa_output.md and .json

Usage:
  python question_1_doc_qa.py
  python question_1_doc_qa.py --file "data/sample_docs/agentic_ai_overview.pdf" --query "What are the core pillars of agentic architecture?"
==============================================================================
"""

import os
import sys
import json
import argparse

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.doc_qa import DocQAAgent


def run_question_1(
    file_path: str = "data/sample_docs/agentic_ai_overview.pdf",
    query: str = "What are the core pillars of agentic architecture?",
    top_k: int = 3,
    output_dir: str = "outputs",
):
    print("=" * 80)
    print("  QUESTION 1: DOCUMENT / PDF RETRIEVAL & QUESTION ANSWERING AGENT")
    print("=" * 80)
    print(f"[*] Target Document : {file_path}")
    print(f"[*] User Query      : {query}")
    print(f"[*] Top-K Passages  : {top_k}\n")

    if not os.path.exists(file_path):
        print(f"[-] Error: Target file not found at: {file_path}")
        sys.exit(1)

    agent = DocQAAgent()

    # Step 1: Ingest Document
    print(f"[*] Parsing and indexing document: {file_path} ...")
    num_chunks = agent.load_document(file_path)
    print(f"[+] Document successfully indexed into {num_chunks} text chunks.\n")

    # Step 2: Execute Grounded QA
    print(f"[*] Executing Hybrid Retrieval & Grounded LLM Synthesis...")
    result = agent.ask(query=query, top_k=top_k)

    print("\n" + "-" * 80)
    print("AGENT ANSWER (GROUNDED WITH CITATIONS):")
    print("-" * 80)
    print(result.output)
    print("-" * 80)

    print("\n[*] Citations Extracted:")
    citations = result.metadata.get("citations", [])
    for c in citations:
        print(f"    - {c}")

    print(f"\n[*] Execution Step Trace ({len(result.steps)} steps):")
    for idx, step in enumerate(result.steps, 1):
        print(f"    Step {idx} [{step.action}]: {step.thoughts}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    md_output_path = os.path.join(output_dir, "question_1_doc_qa_output.md")
    json_output_path = os.path.join(output_dir, "question_1_doc_qa_output.json")

    # Save Markdown Report
    md_content = f"""# Question 1: Document / PDF QA Agent Output

- **Target Document**: `{file_path}`
- **User Query**: {query}
- **Total Chunks Indexed**: {num_chunks}
- **Retrieved Passages**: {top_k}

---

## Agent Response

{result.output}

---

## Provenance & Citations
{chr(10).join(f"- {c}" for c in citations)}

---

## Retrieved Passages Used as Context

"""
    for idx, chunk in enumerate(result.metadata.get("retrieved_chunks", []), 1):
        md_content += f"""### Chunk #{idx} (Score: {chunk['score']}) - [{chunk['doc_name']}, Page {chunk['page']}]
```
{chunk['text']}
```

"""

    md_content += f"""---

## Execution Step Trace
"""
    for idx, step in enumerate(result.steps, 1):
        md_content += f"- **Step {idx} ({step.action})**: {step.thoughts}\n"

    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)

    print(f"\n[+] Outputs successfully saved to:")
    print(f"    - Markdown : {md_output_path}")
    print(f"    - JSON Raw : {json_output_path}")
    print("=" * 80 + "\n")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Question 1: Document / PDF QA Agent")
    parser.add_argument(
        "--file",
        "-f",
        default="data/sample_docs/agentic_ai_overview.pdf",
        help="Path to PDF or document file",
    )
    parser.add_argument(
        "--query",
        "-q",
        default="What are the core pillars of agentic architecture?",
        help="Question to ask about the document",
    )
    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=3,
        help="Number of chunks to retrieve",
    )
    args = parser.parse_args()
    run_question_1(file_path=args.file, query=args.query, top_k=args.top_k)
