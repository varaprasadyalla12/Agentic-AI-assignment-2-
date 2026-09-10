"""
Unit and Integration Tests for FastAPI Server Endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "DocQAAgent" in data["agents"]


def test_dashboard_ui_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "Applied Agentic AI" in response.text
    assert "Doc QA" in response.text


def test_api_doc_qa_ask():
    response = client.post("/api/doc-qa/ask", json={
        "query": "What are the core pillars of agentic architecture?",
        "top_k": 2
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "pillars" in data["output"].lower() or "architecture" in data["output"].lower()


def test_api_research_run():
    response = client.post("/api/research/run", json={
        "topic": "Agentic AI in Enterprise Cybersecurity",
        "sources": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "references" in data["metadata"]


def test_api_security_sample_and_analyze():
    sample_res = client.get("/api/security/sample/ssh")
    assert sample_res.status_code == 200
    sample_data = sample_res.json()
    assert "Failed password" in sample_data["content"]

    analyze_res = client.post("/api/security/analyze", json={
        "log_text": sample_data["content"][:600],
        "log_type": "ssh_sample.log"
    })
    assert analyze_res.status_code == 200
    analyze_data = analyze_res.json()
    assert analyze_data["success"] is True
    assert "CRITICAL" in analyze_data["output"] or "HIGH" in analyze_data["output"] or "Incident" in analyze_data["output"]


def test_api_multi_agent_collaborate():
    response = client.post("/api/multi-agent/collaborate", json={
        "task": "Evaluate the Impact of Agentic AI on Enterprise Cloud Security"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["metadata"]["dialogue"]) >= 4


def test_api_outputs_list():
    response = client.get("/api/outputs")
    assert response.status_code == 200
    data = response.json()
    assert "outputs" in data
    assert len(data["outputs"]) >= 4
