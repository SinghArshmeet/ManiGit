"""
Provider-agnostic Model Adapter interface.

Defines the essential abstractions required by ManiGit:
- generate()
- summarize()
- judge_memory()
- count_tokens()
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ModelAdapter(ABC):
    """
    Abstract base class for LLM providers (Mock, OpenAI, Anthropic, Gemini, Local).
    """

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """General text generation."""
        pass

    @abstractmethod
    def summarize(
        self,
        text: str,
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Summarize conversation excerpts into a concise synthesis preserving key facts."""
        pass

    @abstractmethod
    def judge_memory(
        self,
        message_content: str,
        active_memories: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Evaluate a conversational event and return a structured memory judgment:
        {
            "tier": "VERBATIM" | "SUMMARY" | "ARCHIVED",
            "confidence": float,
            "reason": str,
            "importance": str,
            "needs_summary": bool,
            "extracted_fact": Optional[str]
        }
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count or estimate tokens for a string."""
        pass
