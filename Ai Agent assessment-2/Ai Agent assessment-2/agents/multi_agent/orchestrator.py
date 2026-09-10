"""
Multi-Agent Orchestrator (Requirement 4).
Coordinates the specialized collaboration workflow between Research, Analyst, and Report Agents.
"""
from typing import Optional, Dict, Any, List, Callable
from agents.core.base_agent import AgentResult, AgentStep
from agents.core.llm_client import LLMClient
from agents.multi_agent.blackboard import SharedBlackboard, CollaborationMessage
from agents.multi_agent.roles import (
    LeadResearchAgent,
    SeniorAnalystAgent,
    ExecutiveReportAgent,
)


class MultiAgentOrchestrator:
    """
    Coordinates end-to-end multi-agent problem solving.
    Orchestrates the pipeline:
      User Goal -> Research Agent -> Analyst Agent -> Report Agent -> Final Deliverable.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client
        self.blackboard = SharedBlackboard()
        self.researcher = LeadResearchAgent(llm_client=llm_client)
        self.analyst = SeniorAnalystAgent(llm_client=llm_client)
        self.reporter = ExecutiveReportAgent(llm_client=llm_client)
        self._message_listeners: List[Callable[[CollaborationMessage], None]] = []

    def add_message_listener(self, listener: Callable[[CollaborationMessage], None]):
        self._message_listeners.append(listener)

    def _broadcast(self, msg: CollaborationMessage):
        for listener in self._message_listeners:
            try:
                listener(msg)
            except Exception:
                pass

    def run_collaborative_task(self, goal: str) -> AgentResult:
        """
        Executes the autonomous multi-agent pipeline with step-by-step handoffs.
        """
        self.blackboard.init_task(goal)
        all_steps: List[AgentStep] = []

        # -------------------------------------------------------------
        # Phase 1: Task Scoping & Delegation
        # -------------------------------------------------------------
        msg1 = self.blackboard.post_message(
            sender="Coordinator",
            recipient="ResearchAgent",
            phase="Delegation",
            content=f"Delegating objective '{goal}' to Lead Research Agent for factual exploration and evidence gathering.",
            summary=f"Task delegated to ResearchAgent: {goal}",
        )
        self._broadcast(msg1)

        # -------------------------------------------------------------
        # Phase 2: Autonomous Research Execution
        # -------------------------------------------------------------
        research_out = self.researcher.conduct_research(goal)
        all_steps.extend(self.researcher.steps)
        self.blackboard.store_artifact("research_findings", research_out["findings"])
        self.blackboard.store_artifact("sources", research_out["sources"])

        msg2 = self.blackboard.post_message(
            sender="ResearchAgent",
            recipient="AnalystAgent",
            phase="Research Complete",
            content=research_out["findings"],
            summary=f"Research complete. Forwarded {len(research_out['sources'])} evidence sources and factual dossier to AnalystAgent.",
        )
        self._broadcast(msg2)

        # -------------------------------------------------------------
        # Phase 3: Senior Analyst Critical Evaluation & SWOT
        # -------------------------------------------------------------
        analyst_out = self.analyst.analyze_findings(
            goal=goal,
            research_findings=research_out["findings"],
        )
        all_steps.extend(self.analyst.steps)
        self.blackboard.store_artifact("analyst_critique", analyst_out["analysis"])

        msg3 = self.blackboard.post_message(
            sender="AnalystAgent",
            recipient="ReportAgent",
            phase="Analysis Complete",
            content=analyst_out["analysis"],
            summary="Critical SWOT and vulnerability analysis concluded. Transmitted to ReportAgent.",
        )
        self._broadcast(msg3)

        # -------------------------------------------------------------
        # Phase 4: Executive Report Synthesis & Publication
        # -------------------------------------------------------------
        report_out = self.reporter.generate_report(
            goal=goal,
            research_findings=research_out["findings"],
            analyst_critique=analyst_out["analysis"],
        )
        all_steps.extend(self.reporter.steps)
        self.blackboard.store_artifact("final_report", report_out["report"])

        msg4 = self.blackboard.post_message(
            sender="ReportAgent",
            recipient="User",
            phase="Task Finalized",
            content=report_out["report"],
            summary="Publication-ready multi-agent executive briefing generated successfully.",
        )
        self._broadcast(msg4)

        return AgentResult(
            agent_name="MultiAgentCollaborativeSystem",
            success=True,
            output=report_out["report"],
            steps=all_steps,
            metadata={
                "goal": goal,
                "dialogue": [m.model_dump() for m in self.blackboard.get_all_messages()],
                "research_findings": research_out["findings"],
                "analyst_critique": analyst_out["analysis"],
                "sources": research_out["sources"],
            },
        )
