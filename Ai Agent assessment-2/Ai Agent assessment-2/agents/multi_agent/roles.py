"""
Specialized Agent Roles for Multi-Agent Collaboration.
1. LeadResearchAgent: Inquires, gathers facts, compiles evidence.
2. SeniorAnalystAgent: Critiques findings, performs SWOT & risk evaluation.
3. ExecutiveReportAgent: Synthesizes final deliverables with executive recommendations.
"""
from typing import Optional, Dict, Any, List
from agents.core.base_agent import BaseAgent, AgentResult
from agents.core.llm_client import LLMClient
from agents.researcher.search_tools import SearchTool, SearchResult


class LeadResearchAgent(BaseAgent):
    """
    Agent 1 in the collaborative team: Responsible for information discovery,
    fact extraction, and compiling empirical evidence.
    """

    SYSTEM_PROMPT = """You are the Lead Research Agent in a collaborative intelligence unit.
Your goal is to thoroughly investigate the assigned task, gather empirical evidence,
and structure factual findings clearly for downstream analysts.
Focus strictly on objective data, verifiable mechanisms, and clear benchmarks.
"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            name="ResearchAgent",
            role="Information Gathering & Evidence Lead",
            description="Performs domain inquiry, gathers facts from search and knowledge stores, and establishes the empirical baseline.",
            system_prompt=self.SYSTEM_PROMPT,
            llm_client=llm_client,
        )
        self.search_tool = SearchTool(use_live=True)

    def conduct_research(self, goal: str) -> Dict[str, Any]:
        self.reset_trace()

        # Step 1: Query Formulation
        self.log_step(
            action="Query Formulation",
            thoughts=f"Formulating empirical queries for goal: '{goal}'",
            input_data={"goal": goal},
            output_data={"queries": [goal, f"{goal} analysis", f"{goal} best practices"]},
        )

        # Step 2: Information Retrieval
        results = self.search_tool.search(goal, max_results=4)
        self.log_step(
            action="Fact Retrieval",
            thoughts=f"Gathered {len(results)} authoritative evidence points.",
            output_data={"sources": [r.title for r in results]},
        )

        # Step 3: LLM Synthesis of Factual Baseline
        evidence_text = "\n\n".join(f"- **{r.title}**: {r.snippet} (Source: {r.source})" for r in results)
        prompt = f"""Investigate the following collaborative goal: "{goal}"

Available Evidence:
{evidence_text}

Provide an objective factual research briefing for our Senior Analyst.
Detail:
1. Primary Objectives and Core Architecture
2. Empirical Benchmarks & Current State-of-the-Art
3. Observable Industry / Technical Patterns"""

        findings = self.query_llm(prompt, temperature=0.3)

        self.log_step(
            action="Factual Briefing Prepared",
            thoughts="Compiled factual dossier and handed over to Senior Analyst Agent.",
            output_data={"findings_length": len(findings)},
        )

        return {
            "goal": goal,
            "findings": findings,
            "sources": [r.model_dump() for r in results],
            "steps": self.steps,
        }


class SeniorAnalystAgent(BaseAgent):
    """
    Agent 2 in the collaborative team: Responsible for critical evaluation,
    SWOT analysis, stress-testing assumptions, and identifying security/operational risks.
    """

    SYSTEM_PROMPT = """You are the Senior Analyst Agent in a collaborative intelligence unit.
Your goal is to critically evaluate findings provided by the Research Agent.
Rules:
1. Conduct a rigorous SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis.
2. Stress-test assumptions and pinpoint potential failure modes, blind spots, and security/operational risks.
3. Provide strategic trade-offs and constructive critiques for the final report.
"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            name="AnalystAgent",
            role="Critical Analysis & Risk Strategist",
            description="Critically reviews research data, evaluates risks and trade-offs, and conducts SWOT analysis.",
            system_prompt=self.SYSTEM_PROMPT,
            llm_client=llm_client,
        )

    def analyze_findings(self, goal: str, research_findings: str) -> Dict[str, Any]:
        self.reset_trace()

        self.log_step(
            action="Reviewing Research Dossier",
            thoughts=f"Analyzing research briefing regarding '{goal}' to identify strategic vulnerabilities.",
            input_data={"findings_preview": research_findings[:150] + "..."},
        )

        prompt = f"""Conduct a Senior Analyst evaluation of the research findings for: "{goal}"

Research Dossier:
{research_findings}

Deliver a comprehensive critical assessment covering:
1. Evaluation of Core Claims & Empirical Soundness
2. Comprehensive SWOT Matrix (Strengths, Weaknesses, Opportunities, Threats)
3. Operational & Security Risk Vectors
4. Strategic Trade-offs & Recommendations for Executive Delivery"""

        analysis = self.query_llm(prompt, temperature=0.3)

        self.log_step(
            action="SWOT & Risk Matrix Finalized",
            thoughts="Constructed critique and forwarded strategic assessment to Report Agent.",
            output_data={"analysis_length": len(analysis)},
        )

        return {
            "analysis": analysis,
            "steps": self.steps,
        }


class ExecutiveReportAgent(BaseAgent):
    """
    Agent 3 in the collaborative team: Synthesizes research findings and analyst critiques
    into a cohesive, high-impact executive report with clear action items.
    """

    SYSTEM_PROMPT = """You are the Executive Report Agent in a collaborative intelligence unit.
Your mission is to synthesize input from the Research Agent (facts) and the Analyst Agent (critique)
into a polished, definitive, executive-grade deliverable.
Rules:
1. Deliver a clean structure: Executive Summary, Key Evidence, Strategic SWOT, Trade-Off Matrix, and Action Roadmap.
2. Eliminate redundancies and produce crisp, boardroom-ready prose.
"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            name="ReportAgent",
            role="Executive Synthesis & Communication Lead",
            description="Synthesizes factual research and analytical critiques into structured, publication-ready reports.",
            system_prompt=self.SYSTEM_PROMPT,
            llm_client=llm_client,
        )

    def generate_report(self, goal: str, research_findings: str, analyst_critique: str) -> Dict[str, Any]:
        self.reset_trace()

        self.log_step(
            action="Cross-Agent Synthesis",
            thoughts="Fusing empirical research with strategic SWOT analysis into a final publication.",
            input_data={"goal": goal},
        )

        prompt = f"""Synthesize the collaborative findings into a definitive Executive Report:

Objective: "{goal}"

Research Findings (from Lead Research Agent):
{research_findings}

Analyst Critique & SWOT (from Senior Analyst Agent):
{analyst_critique}

Format a publication-ready Executive Report covering:
# Collaborative Executive Intelligence Report: {goal}
## 1. Executive Summary
## 2. Integrated Key Findings
## 3. Critical SWOT & Risk Analysis
## 4. Strategic Recommendations & Roadmap"""

        report_content = self.query_llm(prompt, temperature=0.2)

        self.log_step(
            action="Final Report Published",
            thoughts="Executive report completed and verified.",
            output_data={"report_chars": len(report_content)},
        )

        return {
            "report": report_content,
            "steps": self.steps,
        }
