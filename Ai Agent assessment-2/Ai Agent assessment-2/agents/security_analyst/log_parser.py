"""
Multi-Format Security Log Parser.
Parses Linux Syslog/Auth.log, Nginx/Apache Web Server Logs, and AWS CloudTrail JSON.
"""
import re
import json
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SecurityLogEntry(BaseModel):
    id: str
    log_format: str  # 'ssh_auth', 'web_access', 'cloudtrail', 'syslog'
    timestamp: str
    source_ip: Optional[str] = None
    service: str
    event_type: str
    user: Optional[str] = None
    status_code: Optional[int] = None
    raw_message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LogParser:
    """
    Parses heterogeneous security log files into standardized SecurityLogEntry models.
    """

    SSH_FAILED_PATTERN = re.compile(
        r"^(?P<time>[A-Za-z]{3}\s+\d+\s+\d+:\d+:\d+)\s+(?P<host>\S+)\s+sshd\[\d+\]:\s+Failed\s+password\s+for\s+(?:invalid\s+user\s+)?(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+(?P<port>\d+)",
        re.IGNORECASE,
    )
    SSH_ACCEPTED_PATTERN = re.compile(
        r"^(?P<time>[A-Za-z]{3}\s+\d+\s+\d+:\d+:\d+)\s+(?P<host>\S+)\s+sshd\[\d+\]:\s+Accepted\s+password\s+for\s+(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+(?P<port>\d+)",
        re.IGNORECASE,
    )
    SUDO_PATTERN = re.compile(
        r"^(?P<time>[A-Za-z]{3}\s+\d+\s+\d+:\d+:\d+)\s+(?P<host>\S+)\s+sudo:\s+(?P<user>\S+)\s+:.*?COMMAND=(?P<cmd>.*)$",
        re.IGNORECASE,
    )
    WEB_ACCESS_PATTERN = re.compile(
        r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<time>[^\]]+)\]\s+"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+(?P<status>\d{3})\s+(?P<bytes>\S+)(?:\s+"(?P<ref>[^"]*)"\s+"(?P<ua>[^"]*)")?',
    )

    def parse_file(self, file_path: str) -> List[SecurityLogEntry]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Log file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return self.parse_text(content, filename=os.path.basename(file_path))

    def parse_text(self, text: str, filename: str = "unnamed.log") -> List[SecurityLogEntry]:
        text_strip = text.strip()
        # 1. Attempt JSON / CloudTrail
        if text_strip.startswith("{") or text_strip.startswith("["):
            try:
                data = json.loads(text_strip)
                return self._parse_cloudtrail(data)
            except Exception:
                pass

        # 2. Line-by-line parsing for SSH or Web or Syslog
        entries: List[SecurityLogEntry] = []
        lines = text.splitlines()
        for idx, line in enumerate(lines, 1):
            if not line.strip():
                continue
            entry = self._parse_single_line(line, idx, filename)
            if entry:
                entries.append(entry)
        return entries

    def _parse_single_line(self, line: str, idx: int, filename: str) -> Optional[SecurityLogEntry]:
        line_str = line.strip()

        # Try SSH Failed
        m = self.SSH_FAILED_PATTERN.match(line_str)
        if m:
            d = m.groupdict()
            return SecurityLogEntry(
                id=f"{filename}_{idx}",
                log_format="ssh_auth",
                timestamp=d["time"],
                source_ip=d["ip"],
                service="sshd",
                event_type="AUTH_FAILED",
                user=d["user"],
                raw_message=line_str,
                metadata={"port": d.get("port"), "host": d.get("host")},
            )

        # Try SSH Accepted
        m = self.SSH_ACCEPTED_PATTERN.match(line_str)
        if m:
            d = m.groupdict()
            return SecurityLogEntry(
                id=f"{filename}_{idx}",
                log_format="ssh_auth",
                timestamp=d["time"],
                source_ip=d["ip"],
                service="sshd",
                event_type="AUTH_SUCCESS",
                user=d["user"],
                raw_message=line_str,
                metadata={"port": d.get("port"), "host": d.get("host")},
            )

        # Try Sudo Command
        m = self.SUDO_PATTERN.match(line_str)
        if m:
            d = m.groupdict()
            return SecurityLogEntry(
                id=f"{filename}_{idx}",
                log_format="ssh_auth",
                timestamp=d["time"],
                source_ip=None,
                service="sudo",
                event_type="PRIVILEGE_EXEC",
                user=d["user"],
                raw_message=line_str,
                metadata={"command": d.get("cmd")},
            )

        # Try Web Access Log
        m = self.WEB_ACCESS_PATTERN.match(line_str)
        if m:
            d = m.groupdict()
            status = int(d["status"])
            event_type = "HTTP_REQUEST"
            if status == 401 or status == 403:
                event_type = "HTTP_FORBIDDEN"
            elif status >= 500:
                event_type = "HTTP_SERVER_ERROR"

            return SecurityLogEntry(
                id=f"{filename}_{idx}",
                log_format="web_access",
                timestamp=d["time"],
                source_ip=d["ip"],
                service="web_server",
                event_type=event_type,
                status_code=status,
                raw_message=line_str,
                metadata={
                    "method": d["method"],
                    "path": d["path"],
                    "user_agent": d.get("ua") or "",
                    "referer": d.get("ref") or "",
                },
            )

        # Generic Syslog Fallback
        return SecurityLogEntry(
            id=f"{filename}_{idx}",
            log_format="syslog",
            timestamp="Unknown",
            source_ip=self._extract_ip(line_str),
            service="system",
            event_type="GENERIC_LOG",
            raw_message=line_str,
        )

    def _parse_cloudtrail(self, data: Any) -> List[SecurityLogEntry]:
        records = data.get("Records", []) if isinstance(data, dict) else (data if isinstance(data, list) else [data])
        entries: List[SecurityLogEntry] = []
        for idx, rec in enumerate(records, 1):
            user_identity = rec.get("userIdentity", {})
            user_name = user_identity.get("userName") or user_identity.get("arn", "Unknown")
            event_name = rec.get("eventName", "UnknownEvent")
            source_ip = rec.get("sourceIPAddress")

            entries.append(
                SecurityLogEntry(
                    id=f"cloudtrail_{idx}",
                    log_format="cloudtrail",
                    timestamp=rec.get("eventTime", "UnknownTime"),
                    source_ip=source_ip,
                    service=rec.get("eventSource", "aws"),
                    event_type=f"AWS_{event_name.upper()}",
                    user=user_name,
                    raw_message=json.dumps(rec),
                    metadata={
                        "awsRegion": rec.get("awsRegion"),
                        "eventName": event_name,
                        "requestParameters": rec.get("requestParameters"),
                        "userAgent": rec.get("userAgent"),
                    },
                )
            )
        return entries

    def _extract_ip(self, text: str) -> Optional[str]:
        m = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
        return m.group(0) if m else None
