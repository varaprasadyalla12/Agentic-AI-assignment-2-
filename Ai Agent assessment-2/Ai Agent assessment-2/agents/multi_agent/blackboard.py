"""
Shared Blackboard & Message Bus for Multi-Agent Collaboration.
Enables transparent, asynchronous or synchronous inter-agent communication.
"""
import time
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CollaborationMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender: str
    recipient: str
    phase: str
    content: str
    summary: str = ""
    timestamp: float = Field(default_factory=time.time)


class SharedBlackboard:
    """
    Central collaborative blackboard tracking inter-agent dialogue, artifacts, and consensus.
    """

    def __init__(self):
        self.messages: List[CollaborationMessage] = []
        self.artifacts: Dict[str, Any] = {}
        self.task_goal: str = ""

    def init_task(self, goal: str):
        self.task_goal = goal
        self.messages = []
        self.artifacts = {"goal": goal}

    def post_message(
        self,
        sender: str,
        recipient: str,
        phase: str,
        content: str,
        summary: Optional[str] = None,
    ) -> CollaborationMessage:
        msg = CollaborationMessage(
            sender=sender,
            recipient=recipient,
            phase=phase,
            content=content,
            summary=summary or content[:100] + "...",
        )
        self.messages.append(msg)
        return msg

    def store_artifact(self, key: str, value: Any):
        self.artifacts[key] = value

    def get_artifact(self, key: str) -> Optional[Any]:
        return self.artifacts.get(key)

    def get_all_messages(self) -> List[CollaborationMessage]:
        return self.messages

    def dump_state(self) -> Dict[str, Any]:
        return {
            "task_goal": self.task_goal,
            "message_count": len(self.messages),
            "messages": [m.model_dump() for m in self.messages],
            "artifacts_keys": list(self.artifacts.keys()),
        }
