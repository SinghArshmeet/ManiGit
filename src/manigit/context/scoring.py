"""
Deterministic scoring and prioritization engine for active memory units.
"""

import re
from typing import List, Optional, Set, Tuple

from manigit.context.models import ScoringWeights
from manigit.core.models import Memory, MemoryTier


class ScoringEngine:
    """
    Computes deterministic textual relevance and priority scores.
    
    Guarantees:
    - Textual relevance outranks blind tier prioritization.
    - Relevant constraints and decisions receive distinct priority boosts.
    - Equal scores break ties deterministically.
    """

    STOP_WORDS: Set[str] = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
        "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
        "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
        "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
        "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
        "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
        "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
        "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
        "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
        "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
        "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
        "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
        "they've", "this", "those", "through", "to", "too", "under", "until", "up",
        "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
        "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
        "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
        "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
        "yourself", "yourselves"
    }

    CONSTRAINT_KEYWORDS: Set[str] = {
        "must", "cannot", "strictly", "required", "mandatory", "never", "always",
        "only", "limit", "restriction", "deadline", "capped", "forbidden"
    }

    DECISION_KEYWORDS: Set[str] = {
        "decided", "decision", "agreed", "selected", "chosen", "will use", "switched",
        "adopted", "target", "approved"
    }

    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()

    def tokenize(self, text: str) -> List[str]:
        """Extract lower-cased alphanumeric word tokens excluding stop words."""
        raw_tokens = re.findall(r"[a-zA-Z0-9_\-]+", text.lower())
        return [t for t in raw_tokens if t not in self.STOP_WORDS and len(t) > 1]

    def compute_relevance(self, query: str, text: str) -> float:
        """
        Compute normalized textual relevance in [0.0, 1.0].
        
        Calculated via query token overlap ratio and substring containment.
        """
        q_tokens = self.tokenize(query)
        if not q_tokens:
            return 0.0

        t_tokens = set(self.tokenize(text))
        if not t_tokens:
            return 0.0

        # Term overlap
        matched_tokens = sum(1 for q in q_tokens if q in t_tokens)
        token_overlap = matched_tokens / float(len(q_tokens))

        # Substring / exact phrase bonus
        clean_query = query.strip().lower()
        clean_text = text.strip().lower()
        phrase_bonus = 0.20 if (len(clean_query) > 3 and clean_query in clean_text) else 0.0

        raw_score = token_overlap * 0.80 + phrase_bonus
        return min(1.0, round(raw_score, 4))

    def compute_priority(
        self,
        memory: Memory,
        relevance_score: float,
        query_has_terms: bool = True,
    ) -> Tuple[float, str]:
        """
        Compute final composite priority score and determine dominant selection reason.
        
        Mathematical Guarantees:
        1. Relevance Dominance:
           Any memory with genuine query relevance (relevance > 0.0) is strictly
           partitioned above any unrelated memory (relevance == 0.0).
           Base score for relevant memory >= 1.0000; max score for unrelated memory <= 0.0500.
           Therefore, an unrelated VERBATIM memory can never outrank a relevant SUMMARY.
        2. Hierarchical Secondary Ordering:
           Within candidates of identical relevance:
           - Constraints (+0.15) and Decisions (+0.10) provide secondary boost.
           - Confidence (up to +0.08) provides tertiary ordering.
           - Memory tier (VERBATIM +0.10 vs SUMMARY +0.05) provides quaternary ordering.
        3. Deterministic Tie-Breaking:
           Handled downstream by sorting on (priority DESC, token_count ASC, memory_id ASC).
        """
        mem_tokens = set(self.tokenize(memory.content))

        is_constraint = bool(self.CONSTRAINT_KEYWORDS.intersection(mem_tokens))
        is_decision = bool(self.DECISION_KEYWORDS.intersection(mem_tokens))

        # Secondary, tertiary, and quaternary signals (bounded in [0.0, 0.40])
        secondary_boosts = 0.0
        if is_constraint:
            secondary_boosts += self.weights.constraint_boost
        if is_decision:
            secondary_boosts += self.weights.decision_boost

        if memory.tier == MemoryTier.VERBATIM.value:
            secondary_boosts += self.weights.verbatim_boost
        elif memory.tier == MemoryTier.SUMMARY.value:
            secondary_boosts += self.weights.summary_boost

        secondary_boosts += self.weights.confidence_weight * memory.confidence

        if query_has_terms:
            if relevance_score > 0.0:
                # Relevant partition: base offset 1.0 ensures any relevant memory
                # strictly outranks all unrelated memories.
                # Relevance scaled by relevance_weight (default 2.0x weight).
                priority = (
                    1.0
                    + (relevance_score * self.weights.relevance_weight * 2.0)
                    + secondary_boosts
                )
            else:
                # Unrelated partition: strictly bounded below 0.05
                priority = secondary_boosts * 0.10
        else:
            # Query was empty / unconstrained: rank purely by intrinsic importance
            priority = secondary_boosts

        priority = round(priority, 4)

        # Attribute dominant selection reason
        if is_constraint and (not query_has_terms or relevance_score > 0.0):
            reason = "explicit constraint"
        elif is_decision and (not query_has_terms or relevance_score > 0.0):
            reason = "important decision"
        elif relevance_score >= 0.7:
            reason = "high relevance"
        elif memory.tier == MemoryTier.SUMMARY.value and relevance_score > 0.2:
            reason = "summary relevant"
        elif relevance_score > 0.0:
            reason = "relevant memory"
        elif memory.confidence >= 0.95:
            reason = "high confidence"
        else:
            reason = "baseline active memory"

        return priority, reason

