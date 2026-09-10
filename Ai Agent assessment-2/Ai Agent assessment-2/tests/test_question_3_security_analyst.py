"""
Unit and Integration Tests for Question 3: Security Log & Threat Analyst Agent.
"""
import os
import pytest
from agents.security_analyst import SecurityAnalystAgent
from agents.security_analyst.log_parser import LogParser
from agents.security_analyst.threat_rules import ThreatRuleEngine


def test_ssh_log_parser_and_threat_detection():
    ssh_log_path = "data/sample_logs/ssh_bruteforce.log"
    assert os.path.exists(ssh_log_path), "SSH log sample must exist"

    parser = LogParser()
    entries = parser.parse_file(ssh_log_path)
    assert len(entries) > 5

    engine = ThreatRuleEngine()
    threats = engine.analyze(entries)
    assert len(threats) >= 1

    # Brute force with root escalation should be CRITICAL
    severities = [t.severity for t in threats]
    assert "CRITICAL" in severities or "HIGH" in severities


def test_web_sqli_detection():
    sqli_log_path = "data/sample_logs/web_sqli_attack.log"
    assert os.path.exists(sqli_log_path), "Web SQLi log sample must exist"

    agent = SecurityAnalystAgent()
    result = agent.analyze_file(sqli_log_path)

    assert result.success is True
    assert "MITRE" in result.output
    assert result.metadata["peak_severity"] in ["HIGH", "CRITICAL"]
    assert any("iptables" in cmd or "firewall" in cmd.lower() for t in result.metadata["threats"] for cmd in t.get("remediation_commands", []))


def test_cloudtrail_detection():
    cloudtrail_path = "data/sample_logs/cloudtrail_suspicious.json"
    assert os.path.exists(cloudtrail_path), "CloudTrail log sample must exist"

    agent = SecurityAnalystAgent()
    result = agent.analyze_file(cloudtrail_path)

    assert result.success is True
    assert result.metadata["total_logs"] >= 1
    assert result.metadata["peak_severity"] in ["HIGH", "CRITICAL"]
