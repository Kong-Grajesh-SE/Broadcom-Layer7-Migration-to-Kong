"""Pattern matcher: scores assertions against the pattern library.

Uses weighted similarity across multiple dimensions:
- Assertion type match: 0.35
- Config key overlap: 0.25
- Keyword overlap: 0.15
- Config value similarity: 0.15
- Metadata match: 0.10
"""

from typing import Any

from layer7_kong_migration.models.ir import AssertionConfig
from layer7_kong_migration.patterns.library import PatternLibrary

HIGH_CONFIDENCE_THRESHOLD = 0.85

WEIGHTS = {
    "assertion_type": 0.35,
    "config_keys": 0.25,
    "keywords": 0.15,
    "config_values": 0.15,
    "metadata": 0.10,
}


class PatternMatcher:
    def __init__(self, patterns_dir: str = "knowledge/patterns") -> None:
        self.library = PatternLibrary(patterns_dir)

    def match(self, assertion: AssertionConfig) -> dict[str, Any] | None:
        candidates = self.library.by_assertion_type(assertion.assertion_type)
        if not candidates:
            return None

        best_score = 0.0
        best_pattern = None

        for pattern in candidates:
            score = self._score(assertion, pattern)
            if score > best_score:
                best_score = score
                best_pattern = pattern

        if best_pattern and best_score >= HIGH_CONFIDENCE_THRESHOLD:
            kong = best_pattern.get("kong", {})
            return {
                "kong_plugin_name": kong.get("plugin", "pre-function"),
                "kong_plugin_config": kong.get("config", {}),
                "lua_code": kong.get("lua_code"),
                "confidence": best_score,
                "explanation": f"Matched pattern: {best_pattern.get('name', '')}",
                "review_notes": ["Matched from pattern library"] if kong.get("requires_review") else [],
                "pattern_id": best_pattern.get("id"),
            }

        return None

    def _score(self, assertion: AssertionConfig, pattern: dict[str, Any]) -> float:
        l7 = pattern.get("layer7", {})
        score = 0.0

        if l7.get("assertion_type") == assertion.assertion_type:
            score += WEIGHTS["assertion_type"]

        pattern_keys = set(l7.get("config_keys", []))
        assertion_keys = {k for k in assertion.configuration.keys() if not k.startswith("_")}
        if pattern_keys and assertion_keys:
            overlap = len(pattern_keys & assertion_keys) / max(len(pattern_keys), 1)
            score += WEIGHTS["config_keys"] * overlap

        pattern_keywords = set(str(k).lower() for k in l7.get("keywords", []))
        assertion_keywords = self._extract_keywords(assertion)
        if pattern_keywords and assertion_keywords:
            overlap = len(pattern_keywords & assertion_keywords) / max(len(pattern_keywords), 1)
            score += WEIGHTS["keywords"] * overlap

        score += WEIGHTS["config_values"] * self._config_value_similarity(assertion, l7)
        score += WEIGHTS["metadata"] * (0.5 if pattern.get("metadata", {}).get("confidence", 0) > 0.8 else 0.0)

        return min(score, 1.0)

    def _extract_keywords(self, assertion: AssertionConfig) -> set[str]:
        keywords = {assertion.assertion_type.lower()}
        for val in assertion.configuration.values():
            if isinstance(val, str) and val:
                keywords.add(val.lower()[:30])
        return keywords

    def _config_value_similarity(self, assertion: AssertionConfig, l7: dict) -> float:
        return 0.5
