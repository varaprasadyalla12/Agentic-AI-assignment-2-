"""
Utility to generate a valid multi-page PDF document for testing the Document QA Agent.
Uses pure Python standard PDF 1.4 syntax with no external dependencies required.
"""
import os

def create_pdf(filename: str, pages_content: list[list[str]]):
    objects = []
    offsets = []
    
    def add_object(content: bytes) -> int:
        offsets.append(current_offset[0])
        obj_num = len(offsets)
        obj_data = f"{obj_num} 0 obj\n".encode("latin1") + content + b"\nendobj\n"
        objects.append(obj_data)
        current_offset[0] += len(obj_data)
        return obj_num

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    current_offset = [len(header)]
    
    # 1. Font Object
    font_obj_num = 1
    font_data = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    offsets.append(current_offset[0])
    obj_data = f"{font_obj_num} 0 obj\n".encode("latin1") + font_data + b"\nendobj\n"
    objects.append(obj_data)
    current_offset[0] += len(obj_data)
    
    page_obj_nums = []
    content_obj_nums = []
    
    # Pre-calculate numbers
    # obj 1: font
    # obj 2: pages catalog
    # obj 3..3+N-1: page objects
    # obj 3+N..3+2N-1: content stream objects
    # obj 3+2N: catalog root
    num_pages = len(pages_content)
    
    # We will define pages catalog as obj 2
    pages_cat_num = 2
    offsets.append(0) # placeholder
    objects.append(b"") # placeholder
    
    for i, page_lines in enumerate(pages_content):
        # Create text stream
        stream_cmds = ["BT", "/F1 12 Tf", "50 750 Td", "16 TL"]
        for line in page_lines:
            # Escape parenthesis
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            if line.startswith("# "):
                stream_cmds.append(f"/F1 18 Tf ({escaped[2:]}) Tj T* /F1 12 Tf")
            elif line.startswith("## "):
                stream_cmds.append(f"/F1 14 Tf ({escaped[3:]}) Tj T* /F1 12 Tf")
            elif line == "":
                stream_cmds.append("T*")
            else:
                stream_cmds.append(f"({escaped}) Tj T*")
        stream_cmds.append("ET")
        stream_body = "\n".join(stream_cmds).encode("latin1")
        stream_obj = f"<< /Length {len(stream_body)} >>\nstream\n".encode("latin1") + stream_body + b"\nendstream"
        
        c_num = add_object(stream_obj)
        content_obj_nums.append(c_num)

    for i in range(num_pages):
        page_data = (
            f"<< /Type /Page /Parent {pages_cat_num} 0 R "
            f"/MediaBox [0 0 612 792] "
            f"/Contents {content_obj_nums[i]} 0 R "
            f"/Resources << /Font << /F1 {font_obj_num} 0 R >> >> >>"
        ).encode("latin1")
        p_num = add_object(page_data)
        page_obj_nums.append(p_num)
        
    # Now fill in obj 2 (Pages catalog)
    kids_str = " ".join(f"{p} 0 R" for p in page_obj_nums)
    pages_cat_data = f"<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>".encode("latin1")
    cat_obj_bytes = f"{pages_cat_num} 0 obj\n".encode("latin1") + pages_cat_data + b"\nendobj\n"
    
    # Recalculate offsets properly
    final_objects = [objects[0]] # font
    final_objects.append(cat_obj_bytes) # pages catalog
    for obj in objects[2:]:
        final_objects.append(obj)
        
    # Root Catalog
    root_obj_num = len(final_objects) + 1
    root_data = f"<< /Type /Catalog /Pages {pages_cat_num} 0 R >>".encode("latin1")
    root_obj_bytes = f"{root_obj_num} 0 obj\n".encode("latin1") + root_data + b"\nendobj\n"
    final_objects.append(root_obj_bytes)
    
    # Rebuild offset table from scratch
    recomputed_offsets = []
    curr = len(header)
    for obj in final_objects:
        recomputed_offsets.append(curr)
        curr += len(obj)
        
    xref_offset = curr
    xref = [f"xref\n0 {len(final_objects) + 1}\n0000000000 65535 f \n"]
    for off in recomputed_offsets:
        xref.append(f"{off:010d} 00000 n \n")
        
    trailer = (
        f"trailer\n<< /Size {len(final_objects) + 1} /Root {root_obj_num} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )
    
    full_pdf = header + b"".join(final_objects) + "".join(xref).encode("latin1") + trailer.encode("latin1")
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    with open(filename, "wb") as f:
        f.write(full_pdf)
    print(f"Generated PDF successfully: {filename} ({len(full_pdf)} bytes, {num_pages} pages)")

if __name__ == "__main__":
    pages = [
        [
            "# Architectural Foundations of Agentic AI Systems",
            "Technical Whitepaper - Version 2.4",
            "",
            "## 1. Executive Summary",
            "Autonomous Agentic AI systems represent an evolutionary leap from passive language models",
            "to active decision-makers capable of perception, planning, tool usage, and memory retention.",
            "Modern agents operate via iterative reasoning loops such as ReAct (Reasoning + Acting),",
            "evaluating intermediate observations to navigate dynamic, non-deterministic environments.",
            "",
            "## 2. Core Pillars of Agentic Architecture",
            "An agentic system relies upon four foundational subsystems:",
            "1. Perception and Context Processing: Ingestion of multimodal prompts, environment state, and documents.",
            "2. Planning and Decomposition: Breaking down complex objectives into directed acyclic task graphs.",
            "3. Tool Integration: Executing deterministic APIs, bash terminals, web search, and vector databases.",
            "4. Memory Systems: Short-term episodic context windows combined with long-term semantic stores."
        ],
        [
            "# Memory Systems and Multi-Agent Coordination",
            "",
            "## 3. Memory Hierarchy in Production Agents",
            "Agents utilize a dual-tiered memory architecture:",
            "- Working Memory: Maintains immediate turn-by-turn conversational context and tool responses.",
            "- Semantic Episodic Memory: Vector stores (e.g. Chroma, FAISS, Milvus) that index past interactions.",
            "Experiments demonstrate that semantic retrieval reduces hallucination rates by up to 64% in QA.",
            "",
            "## 4. Multi-Agent Collaboration Patterns",
            "Complex enterprise objectives exceed the capabilities of single monolithic agents.",
            "Multi-agent patterns divide labor among specialized personas:",
            "- Hierarchical Delegation: A Supervisor Agent plans and assigns tasks to subordinate workers.",
            "- Peer-to-Peer Consensus: Agents critique each others outputs via debate loops before finalizing.",
            "- Blackboard Architecture: Specialized agents post partial solutions to a shared message board.",
            "In benchmark tests, three collaborating agents (Researcher, Analyst, Reporter) achieved a 42%",
            "higher fact-verification score than a single zero-shot prompt."
        ],
        [
            "# Security, Safety, and Evaluation Metrics",
            "",
            "## 5. Security Vectors in Agentic AI",
            "Because agents possess tool-execution capabilities, they introduce new attack surfaces:",
            "- Indirect Prompt Injection: Malicious instructions embedded within retrieved web pages or PDFs.",
            "- Privilege Escalation: Agents inadvertently running destructive bash commands or database drops.",
            "- Data Exfiltration: Attackers tricking agents into sending proprietary context to external endpoints.",
            "Mitigation requires Sandboxed Runtimes, Tool Execution Guardrails, and Human-in-the-Loop approvals.",
            "",
            "## 6. Evaluation Frameworks",
            "Evaluating agent performance requires multifaceted metrics:",
            "- Task Completion Rate (TCR): Percentage of end-to-end tasks successfully executed without errors.",
            "- Retrieval Precision@K: Ground truth relevance of chunks surfaced during RAG operations.",
            "- Tool Call Efficiency: Ratio of necessary tool invocations versus redundant retry loops."
        ]
    ]
    pdf_path = os.path.join(os.path.dirname(__file__), "agentic_ai_overview.pdf")
    create_pdf(pdf_path, pages)
