"""
Deterministic Rule Engine for Memory Intelligence.

Extracts signals from conversation text to identify:
- High-priority / VERBATIM items (constraints, code, errors, numbers, paths, IDs, URLs)
- Low-value / ARCHIVED items (greetings, acknowledgements, small talk)
"""

from dataclasses import dataclass, field
import re
from typing import List, Optional

from manigit.core.models import MemoryTier


@dataclass(frozen=True)
class RuleSignal:
    """Structured signal emitted by the rule engine."""
    suggested_tier: Optional[str]
    confidence: float
    matched_rules: List[str] = field(default_factory=list)
    reason: str = ""
    is_definitive: bool = False  # If True, can bypass LLM judge without ambiguity


class RuleEngine:
    """
    Evaluates text against deterministic patterns for immediate high-confidence classification.
    """

    # Regex patterns for High-Priority / Verbatim information
    URL_PATTERN = re.compile(r"https?://[^\s]+|ftp://[^\s]+", re.IGNORECASE)
    FILE_PATH_PATTERN = re.compile(
        r"(?:[a-zA-Z]:[/\\]|[./\\]|[a-zA-Z0-9_\-.]+[/\\])[a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+",
        re.IGNORECASE,
    )
    UUID_OR_ID_PATTERN = re.compile(
        r"\b(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|"
        r"(?:id|msg|mem|usr|tx|commit|c)_[0-9a-zA-Z]{6,32}|[A-Z0-9_]{16,64})\b"
    )
    NUMERIC_QUANTITY_PATTERN = re.compile(
        r"(?:[\$\€\£\¥]\s*\d+(?:,\d{3})*(?:\.\d+)?|\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|tokens?|ms|seconds?|mins?|gb|mb|kb|users?|requests?|usd)\b)"
    )
    DATE_PATTERN = re.compile(
        r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?,? \d{4})\b",
        re.IGNORECASE,
    )
    CODE_OR_STACKTRACE_PATTERN = re.compile(
        r"```.*?```|Traceback \(most recent call last\):|\b(?:def |class |import |from [a-zA-Z0-9_]+ import |return |function\b|\bconst |let |var )\b",
        re.DOTALL,
    )
    ERROR_PATTERN = re.compile(
        r"\b(?:Error|Exception|HTTP (?:4\d\d|5\d\d)|Fatal|Fail(?:ed|ure)?|Crash|Timeout|SyntaxError|TypeError|ValueError|KeyError)\b:?",
        re.IGNORECASE,
    )
    KEY_VALUE_CONFIG_PATTERN = re.compile(
        r"\b[A-Z0-9_]{3,30}\s*=\s*['\"a-zA-Z0-9_.\-/:~]+"
    )
    EXPLICIT_CONSTRAINT_PATTERN = re.compile(
        r"\b(?:must(?:\s+not)?|cannot|strictly|required?|mandatory|never|always|do not|don't|only use|limit to)\b",
        re.IGNORECASE,
    )
    EXPLICIT_DECISION_PATTERN = re.compile(
        r"\b(?:we(?:'ve)? decided|decision is|we will use|agreed on|switching to|chosen|selected|agreed that)\b",
        re.IGNORECASE,
    )
    USER_PREFERENCE_PATTERN = re.compile(
        r"\b(?:my preference is|i prefer|i like|i want you to always|format as|style preference)\b",
        re.IGNORECASE,
    )

    GREETING_WORDS = {
        "hi", "hello", "hey", "there", "good", "morning", "afternoon", "evening",
        "howdy", "greetings", "welcome", "yo"
    }
    ACKNOWLEDGEMENT_WORDS = {
        "ok", "okay", "got", "it", "sounds", "good", "thanks", "thank", "you",
        "cool", "acknowledged", "understood", "sure", "thing", "noted", "alright",
        "fine", "perfect", "cheers", "bye", "goodbye", "yes", "no", "yep", "nope",
        "great", "awesome", "nice"
    }
    SMALL_TALK_PATTERN = re.compile(
        r"^(?:how are you|how's it going|what's up|nice to meet you|have a (?:great|good) day)[?.,! ]*$",
        re.IGNORECASE,
    )

    def evaluate(self, text: str, existing_memories: Optional[List[str]] = None) -> RuleSignal:
        """
        Evaluate text and return a structured RuleSignal.
        """
        cleaned = text.strip()
        matched_rules: List[str] = []

        if not cleaned:
            return RuleSignal(
                suggested_tier=MemoryTier.ARCHIVED.value,
                confidence=1.0,
                matched_rules=["empty_text"],
                reason="Empty input text archived.",
                is_definitive=True,
            )

        # Check for duplicates if existing memories are provided
        if existing_memories:
            cleaned_lower = cleaned.lower()
            for mem_content in existing_memories:
                if cleaned_lower == mem_content.strip().lower():
                    return RuleSignal(
                        suggested_tier=MemoryTier.ARCHIVED.value,
                        confidence=0.98,
                        matched_rules=["duplicate_statement"],
                        reason="Identical statement already exists in active memory.",
                        is_definitive=True,
                    )

        # 1. Check for Archive Candidates (Greetings, acknowledgements, small talk)
        words_only = re.findall(r"[a-zA-Z]+", cleaned.lower())
        if words_only:
            is_all_greeting = all(w in self.GREETING_WORDS for w in words_only)
            is_all_ack = all(w in self.ACKNOWLEDGEMENT_WORDS for w in words_only)
            is_all_filler = all(w in (self.GREETING_WORDS | self.ACKNOWLEDGEMENT_WORDS) for w in words_only)

            if is_all_greeting:
                matched_rules.append("greeting")
            elif is_all_ack:
                matched_rules.append("acknowledgement")
            elif is_all_filler:
                matched_rules.append("acknowledgement")

        if self.SMALL_TALK_PATTERN.match(cleaned):
            matched_rules.append("small_talk")

        if matched_rules:
            return RuleSignal(
                suggested_tier=MemoryTier.ARCHIVED.value,
                confidence=0.95,
                matched_rules=matched_rules,
                reason=f"Matched conversational non-factual filler: {', '.join(matched_rules)}",
                is_definitive=True,
            )

        # 2. Check for High-Priority / Verbatim Indicators
        is_code_or_trace = bool(self.CODE_OR_STACKTRACE_PATTERN.search(cleaned))
        if is_code_or_trace:
            matched_rules.append("code_or_stacktrace")

        if self.ERROR_PATTERN.search(cleaned):
            matched_rules.append("error_or_exception")

        if self.URL_PATTERN.search(cleaned):
            matched_rules.append("url")

        if self.FILE_PATH_PATTERN.search(cleaned):
            matched_rules.append("file_path")

        if self.UUID_OR_ID_PATTERN.search(cleaned):
            matched_rules.append("identifier_or_hash")

        if self.NUMERIC_QUANTITY_PATTERN.search(cleaned):
            matched_rules.append("exact_numeric_quantity")

        if self.DATE_PATTERN.search(cleaned):
            matched_rules.append("date_or_deadline")

        if self.KEY_VALUE_CONFIG_PATTERN.search(cleaned):
            matched_rules.append("key_value_config")

        if self.EXPLICIT_CONSTRAINT_PATTERN.search(cleaned):
            matched_rules.append("explicit_constraint")

        if self.EXPLICIT_DECISION_PATTERN.search(cleaned):
            matched_rules.append("explicit_decision")

        if self.USER_PREFERENCE_PATTERN.search(cleaned):
            matched_rules.append("user_preference")

        # Evaluate matches
        if matched_rules:
            # Code, explicit constraints, decisions, configs, and errors are definitive verbatim
            definitive_triggers = {
                "code_or_stacktrace",
                "explicit_constraint",
                "explicit_decision",
                "key_value_config",
                "error_or_exception",
                "identifier_or_hash",
            }
            has_definitive = bool(definitive_triggers.intersection(matched_rules))
            confidence = 0.95 if has_definitive else 0.85

            return RuleSignal(
                suggested_tier=MemoryTier.VERBATIM.value,
                confidence=confidence,
                matched_rules=matched_rules,
                reason=f"Matched verbatim factual patterns: {', '.join(matched_rules)}",
                is_definitive=has_definitive,
            )

        # 3. No definitive rule match -> Ambiguous, requires semantic judge
        return RuleSignal(
            suggested_tier=None,
            confidence=0.50,
            matched_rules=[],
            reason="No deterministic rule matched; passes to semantic judge.",
            is_definitive=False,
        )
