"""AI analysis orchestrator.

Routes CUSTOM (and optionally CONDITIONAL) assertions through:
  pattern match → cache check → Claude API → cache store → pattern learning
"""

from layer7_kong_migration.ai.cache import AICache
from layer7_kong_migration.ai.client import AIClient
from layer7_kong_migration.ai.config import get_ai_config
from layer7_kong_migration.ai.learner import PatternLearner
from layer7_kong_migration.ai.prompts import (
    CONDITIONAL_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_user_prompt,
)
from layer7_kong_migration.models.ir import (
    AssertionConfig,
    Complexity,
    PolicyBundle,
    ReviewFlag,
)
from layer7_kong_migration.patterns.matcher import PatternMatcher


class AIAnalyzer:
    def __init__(self, cache_dir: str = ".cache/ai", patterns_dir: str = "knowledge/patterns") -> None:
        self.client = AIClient()
        self.cache = AICache(cache_dir)
        self.matcher = PatternMatcher(patterns_dir)
        self.learner = PatternLearner(patterns_dir)
        self.config = get_ai_config()
        self.stats = {"cache_hits": 0, "pattern_hits": 0, "api_calls": 0, "errors": 0}

    def analyze_bundle(
        self,
        bundle: PolicyBundle,
        include_conditional: bool = False,
    ) -> PolicyBundle:
        for svc in bundle.services:
            for assertion in svc.assertions:
                if assertion.complexity == Complexity.CUSTOM:
                    self._analyze_assertion(assertion, SYSTEM_PROMPT)
                elif include_conditional and assertion.complexity == Complexity.CONDITIONAL:
                    self._analyze_assertion(assertion, CONDITIONAL_SYSTEM_PROMPT)

        for pol in bundle.shared_policies:
            for assertion in pol.assertions:
                if assertion.complexity == Complexity.CUSTOM:
                    self._analyze_assertion(assertion, SYSTEM_PROMPT)

        return bundle

    def _analyze_assertion(self, assertion: AssertionConfig, system_prompt: str) -> None:
        pattern_result = self.matcher.match(assertion)
        if pattern_result and pattern_result.get("confidence", 0) >= self.config["confidence_auto_threshold"]:
            assertion.kong_mapping = pattern_result
            assertion.confidence = pattern_result["confidence"]
            self.stats["pattern_hits"] += 1
            return

        cache_key = self.cache.cache_key(
            assertion.assertion_type,
            assertion.configuration,
            assertion.resource_content,
        )
        cached = self.cache.get(cache_key)
        if cached:
            assertion.kong_mapping = cached
            assertion.confidence = cached.get("confidence", 0.5)
            self.stats["cache_hits"] += 1
            self._apply_confidence_flags(assertion)
            return

        try:
            user_prompt = build_user_prompt(
                assertion.assertion_type,
                assertion.raw_xml,
                assertion.configuration,
                assertion.resource_content,
                self.config["max_resource_chars"],
            )
            result = self.client.analyze_assertion(system_prompt, user_prompt)

            if "error" not in result:
                self.cache.put(cache_key, result)
                assertion.kong_mapping = result
                assertion.confidence = result.get("confidence", 0.5)
                self._apply_confidence_flags(assertion)
                self.learner.learn(assertion, result)
                self.stats["api_calls"] += 1
            else:
                self.stats["errors"] += 1
        except Exception as e:
            print(f"AI analysis failed for {assertion.assertion_type}: {e}")
            self.stats["errors"] += 1

    def _apply_confidence_flags(self, assertion: AssertionConfig) -> None:
        conf = assertion.confidence
        if conf >= self.config["confidence_auto_threshold"]:
            if assertion.review_flag == ReviewFlag.CUSTOM_PLUGIN_REQUIRED:
                assertion.review_flag = ReviewFlag.NONE
        elif conf >= self.config["confidence_review_threshold"]:
            if assertion.review_flag == ReviewFlag.CUSTOM_PLUGIN_REQUIRED:
                assertion.review_flag = ReviewFlag.MANUAL_REVIEW
                assertion.review_reason = f"AI confidence {conf:.0%} - review recommended"
