"""
Agent Runtime Subsystem.

Responsible for orchestrating the complete multi-turn interaction lifecycle:
1. Receive User Message: Save raw user message to immutable append-only archive.
2. Context Retrieval: Fetch relevant active facts and summaries from versioned repository.
3. Context Construction: Context compiler packs memory within the token budget.
4. Model Response: Invoke model adapter to generate response.
5. Memory Intelligence: Classify exchange, identify new facts/updates, detect contradictions.
6. Commit: Atomically persist updated memory snapshot with commit metadata & why report.
"""

from manigit.agent.exceptions import (
    AgentRuntimeError,
    ContextCompilationError,
    EmptyMessageError,
    InvalidBranchError,
    ModelAdapterError,
)
from manigit.agent.models import (
    AgentConfig,
    AgentResponse,
    AgentTurn,
    TokenUsage,
)
from manigit.agent.runtime import AgentRuntime

__all__ = [
    "AgentRuntime",
    "AgentConfig",
    "AgentTurn",
    "AgentResponse",
    "TokenUsage",
    "AgentRuntimeError",
    "EmptyMessageError",
    "ModelAdapterError",
    "ContextCompilationError",
    "InvalidBranchError",
]
