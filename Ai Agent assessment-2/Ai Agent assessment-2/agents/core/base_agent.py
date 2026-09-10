"""
Base Agent Architecture with execution tracing, step logging, and state management.
"""
from typing import Optional, List, Dict, Any, Callable
from pydantic import BaseModel, Field
import time
import uuid
import logging
from agents.core.llm_client import LLMClient, get_default_llm_client

logger = logging.getLogger(__name__)


class AgentStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    step_number: int
    agent_name: str
    action: str
    thoughts: Optional[str] = None
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    timestamp: float = Field(default_factory=time.time)


class AgentResult(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_name: str
    success: bool
    output: str
    steps: List[AgentStep] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class BaseAgent:
    """
    Abstract foundation for all specialized autonomous agents.
    Provides execution tracing, LLM integration, and step callbacks.
    """

    def __init__(
        self,
        name: str,
        role: str,
        description: str,
        system_prompt: str,
        llm_client: Optional[LLMClient] = None,
    ):
        self.name = name
        self.role = role
        self.description = description
        self.system_prompt = system_prompt
        self.llm_client = llm_client or get_default_llm_client()
        self.steps: List[AgentStep] = []
        self._step_counter = 0
        self._callbacks: List[Callable[[AgentStep], None]] = []

    def register_callback(self, callback: Callable[[AgentStep], None]):
        """Register a real-time step observer."""
        self._callbacks.append(callback)

    def log_step(
        self,
        action: str,
        thoughts: Optional[str] = None,
        input_data: Optional[Any] = None,
        output_data: Optional[Any] = None,
    ) -> AgentStep:
        """Records an execution step and notifies registered listeners."""
        self._step_counter += 1
        step = AgentStep(
            step_number=self._step_counter,
            agent_name=self.name,
            action=action,
            thoughts=thoughts,
            input_data=input_data,
            output_data=output_data,
        )
        self.steps.append(step)
        for cb in self._callbacks:
            try:
                cb(step)
            except Exception as e:
                logger.error(f"Error in step callback: {e}")
        return step

    def reset_trace(self):
        """Resets execution history for a new task."""
        self.steps = []
        self._step_counter = 0

    def query_llm(self, prompt: str, temperature: float = 0.3) -> str:
        """Helper to invoke the configured LLM client."""
        return self.llm_client.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=temperature,
        )

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """Core execution method to be overridden or used with default flow."""
        raise NotImplementedError("Subclasses must implement run()")
