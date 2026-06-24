"""Claude API client wrapper with retry logic and rate limiting."""

import time

import anthropic

from layer7_kong_migration.ai.config import get_ai_config


class AIClient:
    def __init__(self) -> None:
        config = get_ai_config()
        self.client = anthropic.Anthropic()
        self.model = config["model"]
        self.max_tokens = config["max_tokens"]
        self.rate_limit_delay = config["rate_limit_delay_ms"] / 1000
        self.max_retries = config["max_retries"]
        self._last_call_time = 0.0

    def analyze_assertion(self, system_prompt: str, user_prompt: str) -> dict:
        self._rate_limit()
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                text = response.content[0].text
                return self._parse_response(text)
            except anthropic.RateLimitError:
                wait = 2 ** (attempt + 1)
                print(f"Rate limited, waiting {wait}s...")
                time.sleep(wait)
            except anthropic.APIError as e:
                if attempt == self.max_retries - 1:
                    raise
                print(f"API error (attempt {attempt + 1}): {e}")
                time.sleep(1)
        return {}

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_call_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_call_time = time.time()

    def _parse_response(self, text: str) -> dict:
        import json

        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            return {"error": "Failed to parse AI response", "raw": text[:500]}
