"""
Autonomous Research & Report Agent (Requirement 2).
Searches for information, summarizes findings, and generates a structured research report with references.
"""
from typing import Optional, List, Dict, Any
from agents.core.base_agent import BaseAgent, AgentResult
from agents.core.llm_client import LLMClient
from agents.researcher.search_tools import SearchTool, SearchResult
from agents.researcher.synthesizer import ReportSynthesizer, ResearchReport


class ResearchAgent(BaseAgent):
    """
    Autonomous research agent that orchestrates web search,
    synthesizes multi-source findings, and formats an executive report with citations.
    """

    SYSTEM_PROMPT = """You are a Senior Principal Research Scientist and Autonomous Intelligence Agent.
Your mission is to perform thorough investigations into technical, scientific, or market domains.
Rules:
1. Synthesize multi-source facts objectively, avoiding unsupported claims.
2. Structure analysis into Executive Summary, Key Trends & Data, Architectural Implications, and Strategic Challenges.
3. Explicitly reference gathered evidence and provide actionable takeaways.
"""

    def __init__(
        self,
        name: str = "ResearchAgent",
        llm_client: Optional[LLMClient] = None,
        use_live_search: bool = True,
    ):
        super().__init__(
            name=name,
            role="Autonomous Research Specialist",
            description="Searches for information, summarizes cross-source findings, and generates structured reports with references.",
            system_prompt=self.SYSTEM_PROMPT,
            llm_client=llm_client,
        )
        self.search_tool = SearchTool(use_live=use_live_search)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        return self.research(topic=task, max_sources=context.get("max_sources", 5) if context else 5)

    def research(self, topic: str, max_sources: int = 5) -> AgentResult:
        self.reset_trace()

        # Step 1: Research Scoping & Query Formulation
        self.log_step(
            action="Research Scoping",
            thoughts=f"Formulating targeted search queries for topic: '{topic}'",
            input_data={"topic": topic},
            output_data={"queries": [topic, f"{topic} latest trends", f"{topic} benchmarks"]},
        )

        # Step 2: Multi-Source Web Information Retrieval
        search_results = self.search_tool.search(topic, max_results=max_sources)
        results_preview = [
            {"title": r.title, "url": r.url, "source": r.source, "snippet": r.snippet[:100] + "..."}
            for r in search_results
        ]

        self.log_step(
            action="Information Gathering",
            thoughts=f"Retrieved {len(search_results)} authoritative sources from web intelligence.",
            input_data={"search_topic": topic, "max_sources": max_sources},
            output_data={"sources_found": results_preview},
        )

        # Step 3: Information Extraction & Fact Synthesis
        snippets_text = "\n\n".join(
            f"[{idx+1}] Source: {r.title} ({r.source})\nURL: {r.url}\nExcerpt: {r.snippet}"
            for idx, r in enumerate(search_results)
        )

        synthesis_prompt = f"""Investigate and synthesize the following domain topic: "{topic}"

Gathered Web Evidence & Excerpts:
{snippets_text}

Provide an in-depth analytical summary covering:
1. Executive Summary
2. Key Empirical Findings & Breakthroughs
3. Architectural / Technical Implications
4. Strategic Challenges & Next Steps
Ensure insights directly reflect the provided source evidence."""

        self.log_step(
            action="Cross-Source Evidence Synthesis",
            thoughts="Analyzing and correlating multi-source excerpts through LLM reasoning.",
            input_data={"evidence_count": len(search_results)},
            output_data={"status": "synthesizing"},
        )

        # Step 4: LLM Generation
        raw_synthesis = self.query_llm(synthesis_prompt, temperature=0.3)

        # Step 5: Structured Report Compilation & Reference Formatting
        report: ResearchReport = ReportSynthesizer.compile_report(
            topic=topic,
            raw_synthesis=raw_synthesis,
            search_results=search_results,
        )

        self.log_step(
            action="Structured Report Generation",
            thoughts="Compiled complete structured markdown and HTML report with verified references.",
            output_data={
                "report_length_chars": len(report.markdown_content),
                "num_references": len(report.references),
            },
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            output=report.markdown_content,
            steps=self.steps,
            metadata={
                "topic": topic,
                "report": report.model_dump(),
                "html_export": report.html_content,
                "references": report.references,
            },
        )
