# Security Operations Center (SOC) Incident Assessment
**Target System/File**: `data/sample_logs/ssh_bruteforce.log` | **Overall Incident Severity**: **`CRITICAL`**

## 1. Threat Summary & MITRE ATT&CK Matrix

| Threat ID | Threat Title | Severity | MITRE Technique | Affected Targets |
|---|---|---|---|---|
| `THR-SSH-COMPROMISE-198_51_100_23` | **SSH Brute-Force Succeeded with Root Privilege Escalation** | `CRITICAL` | T1110.001 / T1068 | 198.51.100.23 |

## 2. In-Depth Incident Analysis & Playbook
### Comprehensive Threat Intelligence Analysis

**Overall Incident Severity**: `CRITICAL`

#### 1. Identified Threat Indicators & MITRE ATT&CK Mapping
- **MITRE Techniques**: T1110 (Brute Force), T1078 (Valid Accounts), T1068 (Privilege Escalation)
- **Primary Observations**:
- Detected distributed SSH password brute-force attempts targeting administrative accounts.
- Compromised account detected followed by unauthorized privilege escalation (`sudo cat /etc/shadow`).

#### 2. Root Cause & Impact Assessment
The adversary appears to be attempting automated exploitation or unauthorized privilege escalation. If left uncontained, this compromises confidentiality and system integrity.

#### 3. Immediate Mitigation Steps (Containment)
1. **Firewall Block**: Blacklist the offending IP address immediately on edge firewalls:
   ```bash
   iptables -A INPUT -s <OFFENDING_IP> -j DROP
   ```
2. **Session Termination**: Terminate active SSH sessions and revoke temporary AWS STS credentials.
3. **Account Containment**: Lock compromised user accounts and force password/key rotation with Hardware MFA.

#### 4. Hardening Recommendations
- Enforce Zero-Trust Network Access (ZTNA) and disable password-based SSH authentication (`PasswordAuthentication no`).
- Deploy CloudTrail GuardDuty anomaly alerts and enforce SCPs preventing unauthorized `iam:AttachUserPolicy` calls.
- Enforce Web Application Firewall (WAF) rules blocking SQL injection payloads.


## 3. Automated Containment Script (Executable)
```bash
#!/usr/bin/env bash
# Automated Incident Response Containment Script
set -e
iptables -A INPUT -s 198.51.100.23 -j DROP
usermod -L devops
pkill -u devops
echo '[+] Containment actions executed successfully.'
```