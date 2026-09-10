"""
Unit and Integration Tests for Question 1: Document / PDF QA Agent.
"""
import os
import pytest
from agents.doc_qa import DocQAAgent
from agents.doc_qa.document_parser import DocumentParser


def test_document_parser_text():
    parser = DocumentParser(chunk_size=100, chunk_overlap=20)
    raw_text = "Machine learning is a subset of artificial intelligence. " * 10
    chunks = parser.parse_raw_text(raw_text, doc_name="test_doc.txt")
    assert len(chunks) > 1
    assert chunks[0].doc_name == "test_doc.txt"
    assert chunks[0].page_number == 1


def test_document_parser_pdf():
    pdf_path = "data/sample_docs/agentic_ai_overview.pdf"
    assert os.path.exists(pdf_path), "Sample PDF must exist"
    parser = DocumentParser(chunk_size=300, chunk_overlap=50)
    chunks = parser.parse_file(pdf_path)
    assert len(chunks) >= 3
    assert any(c.page_number == 1 for c in chunks)


def test_doc_qa_agent_ingestion_and_ask():
    agent = DocQAAgent()
    sample_txt = (
        "Agentic Architecture Overview.\n"
        "The core pillars of agentic AI systems are Planning, Memory, Tools, and Reflection.\n"
        "Planning breaks complex goals into tasks. Memory stores past state.\n"
        "Tools allow external actions. Reflection evaluates intermediate outputs."
    )
    num_chunks = agent.load_raw_text(sample_txt, doc_name="architecture_doc.txt")
    assert num_chunks >= 1

    result = agent.ask("What are the core pillars of agentic architecture?", top_k=2)
    assert result.success is True
    assert len(result.steps) >= 3
    assert "Planning" in result.output or "pillars" in result.output
    assert len(result.metadata["citations"]) > 0


def test_doc_qa_empty_index():
    agent = DocQAAgent()
    result = agent.ask("Any question?")
    assert result.success is False
    assert result.error == "EMPTY_INDEX"
