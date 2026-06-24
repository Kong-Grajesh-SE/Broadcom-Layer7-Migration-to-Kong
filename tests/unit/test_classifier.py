"""Tests for assertion classification."""

import pytest

from layer7_kong_migration.analysis.classifier import AssertionClassifier
from layer7_kong_migration.models.ir import AssertionConfig, Complexity, ReviewFlag


@pytest.fixture
def classifier():
    return AssertionClassifier()


def _make_assertion(assertion_type: str) -> AssertionConfig:
    return AssertionConfig(name=assertion_type, assertion_type=assertion_type)


def test_direct_classification(classifier):
    a = _make_assertion("HttpBasic")
    from layer7_kong_migration.models.ir import PolicyBundle, ServiceDefinition
    bundle = PolicyBundle(
        name="test",
        services=[ServiceDefinition(name="svc", assertions=[a])],
    )
    classifier.classify_bundle(bundle)
    assert a.complexity == Complexity.DIRECT
    assert a.confidence == 1.0


def test_conditional_classification(classifier):
    a = _make_assertion("Authentication")
    from layer7_kong_migration.models.ir import PolicyBundle, ServiceDefinition
    bundle = PolicyBundle(
        name="test",
        services=[ServiceDefinition(name="svc", assertions=[a])],
    )
    classifier.classify_bundle(bundle)
    assert a.complexity == Complexity.CONDITIONAL
    assert a.review_flag == ReviewFlag.IDP_CONFIG_REQUIRED


def test_custom_classification(classifier):
    a = _make_assertion("JavaScript")
    from layer7_kong_migration.models.ir import PolicyBundle, ServiceDefinition
    bundle = PolicyBundle(
        name="test",
        services=[ServiceDefinition(name="svc", assertions=[a])],
    )
    classifier.classify_bundle(bundle)
    assert a.complexity == Complexity.CUSTOM
    assert a.review_flag == ReviewFlag.CUSTOM_PLUGIN_REQUIRED


def test_unknown_assertion_classified_as_custom(classifier):
    a = _make_assertion("SomeUnknownAssertion")
    from layer7_kong_migration.models.ir import PolicyBundle, ServiceDefinition
    bundle = PolicyBundle(
        name="test",
        services=[ServiceDefinition(name="svc", assertions=[a])],
    )
    classifier.classify_bundle(bundle)
    assert a.complexity == Complexity.CUSTOM


def test_skip_assertions(classifier):
    a = _make_assertion("CommentAssertion")
    from layer7_kong_migration.models.ir import PolicyBundle, ServiceDefinition
    bundle = PolicyBundle(
        name="test",
        services=[ServiceDefinition(name="svc", assertions=[a])],
    )
    classifier.classify_bundle(bundle)
    assert a.complexity == Complexity.DIRECT


@pytest.mark.parametrize("assertion_type,expected", [
    ("RateLimit", Complexity.DIRECT),
    ("CorsAssertion", Complexity.DIRECT),
    ("RequestSizeLimit", Complexity.DIRECT),
    ("RemoteIpRange", Complexity.DIRECT),
    ("ThroughputQuota", Complexity.CONDITIONAL),
    ("DecodeJsonWebToken", Complexity.CONDITIONAL),
    ("SslAssertion", Complexity.CONDITIONAL),
    ("XslTransformation", Complexity.CUSTOM),
    ("JdbcQuery", Complexity.CUSTOM),
    ("CustomAssertion", Complexity.CUSTOM),
])
def test_classification_matrix(classifier, assertion_type, expected):
    a = _make_assertion(assertion_type)
    from layer7_kong_migration.models.ir import PolicyBundle, ServiceDefinition
    bundle = PolicyBundle(
        name="test",
        services=[ServiceDefinition(name="svc", assertions=[a])],
    )
    classifier.classify_bundle(bundle)
    assert a.complexity == expected
