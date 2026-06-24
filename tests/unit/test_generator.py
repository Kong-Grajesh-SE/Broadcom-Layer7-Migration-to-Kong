"""Tests for Kong configuration generation."""

import pytest

from layer7_kong_migration.analysis.classifier import AssertionClassifier
from layer7_kong_migration.generation.kong import KongGenerator
from layer7_kong_migration.ingestion.parser import PolicyParser


SAMPLE_BUNDLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<l7:Item xmlns:l7="http://ns.l7tech.com/2010/04/gateway-management">
    <l7:Name>Gen Test</l7:Name>
    <l7:Type>BUNDLE</l7:Type>
    <l7:Resource>
        <l7:Bundle>
            <l7:References>
                <l7:Item>
                    <l7:Name>Test API</l7:Name>
                    <l7:Id>gen123</l7:Id>
                    <l7:Type>SERVICE</l7:Type>
                    <l7:Resource>
                        <l7:Service id="gen123">
                            <l7:ServiceDetail folderId="/test">
                                <l7:Name>Test API</l7:Name>
                                <l7:ServiceMappings>
                                    <l7:HttpMapping>
                                        <l7:UrlPattern>/api/gen/*</l7:UrlPattern>
                                    </l7:HttpMapping>
                                </l7:ServiceMappings>
                            </l7:ServiceDetail>
                            <l7:Resources>
                                <l7:ResourceSet>
                                    <l7:Resource type="policy"><![CDATA[<?xml version="1.0" encoding="UTF-8"?>
<wsp:Policy xmlns:L7p="http://www.layer7tech.com/ws/policy"
            xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy">
    <wsp:All wsp:Usage="Required">
        <L7p:HttpBasic/>
        <L7p:RateLimit>
            <L7p:MaxRequestsPerSecond intValue="200"/>
        </L7p:RateLimit>
        <L7p:CorsAssertion>
            <L7p:AcceptedOrigins>
                <L7p:item stringValue="*"/>
            </L7p:AcceptedOrigins>
        </L7p:CorsAssertion>
        <L7p:HttpRoutingAssertion>
            <L7p:ProtectedServiceUrl stringValue="https://backend.test:8443/api"/>
        </L7p:HttpRoutingAssertion>
    </wsp:All>
</wsp:Policy>]]></l7:Resource>
                                </l7:ResourceSet>
                            </l7:Resources>
                        </l7:Service>
                    </l7:Resource>
                </l7:Item>
            </l7:References>
            <l7:Mappings/>
        </l7:Bundle>
    </l7:Resource>
</l7:Item>"""


@pytest.fixture
def classified_bundle():
    parser = PolicyParser()
    bundle = parser.parse_bundle(SAMPLE_BUNDLE)
    classifier = AssertionClassifier()
    return classifier.classify_bundle(bundle)


def test_generates_yaml(classified_bundle):
    gen = KongGenerator()
    yaml_str = gen.generate(classified_bundle)
    assert "_format_version: '3.0'" in yaml_str
    assert "services:" in yaml_str


def test_generates_service(classified_bundle):
    gen = KongGenerator()
    yaml_str = gen.generate(classified_bundle)
    assert "test-api" in yaml_str
    assert "backend.test" in yaml_str


def test_generates_route(classified_bundle):
    gen = KongGenerator()
    yaml_str = gen.generate(classified_bundle)
    assert "route" in yaml_str
    assert "/api/gen/*" in yaml_str


def test_generates_plugins(classified_bundle):
    gen = KongGenerator()
    yaml_str = gen.generate(classified_bundle)
    assert "basic-auth" in yaml_str
    assert "rate-limiting" in yaml_str
    assert "cors" in yaml_str


def test_generates_consumers_for_auth(classified_bundle):
    gen = KongGenerator()
    yaml_str = gen.generate(classified_bundle)
    assert "consumers:" in yaml_str
    assert "test-consumer" in yaml_str
    assert "placeholder" in yaml_str


def test_migration_tags(classified_bundle):
    gen = KongGenerator()
    yaml_str = gen.generate(classified_bundle)
    assert "migrated-from-layer7" in yaml_str
