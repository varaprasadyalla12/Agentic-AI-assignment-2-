"""
Unit and Integration Tests for Question 2: Autonomous Research Agent.
"""
import pytest
from agents.researcher import ResearchAgent
from agents.researcher.search_tools import SearchTool


def test_search_tool_retrieval():
    tool = SearchTool(use_live=False)  # Test with deterministic curated knowledge
    results = tool.search("Agentic AI and LLM workflows", max_results=3)
    assert len(results) >= 1
    assert hasattr(results[0], "title")
    assert hasattr(results[0], "url")
    assert hasattr(results[0], "snippet")


def test_research_agent_execution():
    agent = ResearchAgent(use_live_search=False)
    result = agent.research(topic="Emerging Trends in Autonomous Systems", max_sources=3)

    assert result.success is True
    assert "Executive Summary" in result.output or "Autonomous" in result.output
    assert len(result.steps) >= 3
    assert "references" in result.metadata
    assert len(result.metadata["references"]) >= 1
    assert "html_export" in result.metadata
