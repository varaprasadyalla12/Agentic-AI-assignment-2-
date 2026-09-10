# Question 1: Document / PDF QA Agent Output

- **Target Document**: `data/sample_docs/agentic_ai_overview.pdf`
- **User Query**: What are the core pillars of agentic architecture?
- **Total Chunks Indexed**: 6
- **Retrieved Passages**: 3

---

## Agent Response

Based on the indexed documentation [Doc: agentic_ai_overview.pdf, Page: 1]:

Architectural Foundations of Agentic AI Systems
Technical Whitepaper - Version 2.4
1. Executive Summary
Autonomous Agentic AI systems represent an evolutionary leap from passive language models
to active decision-makers capable of perception, planning, tool usage, and memory retention. Modern agents operate via iterative reasoning loops such as ReAct (Reasoning + Acting),
evaluating intermediate observations to navigate dynamic, non-deterministic environments. 2. Core Pillars of Agentic Architecture
An agentic system relies upon four foundational subsystems:
1. Perception and Context Processing: Ingestion of multimodal prompts, environment state, and documents. 2. Planning and Decomposition: Breaking down complex objectives into directed acyclic task graphs. 3.

**Verified Citation**: [Doc: agentic_ai_overview.pdf, Page: 1]
**Confidence**: Grounded in official source text.

---

## Provenance & Citations
- Doc: agentic_ai_overview.pdf, Page: 1
- Doc: agentic_ai_overview.pdf, Page: 2
- Doc: agentic_ai_overview.pdf, Page: 3

---

## Retrieved Passages Used as Context

### Chunk #1 (Score: 0.7214) - [agentic_ai_overview.pdf, Page 1]
```
Architectural Foundations of Agentic AI Systems
Technical Whitepaper - Version 2.4
1. Executive Summary
Autonomous Agentic AI systems represent an evolutionary leap from passive language models
to active decision-makers capable of perception, planning, tool usage, and memory retention. Modern agents operate via iterative reasoning loops such as ReAct (Reasoning + Acting),
evaluating intermediate observations to navigate dynamic, non-deterministic environments. 2. Core Pillars of Agentic Architecture
An agentic system relies upon four foundational subsystems:
1. Perception and Context Processing: Ingestion of multimodal prompts, environment state, and documents. 2. Planning and Decomposition: Breaking down complex objectives into directed acyclic task graphs. 3.
```

### Chunk #2 (Score: 0.2926) - [agentic_ai_overview.pdf, Page 2]
```
Memory Systems and Multi-Agent Coordination
3. Memory Hierarchy in Production Agents
Agents utilize a dual-tiered memory architecture:
- Working Memory: Maintains immediate turn-by-turn conversational context and tool responses. - Semantic Episodic Memory: Vector stores (e.g. Chroma, FAISS, Milvus) that index past interactions. Experiments demonstrate that semantic retrieval reduces hallucination rates by up to 64% in QA. 4. Multi-Agent Collaboration Patterns
Complex enterprise objectives exceed the capabilities of single monolithic agents. Multi-agent patterns divide labor among specialized personas:
- Hierarchical Delegation: A Supervisor Agent plans and assigns tasks to subordinate workers. - Peer-to-Peer Consensus: Agents critique each others outputs via debate loops before finalizing.
```

### Chunk #3 (Score: 0.1677) - [agentic_ai_overview.pdf, Page 3]
```
Security, Safety, and Evaluation Metrics
5. Security Vectors in Agentic AI
Because agents possess tool-execution capabilities, they introduce new attack surfaces:
- Indirect Prompt Injection: Malicious instructions embedded within retrieved web pages or PDFs. - Privilege Escalation: Agents inadvertently running destructive bash commands or database drops. - Data Exfiltration: Attackers tricking agents into sending proprietary context to external endpoints. Mitigation requires Sandboxed Runtimes, Tool Execution Guardrails, and Human-in-the-Loop approvals. 6. Evaluation Frameworks
Evaluating agent performance requires multifaceted metrics:
- Task Completion Rate (TCR): Percentage of end-to-end tasks successfully executed without errors.
```

---

## Execution Step Trace
- **Step 1 (Query Analysis)**: Analyzing user question to extract key search semantics.
- **Step 2 (Hybrid Passage Retrieval)**: Retrieved top 3 relevant passages combining BM25 and n-gram similarity.
- **Step 3 (LLM Grounded Synthesis)**: Sending retrieved context and query to LLM with grounding instructions.
- **Step 4 (Verification & Final Answer)**: Verified citation tags and absence of hallucinations in synthesized response.
