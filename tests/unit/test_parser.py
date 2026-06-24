"""Tests for Layer 7 bundle parsing."""

import pytest

from layer7_kong_migration.ingestion.parser import PolicyParser


@pytest.fixture
def parser():
    return PolicyParser()


SIMPLE_POLICY = """<?xml version="1.0" encoding="UTF-8"?>
<wsp:Policy xmlns:L7p="http://www.layer7tech.com/ws/policy"
            xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy">
    <wsp:All wsp:Usage="Required">
        <L7p:HttpBasic/>
        <L7p:RateLimit>
            <L7p:MaxRequestsPerSecond intValue="100"/>
        </L7p:RateLimit>
        <L7p:HttpRoutingAssertion>
            <L7p:ProtectedServiceUrl stringValue="https://backend.example.com/api"/>
        </L7p:HttpRoutingAssertion>
    </wsp:All>
</wsp:Policy>"""


RESTMAN_BUNDLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<l7:Item xmlns:l7="http://ns.l7tech.com/2010/04/gateway-management">
    <l7:Name>Test Bundle</l7:Name>
    <l7:Type>BUNDLE</l7:Type>
    <l7:Resource>
        <l7:Bundle>
            <l7:References>
                <l7:Item>
                    <l7:Name>Test Service</l7:Name>
                    <l7:Id>abc123</l7:Id>
                    <l7:Type>SERVICE</l7:Type>
                    <l7:Resource>
                        <l7:Service id="abc123">
                            <l7:ServiceDetail folderId="/test">
                                <l7:Name>Test Service</l7:Name>
                                <l7:ServiceMappings>
                                    <l7:HttpMapping>
                                        <l7:UrlPattern>/api/test/*</l7:UrlPattern>
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
        <L7p:Authentication>
            <L7p:IdentityProviderOid goidValue="0000000000000000fffffffffffffffe"/>
        </L7p:Authentication>
        <L7p:RateLimit>
            <L7p:MaxRequestsPerSecond intValue="50"/>
        </L7p:RateLimit>
        <L7p:CorsAssertion>
            <L7p:AcceptedOrigins>
                <L7p:item stringValue="https://app.example.com"/>
            </L7p:AcceptedOrigins>
            <L7p:MaxAge intValue="7200"/>
        </L7p:CorsAssertion>
        <L7p:HttpRoutingAssertion>
            <L7p:ProtectedServiceUrl stringValue="https://backend.internal:8443/api/test"/>
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


def test_parse_standalone_policy(parser):
    bundle = parser.parse_bundle(SIMPLE_POLICY)
    assert len(bundle.services) == 1
    assertions = bundle.services[0].assertions
    assert len(assertions) == 3
    types = [a.assertion_type for a in assertions]
    assert "HttpBasic" in types
    assert "RateLimit" in types
    assert "HttpRoutingAssertion" in types


def test_parse_rate_limit_config(parser):
    bundle = parser.parse_bundle(SIMPLE_POLICY)
    rate_limit = next(a for a in bundle.services[0].assertions if a.assertion_type == "RateLimit")
    assert rate_limit.configuration["max_requests_per_second"] == 100


def test_parse_routing_url(parser):
    bundle = parser.parse_bundle(SIMPLE_POLICY)
    routing = next(a for a in bundle.services[0].assertions if a.assertion_type == "HttpRoutingAssertion")
    assert routing.configuration["protected_service_url"] == "https://backend.example.com/api"


def test_parse_restman_bundle(parser):
    bundle = parser.parse_bundle(RESTMAN_BUNDLE)
    assert bundle.source_format == "restman"
    assert len(bundle.services) == 1
    svc = bundle.services[0]
    assert svc.name == "Test Service"
    assert svc.resolution_path == "/api/test/*"
    assert len(svc.assertions) == 5


def test_parse_restman_assertion_types(parser):
    bundle = parser.parse_bundle(RESTMAN_BUNDLE)
    types = {a.assertion_type for a in bundle.services[0].assertions}
    assert types == {"HttpBasic", "Authentication", "RateLimit", "CorsAssertion", "HttpRoutingAssertion"}


def test_parse_cors_config(parser):
    bundle = parser.parse_bundle(RESTMAN_BUNDLE)
    cors = next(a for a in bundle.services[0].assertions if a.assertion_type == "CorsAssertion")
    assert "https://app.example.com" in cors.configuration["accepted_origins"]
    assert cors.configuration["max_age"] == 7200


def test_raw_xml_captured(parser):
    bundle = parser.parse_bundle(SIMPLE_POLICY)
    for assertion in bundle.services[0].assertions:
        assert assertion.raw_xml, f"raw_xml not captured for {assertion.assertion_type}"


def test_endpoint_extraction(parser):
    bundle = parser.parse_bundle(RESTMAN_BUNDLE)
    svc = bundle.services[0]
    assert len(svc.endpoints) >= 1
    assert "backend.internal" in svc.endpoints[0].url
