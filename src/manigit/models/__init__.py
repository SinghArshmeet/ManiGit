"""
Model Adapter Subsystem.

Provides lightweight, provider-agnostic abstractions over LLMs:
- generate()
- summarize()
- judge_memory()
- count_tokens()
"""

from manigit.models.base import ModelAdapter
from manigit.models.gemini import GeminiModelAdapter
from manigit.models.mock import MockModelAdapter

__all__ = ["ModelAdapter", "MockModelAdapter", "GeminiModelAdapter"]
