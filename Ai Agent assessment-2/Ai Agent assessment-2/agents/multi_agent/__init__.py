"""
Collaborative Multi-Agent Architecture (Requirement 4).
Coordinates specialized agents collaborating autonomously over a shared blackboard.
"""
from agents.multi_agent.blackboard import CollaborationMessage, SharedBlackboard
from agents.multi_agent.roles import (
    LeadResearchAgent,
    SeniorAnalystAgent,
    ExecutiveReportAgent,
)
from agents.multi_agent.orchestrator import MultiAgentOrchestrator

__all__ = [
    "CollaborationMessage",
    "SharedBlackboard",
    "LeadResearchAgent",
    "SeniorAnalystAgent",
    "ExecutiveReportAgent",
    "MultiAgentOrchestrator",
]
