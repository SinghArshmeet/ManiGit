"""
Optional Gemini Model Adapter for ManiGit.

Connects to Google Gemini API via standard library HTTP requests.
Requires GEMINI_API_KEY environment variable or explicit api_key in constructor.
Zero required external dependencies beyond standard library.
"""

import json
import os
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request

from manigit.core.tokens import estimate_tokens
from manigit.models.base import ModelAdapter


class GeminiModelAdapter(ModelAdapter):
    """
    Lightweight, provider-specific adapter for Google Gemini models.
    
    Adheres strictly to the ModelAdapter contract:
    - generate()
    - summarize()
    - judge_memory()
    - count_tokens()
    
    Safety:
    - Never logs or exposes API keys.
    - Fails clearly with actionable ValueError if GEMINI_API_KEY is missing.
    """

    DEFAULT_MODEL = "gemini-1.5-flash"
    API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL") or self.DEFAULT_MODEL
        self.timeout_seconds = timeout_seconds

    def _require_api_key(self) -> str:
        """Validate presence of API key without exposing it."""
        key = self._api_key or os.getenv("GEMINI_API_KEY")
        if not key or not key.strip():
            raise ValueError(
                "Gemini API key is not configured. Set the GEMINI_API_KEY environment variable "
                "or pass api_key to GeminiModelAdapter."
            )
        return key.strip()

    def _call_api(self, contents: List[Dict[str, Any]], system_instruction: Optional[str] = None) -> str:
        """Execute HTTP request to Gemini generateContent endpoint."""
        key = self._require_api_key()
        url = self.API_URL_TEMPLATE.format(model=self.model_name, key=key)

        body: Dict[str, Any] = {"contents": contents}
        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url=url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            # Scrub API key from error message if present in URL
            clean_error = error_body.replace(key, "[REDACTED_KEY]")
            raise RuntimeError(f"Gemini API HTTP {e.code} error: {clean_error}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to connect to Gemini API: {e.reason}") from None

        try:
            candidates = resp_data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts).strip()
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Malformed Gemini API response format: {resp_data}") from e

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate response text for prompt."""
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        return self._call_api(contents)

    def summarize(
        self,
        text: str,
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Summarize multi-turn conversation text."""
        instruction = "You are a concise, factual summarizer. Extract and synthesize key technical facts, constraints, and decisions."
        prompt = f"Text to summarize:\n{text}"
        if context:
            prompt += f"\n\nPrior Context:\n{context}"
        if max_tokens:
            prompt += f"\n\nConstraint: Maximum {max_tokens} tokens."

        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        return self._call_api(contents, system_instruction=instruction)

    def judge_memory(
        self,
        message_content: str,
        active_memories: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Evaluate memory tier and return structured judgment."""
        instruction = (
            "Analyze the conversation event and return a JSON object with keys: "
            "'tier' (VERBATIM, SUMMARY, or ARCHIVED), 'confidence' (float 0.0-1.0), "
            "'reason' (string), 'importance' (high, medium, low), 'needs_summary' (bool), "
            "'extracted_fact' (string or null). Return raw JSON only."
        )
        prompt = f"Message to evaluate:\n{message_content}"
        if active_memories:
            prompt += f"\n\nActive Memories:\n{json.dumps(active_memories)}"

        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        raw = self._call_api(contents, system_instruction=instruction)

        # Parse JSON from response
        try:
            # Handle potential markdown code block
            clean = raw.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            elif clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            return json.loads(clean.strip())
        except Exception:
            return {
                "tier": "VERBATIM",
                "confidence": 0.65,
                "reason": "Failed to parse structured judgment from model; preserved conservatively.",
                "importance": "medium",
                "needs_summary": False,
                "extracted_fact": message_content.strip(),
            }

    def count_tokens(self, text: str) -> int:
        """Estimate tokens for text string."""
        return estimate_tokens(text)
