"""
Heuristic & Signature Threat Detection Engine with MITRE ATT&CK Mapping.
Identifies Brute-Force, Web Application Exploitation, and Cloud IAM Privilege Escalation.
"""
import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from agents.security_analyst.log_parser import SecurityLogEntry


class ThreatIndicator(BaseModel):
    id: str
    title: str
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    mitre_tactic: str
    mitre_technique_id: str
    confidence: float = 0.95
    affected_ips: List[str] = Field(default_factory=list)
    affected_users: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    mitigation_steps: List[str] = Field(default_factory=list)
    remediation_commands: List[str] = Field(default_factory=list)


class ThreatRuleEngine:
    """
    Evaluates normalized logs against detection signatures and behavioral heuristics.
    """

    SQLI_PATTERNS = [
        re.compile(r"(\bUNION\b.*\bSELECT\b)", re.IGNORECASE),
        re.compile(r"(\bOR\b\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?)", re.IGNORECASE),
        re.compile(r"(--|#|/\*).*", re.IGNORECASE),
        re.compile(r"(\bDROP\b\s+\bTABLE\b)", re.IGNORECASE),
    ]
    XSS_PATTERNS = [
        re.compile(r"(<script.*?>.*?</script>)", re.IGNORECASE),
        re.compile(r"(javascript\s*:)", re.IGNORECASE),
        re.compile(r"(onerror\s*=)", re.IGNORECASE),
    ]
    TRAVERSAL_PATTERNS = [
        re.compile(r"(\.\./\.\.|etc/passwd|windows/system32)", re.IGNORECASE),
    ]

    def analyze(self, entries: List[SecurityLogEntry]) -> List[ThreatIndicator]:
        threats: List[ThreatIndicator] = []

        # 1. SSH Brute Force & Account Takeover Analysis
        ssh_threats = self._detect_ssh_bruteforce(entries)
        threats.extend(ssh_threats)

        # 2. Web Application Exploitation Analysis
        web_threats = self._detect_web_exploits(entries)
        threats.extend(web_threats)

        # 3. AWS CloudTrail IAM Privilege Escalation & Exfiltration
        cloud_threats = self._detect_cloudtrail_threats(entries)
        threats.extend(cloud_threats)

        return threats

    def _detect_ssh_bruteforce(self, entries: List[SecurityLogEntry]) -> List[ThreatIndicator]:
        threats = []
        ip_failures: Dict[str, List[SecurityLogEntry]] = {}
        ip_successes: Dict[str, List[SecurityLogEntry]] = {}
        sudo_events: List[SecurityLogEntry] = []

        for e in entries:
            if e.service == "sshd":
                if e.event_type == "AUTH_FAILED" and e.source_ip:
                    ip_failures.setdefault(e.source_ip, []).append(e)
                elif e.event_type == "AUTH_SUCCESS" and e.source_ip:
                    ip_successes.setdefault(e.source_ip, []).append(e)
            elif e.service == "sudo" and e.event_type == "PRIVILEGE_EXEC":
                sudo_events.append(e)

        for ip, fails in ip_failures.items():
            if len(fails) >= 3:
                targeted_users = list({f.user for f in fails if f.user})
                has_success = ip in ip_successes
                has_suspicious_sudo = any(
                    "shadow" in (s.metadata.get("command") or "") or "root" in (s.metadata.get("command") or "")
                    for s in sudo_events
                )

                if has_success and has_suspicious_sudo:
                    threats.append(
                        ThreatIndicator(
                            id=f"THR-SSH-COMPROMISE-{ip.replace('.', '_')}",
                            title="SSH Brute-Force Succeeded with Root Privilege Escalation",
                            severity="CRITICAL",
                            mitre_tactic="Initial Access & Privilege Escalation",
                            mitre_technique_id="T1110.001 / T1068",
                            affected_ips=[ip],
                            affected_users=targeted_users,
                            evidence=[f"Failed attempts: {len(fails)} from {ip}", f"Accepted login for user: {ip_successes[ip][0].user}"] + [s.raw_message for s in sudo_events],
                            mitigation_steps=[
                                f"Immediately terminate all active sessions for attacker IP {ip}.",
                                "Lock the compromised user account and rotate SSH authorized keys.",
                                "Audit /etc/shadow and system binaries for backdoor implants.",
                            ],
                            remediation_commands=[
                                f"iptables -A INPUT -s {ip} -j DROP",
                                f"usermod -L {ip_successes[ip][0].user}",
                                f"pkill -u {ip_successes[ip][0].user}",
                            ],
                        )
                    )
                elif has_success:
                    threats.append(
                        ThreatIndicator(
                            id=f"THR-SSH-SUCCESS-{ip.replace('.', '_')}",
                            title="SSH Password Guessing Attack Succeeded",
                            severity="HIGH",
                            mitre_tactic="Initial Access",
                            mitre_technique_id="T1110 / T1078",
                            affected_ips=[ip],
                            affected_users=targeted_users,
                            evidence=[f"{len(fails)} failed attempts before successful password authentication from {ip}"],
                            mitigation_steps=[
                                f"Block IP {ip} and enforce hardware MFA.",
                                "Disable SSH password authentication (PasswordAuthentication no).",
                            ],
                            remediation_commands=[
                                f"iptables -A INPUT -s {ip} -j DROP",
                            ],
                        )
                    )
                else:
                    threats.append(
                        ThreatIndicator(
                            id=f"THR-SSH-BRUTE-{ip.replace('.', '_')}",
                            title="Distributed SSH Dictionary Brute-Force",
                            severity="MEDIUM",
                            mitre_tactic="Credential Access",
                            mitre_technique_id="T1110.001",
                            affected_ips=[ip],
                            affected_users=targeted_users,
                            evidence=[f"{len(fails)} failed login attempts against users: {', '.join(targeted_users)}"],
                            mitigation_steps=[
                                f"Blacklist {ip} at network edge firewall or fail2ban.",
                                "Restrict SSH port 22 to authorized bastion IP ranges only.",
                            ],
                            remediation_commands=[
                                f"iptables -A INPUT -s {ip} -j DROP",
                                "fail2ban-client set sshd banip " + ip,
                            ],
                        )
                    )

        return threats

    def _detect_web_exploits(self, entries: List[SecurityLogEntry]) -> List[ThreatIndicator]:
        threats = []
        sqli_entries = []
        xss_entries = []
        traversal_entries = []
        scanner_entries = []

        for e in entries:
            if e.log_format != "web_access":
                continue
            path = e.metadata.get("path", "")
            ua = e.metadata.get("user_agent", "")

            # SQL Injection check
            for pat in self.SQLI_PATTERNS:
                if pat.search(path):
                    sqli_entries.append(e)
                    break

            # XSS check
            for pat in self.XSS_PATTERNS:
                if pat.search(path):
                    xss_entries.append(e)
                    break

            # Traversal check
            for pat in self.TRAVERSAL_PATTERNS:
                if pat.search(path):
                    traversal_entries.append(e)
                    break

            # Scanner check
            if any(s in ua.lower() for s in ["sqlmap", "nikto", "nmap", "dirbuster"]):
                scanner_entries.append(e)

        if sqli_entries:
            ips = list({e.source_ip for e in sqli_entries if e.source_ip})
            threats.append(
                ThreatIndicator(
                    id="THR-WEB-SQLI-01",
                    title="SQL Injection Exploit Attempt (OWASP A03)",
                    severity="CRITICAL",
                    mitre_tactic="Initial Access / Exploitation",
                    mitre_technique_id="T1190",
                    affected_ips=ips,
                    evidence=[e.raw_message for e in sqli_entries[:3]],
                    mitigation_steps=[
                        "Deploy ModSecurity / AWS WAF rule sets blocking SQLi meta-characters.",
                        "Refactor database queries using parameterized queries or prepared statements (ORM).",
                        "Sanitize and validate all query string parameters before database execution.",
                    ],
                    remediation_commands=[
                        f"iptables -A INPUT -s {ips[0]} -j DROP" if ips else "# No IP extracted",
                    ],
                )
            )

        if xss_entries:
            ips = list({e.source_ip for e in xss_entries if e.source_ip})
            threats.append(
                ThreatIndicator(
                    id="THR-WEB-XSS-01",
                    title="Cross-Site Scripting (XSS) Injection Payload",
                    severity="HIGH",
                    mitre_tactic="Defense Evasion / Initial Access",
                    mitre_technique_id="T1189",
                    affected_ips=ips,
                    evidence=[e.raw_message for e in xss_entries[:2]],
                    mitigation_steps=[
                        "Implement Content Security Policy (CSP) headers restricting inline scripts.",
                        "HTML entity encode all dynamic reflection in UI templates.",
                    ],
                    remediation_commands=[],
                )
            )

        if traversal_entries:
            ips = list({e.source_ip for e in traversal_entries if e.source_ip})
            threats.append(
                ThreatIndicator(
                    id="THR-WEB-TRAVERSAL-01",
                    title="Directory Traversal / Arbitrary File Read",
                    severity="HIGH",
                    mitre_tactic="Discovery",
                    mitre_technique_id="T1083",
                    affected_ips=ips,
                    evidence=[e.raw_message for e in traversal_entries[:2]],
                    mitigation_steps=[
                        "Restrict file server downloads to an isolated whitelist directory.",
                        "Strip relative path sequences ('../') in web routing layer.",
                    ],
                    remediation_commands=[],
                )
            )

        if scanner_entries and not sqli_entries:
            ips = list({e.source_ip for e in scanner_entries if e.source_ip})
            threats.append(
                ThreatIndicator(
                    id="THR-WEB-SCANNER-01",
                    title="Automated Vulnerability Scanner Activity",
                    severity="MEDIUM",
                    mitre_tactic="Reconnaissance",
                    mitre_technique_id="T1595.002",
                    affected_ips=ips,
                    evidence=[f"Detected scanner user agent: {scanner_entries[0].metadata.get('user_agent')}"],
                    mitigation_steps=[
                        "Block aggressive vulnerability scanners via WAF rate limiting and UA blocking."
                    ],
                    remediation_commands=[
                        f"iptables -A INPUT -s {ips[0]} -j DROP" if ips else "# No IP extracted"
                    ],
                )
            )

        return threats

    def _detect_cloudtrail_threats(self, entries: List[SecurityLogEntry]) -> List[ThreatIndicator]:
        threats = []
        for e in entries:
            if e.log_format != "cloudtrail":
                continue
            event_name = e.metadata.get("eventName", "")
            req_params = e.metadata.get("requestParameters") or {}
            ua = e.metadata.get("userAgent", "")
            user = e.user or "Unknown"
            ip = e.source_ip or "Unknown"

            # Check 1: Unauthorized AdministratorAccess Attachment
            if event_name in ["AttachUserPolicy", "AttachRolePolicy", "PutUserPolicy"]:
                policy_arn = req_params.get("policyArn", "")
                if "AdministratorAccess" in policy_arn or "admin" in policy_arn.lower():
                    threats.append(
                        ThreatIndicator(
                            id=f"THR-AWS-PRIV-ESC-{user}",
                            title="Critical Cloud IAM Privilege Escalation (AdministratorAccess)",
                            severity="CRITICAL",
                            mitre_tactic="Privilege Escalation & Persistence",
                            mitre_technique_id="T1098 / T1078.004",
                            affected_ips=[ip],
                            affected_users=[user],
                            evidence=[
                                f"User {user} attached policy {policy_arn} from IP {ip}",
                                f"User Agent: {ua}",
                            ],
                            mitigation_steps=[
                                f"Immediately detach AdministratorAccess from {user}.",
                                f"Deactivate IAM access keys and revoke active STS sessions for {user}.",
                                "Audit AWS CloudTrail for subsequent resources created by this identity.",
                            ],
                            remediation_commands=[
                                f"aws iam detach-user-policy --user-name {user} --policy-arn {policy_arn}",
                                f"aws iam delete-access-key --user-name {user} --access-key-id <KEY_ID>",
                            ],
                        )
                    )

            # Check 2: Exfiltration from sensitive buckets
            if event_name == "GetObject":
                bucket = req_params.get("bucketName", "")
                key = req_params.get("key", "")
                if any(kw in bucket.lower() or kw in key.lower() for kw in ["financial", "pii", "secret", "export"]):
                    threats.append(
                        ThreatIndicator(
                            id=f"THR-AWS-EXFIL-{user}",
                            title="High-Value S3 Bucket Data Exfiltration",
                            severity="CRITICAL",
                            mitre_tactic="Collection & Exfiltration",
                            mitre_technique_id="T1567.002",
                            affected_ips=[ip],
                            affected_users=[user],
                            evidence=[
                                f"Identity {user} accessed confidential object {bucket}/{key} from IP {ip} ({ua})"
                            ],
                            mitigation_steps=[
                                f"Apply explicit Deny bucket policy on {bucket} for identity {user}.",
                                "Rotate KMS customer managed keys (CMK) protecting data in S3.",
                            ],
                            remediation_commands=[
                                f"aws s3api put-bucket-policy --bucket {bucket} --policy file://deny_policy.json"
                            ],
                        )
                    )

        return threats
