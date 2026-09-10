"""
Security Log & Threat Intelligence Agent (Requirement 3).
Analyzes security logs/alerts, identifies potential threats, classifies severity, and suggests mitigation steps.
"""
from typing import Optional, List, Dict, Any
from agents.core.base_agent import BaseAgent, AgentResult
from agents.core.llm_client import LLMClient
from agents.security_analyst.log_parser import LogParser, SecurityLogEntry
from agents.security_analyst.threat_rules import ThreatRuleEngine, ThreatIndicator


class SecurityAnalystAgent(BaseAgent):
    """
    Autonomous SOC Analyst Agent.
    Specializes in ingesting heterogeneous security logs, detecting adversaries via MITRE ATT&CK,
    scoring threat severity, and producing automated incident response playbooks.
    """

    SYSTEM_PROMPT = """You are a Principal Security Operations Center (SOC) Incident Response Analyst.
Your duty is to analyze security alerts and server logs to determine:
1. Threat Identification & MITRE ATT&CK taxonomy mapping.
2. Severity Classification (LOW, MEDIUM, HIGH, CRITICAL) with clear risk justification.
3. Immediate Containment Playbooks (firewall rules, account locks, session revocations).
4. Long-term hardening and architecture remediation.
Be thorough, authoritative, and provide ready-to-execute terminal commands.
"""

    def __init__(
        self,
        name: str = "SecurityAnalystAgent",
        llm_client: Optional[LLMClient] = None,
    ):
        super().__init__(
            name=name,
            role="Security Log & Threat Intelligence Analyst",
            description="Analyzes security logs, identifies attack patterns, classifies threat severity, and synthesizes mitigation playbooks.",
            system_prompt=self.SYSTEM_PROMPT,
            llm_client=llm_client,
        )
        self.parser = LogParser()
        self.rule_engine = ThreatRuleEngine()

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """Analyzes log file path or raw log text passed as task."""
        if context and "file_path" in context:
            return self.analyze_file(context["file_path"])
        return self.analyze_text(task)

    def analyze_file(self, file_path: str) -> AgentResult:
        self.reset_trace()
        entries = self.parser.parse_file(file_path)
        return self._process_entries(entries, source_desc=file_path)

    def analyze_text(self, log_text: str, label: str = "Pasted_Logs.log") -> AgentResult:
        self.reset_trace()
        entries = self.parser.parse_text(log_text, filename=label)
        return self._process_entries(entries, source_desc=label)

    def _process_entries(self, entries: List[SecurityLogEntry], source_desc: str) -> AgentResult:
        # Step 1: Log Ingestion & Normalization
        format_counts: Dict[str, int] = {}
        for e in entries:
            format_counts[e.log_format] = format_counts.get(e.log_format, 0) + 1

        self.log_step(
            action="Log Ingestion & Schema Normalization",
            thoughts=f"Ingested {len(entries)} log events from '{source_desc}'. Formats detected: {format_counts}",
            input_data={"total_records": len(entries), "source": source_desc},
            output_data={"detected_formats": format_counts},
        )

        # Step 2: Heuristic Threat Detection & MITRE ATT&CK Mapping
        detected_threats: List[ThreatIndicator] = self.rule_engine.analyze(entries)
        
        # Calculate maximum severity
        severity_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        max_sev = "LOW"
        for t in detected_threats:
            if severity_rank.get(t.severity, 1) > severity_rank.get(max_sev, 1):
                max_sev = t.severity

        threat_summaries = [
            {
                "id": t.id,
                "title": t.title,
                "severity": t.severity,
                "mitre": f"{t.mitre_tactic} ({t.mitre_technique_id})",
                "affected_ips": t.affected_ips,
                "commands": t.remediation_commands,
            }
            for t in detected_threats
        ]

        self.log_step(
            action="Threat Detection & MITRE ATT&CK Mapping",
            thoughts=f"Identified {len(detected_threats)} threat indicators. Peak severity evaluated as: {max_sev}",
            input_data={"log_events_analyzed": len(entries)},
            output_data={"threats_detected": threat_summaries, "peak_severity": max_sev},
        )

        # Step 3: LLM Incident Correlation & Response Synthesis
        threat_evidence_blocks = []
        for t in detected_threats:
            threat_evidence_blocks.append(
                f"### Threat [{t.severity}]: {t.title}\n"
                f"- MITRE ATT&CK: {t.mitre_tactic} ({t.mitre_technique_id})\n"
                f"- Affected Entities: IPs={t.affected_ips}, Users={t.affected_users}\n"
                f"- Raw Evidence:\n" + "\n".join(f"  * {ev}" for ev in t.evidence[:4]) + "\n"
                f"- Mitigation Commands:\n" + "\n".join(f"  ```bash\n  {cmd}\n  ```" for cmd in t.remediation_commands)
            )

        log_sample = "\n".join(e.raw_message for e in entries[:15])
        llm_prompt = f"""Perform a comprehensive Security Operations Center (SOC) threat analysis for the following incident:

Source: {source_desc}
Total Logs Analyzed: {len(entries)}
Peak Calculated Severity: {max_sev}

Detected Threat Indicators:
{chr(10).join(threat_evidence_blocks) if threat_evidence_blocks else "No direct signature matched, evaluating anomaly patterns."}

Sample Raw Log Stream:
{log_sample}

Synthesize a professional Incident Response Report covering:
1. Executive Incident Summary & Severity Rating
2. Adversary Tactics, Techniques, and Procedures (TTPs)
3. Immediate Containment Actions (with bash commands)
4. Strategic Remediation & Long-term Defense Hardening"""

        self.log_step(
            action="SOC Incident Playbook Synthesis",
            thoughts="Prompting LLM to synthesize holistic attack kill-chain and immediate containment directives.",
            input_data={"peak_severity": max_sev, "num_threats": len(detected_threats)},
            output_data={"status": "synthesizing"},
        )

        report_analysis = self.query_llm(llm_prompt, temperature=0.2)

        # Format complete markdown report with structured threat table
        report_md_lines = [
            f"# Security Operations Center (SOC) Incident Assessment",
            f"**Target System/File**: `{source_desc}` | **Overall Incident Severity**: **`{max_sev}`**",
            "",
            "## 1. Threat Summary & MITRE ATT&CK Matrix",
            "",
            "| Threat ID | Threat Title | Severity | MITRE Technique | Affected Targets |",
            "|---|---|---|---|---|",
        ]

        if detected_threats:
            for t in detected_threats:
                targets = ", ".join(t.affected_ips or t.affected_users or ["Host"])
                report_md_lines.append(
                    f"| `{t.id}` | **{t.title}** | `{t.severity}` | {t.mitre_technique_id} | {targets} |"
                )
        else:
            report_md_lines.append("| `THR-BENIGN` | No critical threat signatures triggered | `LOW` | N/A | None |")

        report_md_lines.append("")
        report_md_lines.append("## 2. In-Depth Incident Analysis & Playbook")
        report_md_lines.append(report_analysis)
        report_md_lines.append("")

        if detected_threats:
            all_cmds = []
            for t in detected_threats:
                all_cmds.extend(t.remediation_commands)
            if all_cmds:
                report_md_lines.append("## 3. Automated Containment Script (Executable)")
                report_md_lines.append("```bash")
                report_md_lines.append("#!/usr/bin/env bash")
                report_md_lines.append("# Automated Incident Response Containment Script")
                report_md_lines.append("set -e")
                for cmd in all_cmds:
                    report_md_lines.append(cmd)
                report_md_lines.append("echo '[+] Containment actions executed successfully.'")
                report_md_lines.append("```")

        final_output = "\n".join(report_md_lines)

        self.log_step(
            action="Remediation Playbook Generation",
            thoughts=f"Incident report completed. Peak severity: {max_sev}. Containment commands formulated.",
            output_data={"report_length": len(final_output), "remediation_ready": bool(detected_threats)},
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            output=final_output,
            steps=self.steps,
            metadata={
                "source": source_desc,
                "peak_severity": max_sev,
                "total_logs": len(entries),
                "threats": [t.model_dump() for t in detected_threats],
                "threat_count": len(detected_threats),
            },
        )
