"""
Tier 2 Summarization module for condensing multi-turn discussions into concise factual summaries.
"""

from dataclasses import dataclass
from typing import List, Optional

from manigit.core.models import Message
from manigit.core.tokens import estimate_tokens
from manigit.models.base import ModelAdapter


@dataclass(frozen=True)
class SummaryResult:
    """Structured output of a multi-turn conversation condensation."""
    summary_content: str
    source_message_ids: List[str]
    topic: str
    original_token_count: int
    summary_token_count: int
    tokens_saved: int


class MemorySummarizer:
    """
    Synthesizes multi-turn discussions into concise, factual Tier 2 summaries
    while preserving facts, decisions, numbers, and provenance.
    """

    def __init__(self, model_adapter: ModelAdapter):
        self.model_adapter = model_adapter

    def summarize_messages(
        self,
        messages: List[Message],
        topic: str = "General Discussion",
    ) -> SummaryResult:
        """
        Condense a sequence of raw messages into a factual synthesis.
        """
        if not messages:
            return SummaryResult(
                summary_content="",
                source_message_ids=[],
                topic=topic,
                original_token_count=0,
                summary_token_count=0,
                tokens_saved=0,
            )

        source_ids = [m.id for m in messages]
        raw_text_blocks = [f"{m.role.capitalize()}: {m.content.strip()}" for m in messages]
        combined_text = "\n".join(raw_text_blocks)
        original_tokens = sum(m.token_count for m in messages)

        # Generate summary via model adapter
        summary_text = self.model_adapter.summarize(
            text=combined_text,
            context=f"Topic: {topic}. Preserve all key decisions, constraints, and numbers.",
        )

        summary_tokens = estimate_tokens(summary_text)
        tokens_saved = max(0, original_tokens - summary_tokens)

        return SummaryResult(
            summary_content=summary_text.strip(),
            source_message_ids=source_ids,
            topic=topic,
            original_token_count=original_tokens,
            summary_token_count=summary_tokens,
            tokens_saved=tokens_saved,
        )
