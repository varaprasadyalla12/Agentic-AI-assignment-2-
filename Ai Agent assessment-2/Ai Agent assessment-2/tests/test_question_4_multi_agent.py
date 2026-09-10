"""
Unit and Integration Tests for Question 4: Collaborative Multi-Agent System.
"""
import pytest
from agents.multi_agent.blackboard import SharedBlackboard
from agents.multi_agent.orchestrator import MultiAgentOrchestrator


def test_shared_blackboard_messaging():
    board = SharedBlackboard()
    board.init_task("Sample Goal")
    msg = board.post_message(
        sender="AgentA",
        recipient="AgentB",
        phase="Phase1",
        content="Here is data",
        summary="Data shared",
    )
    assert msg.sender == "AgentA"
    assert msg.recipient == "AgentB"
    assert len(board.get_all_messages()) == 1

    board.store_artifact("key1", {"metric": 42})
    assert board.get_artifact("key1") == {"metric": 42}


def test_multi_agent_orchestrator_collaboration():
    orchestrator = MultiAgentOrchestrator()
    goal = "Assess Autonomous Agent Safety in Financial Transactions"

    recorded_messages = []
    orchestrator.add_message_listener(lambda m: recorded_messages.append(m))

    result = orchestrator.run_collaborative_task(goal)

    assert result.success is True
    assert len(recorded_messages) >= 3
    assert len(result.steps) >= 5
    assert "dialogue" in result.metadata
    assert len(result.metadata["dialogue"]) >= 4

    # Verify all 3 agents participated
    senders = [m["sender"] for m in result.metadata["dialogue"]]
    assert "ResearchAgent" in senders
    assert "AnalystAgent" in senders
    assert "ReportAgent" in senders
