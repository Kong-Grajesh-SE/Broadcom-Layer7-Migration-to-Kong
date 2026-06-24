"""Pattern learner: extracts high-confidence AI results as reusable YAML patterns."""

import hashlib
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from layer7_kong_migration.ai.config import get_ai_config
from layer7_kong_migration.models.ir import AssertionConfig

yaml = YAML()
yaml.default_flow_style = False


class PatternLearner:
    def __init__(self, patterns_dir: str = "knowledge/patterns") -> None:
        self.patterns_dir = Path(patterns_dir)
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        self.threshold = get_ai_config().get("confidence_auto_threshold", 0.85)

    def learn(self, assertion: AssertionConfig, result: dict[str, Any]) -> bool:
        confidence = result.get("confidence", 0)
        if confidence < self.threshold:
            return False

        pattern_id = self._generate_id(assertion)
        pattern_path = self.patterns_dir / f"ai-{pattern_id}.yaml"

        if pattern_path.exists():
            return False

        pattern = self._build_pattern(assertion, result, pattern_id)
        yaml.dump(pattern, pattern_path)
        return True

    def _generate_id(self, assertion: AssertionConfig) -> str:
        sig = f"{assertion.assertion_type}|{sorted(assertion.configuration.keys())}"
        short_hash = hashlib.md5(sig.encode()).hexdigest()[:8]
        return f"{assertion.assertion_type.lower()}-{short_hash}"

    def _build_pattern(
        self, assertion: AssertionConfig, result: dict[str, Any], pattern_id: str
    ) -> dict:
        config_keys = [k for k in assertion.configuration.keys() if not k.startswith("_")]
        return {
            "pattern": {
                "id": pattern_id,
                "name": f"AI-learned: {assertion.assertion_type}",
                "description": result.get("explanation", ""),
                "layer7": {
                    "assertion_type": assertion.assertion_type,
                    "config_keys": config_keys,
                    "keywords": self._extract_keywords(assertion),
                },
                "kong": {
                    "plugin": result.get("kong_plugin_name", "pre-function"),
                    "config": result.get("kong_plugin_config", {}),
                    "lua_code": result.get("lua_code"),
                    "requires_review": bool(result.get("review_notes")),
                },
                "metadata": {
                    "contributor": "ai-generated",
                    "confidence": result.get("confidence", 0),
                    "source_assertion": assertion.assertion_type,
                },
            }
        }

    def _extract_keywords(self, assertion: AssertionConfig) -> list[str]:
        keywords = [assertion.assertion_type.lower()]
        for key, value in assertion.configuration.items():
            if key.startswith("_"):
                continue
            if isinstance(value, str) and value:
                keywords.append(value.lower()[:30])
        return keywords[:10]
