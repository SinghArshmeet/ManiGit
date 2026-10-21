"""
Simple deterministic token accounting abstraction for Phase 1.
"""

import math


def estimate_tokens(text: str) -> int:
    """
    Deterministic token estimate for Phase 1.
    
    Heuristic: Average English token is ~4 characters or ~0.75 words.
    Uses max(1, ceil(len(text) / 4)) for non-empty text, and 0 for empty string.
    Will be swappable with model adapter tokenizers in future phases.
    """
    if not text:
        return 0
    # Use character-based estimation: 4 chars per token
    return max(1, math.ceil(len(text.strip()) / 4.0))
