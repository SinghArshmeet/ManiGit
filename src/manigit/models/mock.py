"""
Mock Model Adapter for deterministic, offline testing of ManiGit.
"""

from typing import Any, Callable, Dict, List, Optional
from manigit.core.tokens import estimate_tokens
from manigit.models.base import ModelAdapter


class MockModelAdapter(ModelAdapter):
    """
    In-memory, deterministic mock adapter for offline execution and testing.
    """

    def __init__(
        self,
        default_judge_response: Optional[Dict[str, Any]] = None,
        default_summary_response: Optional[str] = None,
        default_generate_response: Optional[str] = None,
        judge_handler: Optional[Callable[[str, Optional[List[Dict[str, Any]]]], Dict[str, Any]]] = None,
        generate_handler: Optional[Callable[[str], str]] = None,
    ):
        self.default_judge_response = default_judge_response
        self.default_summary_response = default_summary_response
        self.default_generate_response = default_generate_response
        self.judge_handler = judge_handler
        self.generate_handler = generate_handler
        self.call_history: List[Dict[str, Any]] = []

    def generate(self, prompt: str, **kwargs: Any) -> str:
        self.call_history.append({"method": "generate", "prompt": prompt, "kwargs": kwargs})
        if self.generate_handler:
            return self.generate_handler(prompt)
        if self.default_generate_response is not None:
            return self.default_generate_response
        return "Mock response for prompt."

    def summarize(
        self,
        text: str,
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        self.call_history.append({
            "method": "summarize",
            "text": text,
            "context": context,
            "kwargs": kwargs,
        })
        if self.default_summary_response is not None:
            return self.default_summary_response

        # Deterministic default condensation
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        if len(lines) <= 2:
            return " ".join(lines)
        return f"Summary of discussion: {lines[0]} -> {lines[-1]}"

    def judge_memory(
        self,
        message_content: str,
        active_memories: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        self.call_history.append({
            "method": "judge_memory",
            "message_content": message_content,
            "active_memories": active_memories,
            "kwargs": kwargs,
        })

        if self.judge_handler:
            return self.judge_handler(message_content, active_memories)

        if self.default_judge_response:
            return dict(self.default_judge_response)

        # Basic deterministic heuristic for mock judge
        content_lower = message_content.lower().strip()

        # Inquiries/questions should not be retained as new active facts
        if content_lower.endswith("?") or any(
            content_lower.startswith(q) for q in ["what", "how", "why", "where", "when", "who", "which", "is", "are"]
        ):
            return {
                "tier": "ARCHIVED",
                "confidence": 0.95,
                "reason": "Mock LLM judge identified conversational query or inquiry.",
                "importance": "low",
                "needs_summary": False,
                "extracted_fact": None,
            }

        if any(w in content_lower for w in ["tentative", "might scale", "not certain", "speculative"]):
            return {
                "tier": "ARCHIVED",
                "confidence": 0.55,
                "reason": "Mock LLM judge identified tentative speculation; recommended archive with low confidence.",
                "importance": "low",
                "needs_summary": False,
                "extracted_fact": message_content.strip(),
            }

        if any(w in content_lower for w in ["database", "budget", "constraint", "must", "api_key", "config"]):
            return {
                "tier": "VERBATIM",
                "confidence": 0.95,
                "reason": "Mock LLM judge identified critical technical specification or constraint.",
                "importance": "high",
                "needs_summary": False,
                "extracted_fact": message_content.strip(),
            }
        elif any(w in content_lower for w in ["discussion", "discussing", "considered", "exploring", "options", "pros and cons"]):
            return {
                "tier": "SUMMARY",
                "confidence": 0.85,
                "reason": "Mock LLM judge identified multi-turn reasoning and exploratory options.",
                "importance": "medium",
                "needs_summary": True,
                "extracted_fact": message_content.strip(),
            }
        elif any(w in content_lower for w in ["hi", "hello", "thanks", "ok", "cool", "sounds good"]):
            return {
                "tier": "ARCHIVED",
                "confidence": 0.90,
                "reason": "Mock LLM judge identified conversational filler or greeting.",
                "importance": "low",
                "needs_summary": False,
                "extracted_fact": None,
            }

        # Default uncertain / conservative preservation
        return {
            "tier": "VERBATIM",
            "confidence": 0.65,
            "reason": "Mock LLM judge evaluated content as ambiguous; preserving conservatively.",
            "importance": "medium",
            "needs_summary": False,
            "extracted_fact": message_content.strip(),
        }

    def count_tokens(self, text: str) -> int:
        return estimate_tokens(text)
