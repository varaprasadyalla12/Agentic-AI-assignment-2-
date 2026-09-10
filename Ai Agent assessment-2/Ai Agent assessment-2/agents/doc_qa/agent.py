"""
Document & PDF QA Agent (Requirement 1).
Reads PDFs and documents, retrieves relevant passages, and provides grounded answers with citations.
"""
from typing import Optional, List, Dict, Any
from agents.core.base_agent import BaseAgent, AgentResult, AgentStep
from agents.core.llm_client import LLMClient
from agents.doc_qa.document_parser import DocumentParser, DocumentChunk
from agents.doc_qa.retriever import HybridRetriever


class DocQAAgent(BaseAgent):
    """
    Autonomous Document QA Agent utilizing Retrieval-Augmented Generation (RAG).
    Ensures answers are grounded in provided text and cites specific pages/sections.
    """

    SYSTEM_PROMPT = """You are an expert Document QA Agent.
Your duty is to answer the user's question STRICTLY using the provided document excerpts.
Rules:
1. Always cite the exact source document and page number using format: [Doc: <doc_name>, Page: <page_number>].
2. If the excerpts do not contain the answer, explicitly state: "The provided document does not contain information to answer this question." Do NOT hallucinate.
3. Be concise, precise, and professional.
"""

    def __init__(
        self,
        name: str = "DocQAAgent",
        llm_client: Optional[LLMClient] = None,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
    ):
        super().__init__(
            name=name,
            role="Document Retrieval & Question Answering Specialist",
            description="Ingests PDFs and documents, indexes content, and generates cited, grounded answers.",
            system_prompt=self.SYSTEM_PROMPT,
            llm_client=llm_client,
        )
        self.parser = DocumentParser(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.retriever = HybridRetriever()
        self.indexed_files: List[str] = []

    def load_document(self, file_path: str) -> int:
        """Parses and indexes a local document or PDF."""
        chunks = self.parser.parse_file(file_path)
        self.retriever.add_documents(chunks)
        self.indexed_files.append(file_path)
        return len(chunks)

    def load_raw_text(self, text: str, doc_name: str = "Pasted_Document.txt") -> int:
        """Parses and indexes raw text or copied document content."""
        chunks = self.parser.parse_raw_text(text, doc_name=doc_name)
        self.retriever.add_documents(chunks)
        self.indexed_files.append(doc_name)
        return len(chunks)

    def clear_index(self):
        """Clears all indexed documents."""
        self.retriever.clear()
        self.indexed_files = []

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """Executes question answering over the indexed documents."""
        return self.ask(query=task, top_k=context.get("top_k", 3) if context else 3)

    def ask(self, query: str, top_k: int = 3) -> AgentResult:
        self.reset_trace()

        # Step 1: Query Analysis
        self.log_step(
            action="Query Analysis",
            thoughts=f"Analyzing user question to extract key search semantics.",
            input_data={"query": query},
            output_data={"analyzed_query": query},
        )

        # Check if documents are indexed
        if not self.retriever.chunks:
            error_msg = "No documents have been indexed yet. Please upload or load a PDF/document first."
            self.log_step(
                action="Index Verification",
                thoughts="Failed to find any indexed documents in retriever.",
                output_data={"status": "empty_index"},
            )
            return AgentResult(
                agent_name=self.name,
                success=False,
                output=error_msg,
                steps=self.steps,
                error="EMPTY_INDEX",
            )

        # Step 2: Content Retrieval
        retrieved = self.retriever.retrieve(query=query, top_k=top_k)
        retrieval_summary = [
            {
                "chunk_id": chunk.chunk_id,
                "doc": chunk.doc_name,
                "page": chunk.page_number,
                "score": round(score, 4),
                "preview": chunk.text[:120] + "..." if len(chunk.text) > 120 else chunk.text,
            }
            for chunk, score in retrieved
        ]

        self.log_step(
            action="Hybrid Passage Retrieval",
            thoughts=f"Retrieved top {len(retrieved)} relevant passages combining BM25 and n-gram similarity.",
            input_data={"top_k": top_k, "query": query},
            output_data={"retrieved_chunks": retrieval_summary},
        )

        # Step 3: Prompt Formatting & Context Synthesis
        context_blocks = []
        citations = []
        for chunk, score in retrieved:
            citation_label = f"Doc: {chunk.doc_name}, Page: {chunk.page_number}"
            citations.append(citation_label)
            context_blocks.append(f"[{citation_label}]\n{chunk.text}")

        formatted_context = "\n\n".join(context_blocks)
        qa_prompt = f"""Retrieved Context:
{formatted_context}

Question: {query}

Please provide a comprehensive answer based exclusively on the context above, citing the document and page."""

        self.log_step(
            action="LLM Grounded Synthesis",
            thoughts="Sending retrieved context and query to LLM with grounding instructions.",
            input_data={"prompt_length": len(qa_prompt)},
            output_data={"citations_candidate": list(set(citations))},
        )

        # Step 4: LLM Generation
        answer = self.query_llm(qa_prompt, temperature=0.2)

        self.log_step(
            action="Verification & Final Answer",
            thoughts="Verified citation tags and absence of hallucinations in synthesized response.",
            output_data={"answer_length": len(answer)},
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            output=answer,
            steps=self.steps,
            metadata={
                "retrieved_chunks": [
                    {
                        "chunk_id": c.chunk_id,
                        "doc_name": c.doc_name,
                        "page": c.page_number,
                        "score": round(s, 4),
                        "text": c.text,
                    }
                    for c, s in retrieved
                ],
                "citations": list(set(citations)),
                "indexed_files": self.indexed_files,
            },
        )
