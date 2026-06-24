"""Tests for assertion-specific extractors."""

from lxml import etree

from layer7_kong_migration.ingestion.extractors import extract_assertion_config

NS = {
    "L7p": "http://www.layer7tech.com/ws/policy",
    "wsp": "http://schemas.xmlsoap.org/ws/2002/12/policy",
}


def _parse(xml: str) -> etree._Element:
    return etree.fromstring(xml.encode("utf-8"))


def test_extract_rate_limit():
    elem = _parse("""
    <L7p:RateLimit xmlns:L7p="http://www.layer7tech.com/ws/policy">
        <L7p:MaxRequestsPerSecond intValue="500"/>
        <L7p:CounterName stringValue="my-counter"/>
    </L7p:RateLimit>""")
    config = extract_assertion_config("RateLimit", elem, NS)
    assert config["max_requests_per_second"] == 500
    assert config["counter_name"] == "my-counter"


def test_extract_cors():
    elem = _parse("""
    <L7p:CorsAssertion xmlns:L7p="http://www.layer7tech.com/ws/policy">
        <L7p:AcceptedOrigins>
            <L7p:item stringValue="https://a.com"/>
            <L7p:item stringValue="https://b.com"/>
        </L7p:AcceptedOrigins>
        <L7p:MaxAge intValue="1800"/>
        <L7p:AllowCredentials booleanValue="true"/>
    </L7p:CorsAssertion>""")
    config = extract_assertion_config("CorsAssertion", elem, NS)
    assert len(config["accepted_origins"]) == 2
    assert config["max_age"] == 1800
    assert config["allow_credentials"] is True


def test_extract_http_routing():
    elem = _parse("""
    <L7p:HttpRoutingAssertion xmlns:L7p="http://www.layer7tech.com/ws/policy">
        <L7p:ProtectedServiceUrl stringValue="https://api.example.com/v1"/>
        <L7p:ConnectionTimeout intValue="15000"/>
        <L7p:Timeout intValue="45000"/>
        <L7p:FollowRedirects booleanValue="true"/>
    </L7p:HttpRoutingAssertion>""")
    config = extract_assertion_config("HttpRoutingAssertion", elem, NS)
    assert config["protected_service_url"] == "https://api.example.com/v1"
    assert config["connection_timeout"] == 15000
    assert config["follow_redirects"] is True


def test_extract_set_variable():
    elem = _parse("""
    <L7p:SetVariable xmlns:L7p="http://www.layer7tech.com/ws/policy">
        <L7p:VariableToSet stringValue="myVar"/>
        <L7p:Expression stringValue="${request.http.header.host}"/>
        <L7p:DataType stringValue="string"/>
    </L7p:SetVariable>""")
    config = extract_assertion_config("SetVariable", elem, NS)
    assert config["variable_to_set"] == "myVar"
    assert "host" in config["expression"]


def test_extract_javascript():
    elem = _parse("""
    <L7p:JavaScript xmlns:L7p="http://www.layer7tech.com/ws/policy">
        <L7p:ScriptName stringValue="transform"/>
        <L7p:Script stringValue="var x = 1;"/>
        <L7p:ExecutionTimeout intValue="3000"/>
    </L7p:JavaScript>""")
    config = extract_assertion_config("JavaScript", elem, NS)
    assert config["script_name"] == "transform"
    assert config["script"] == "var x = 1;"
    assert config["execution_timeout"] == 3000


def test_extract_generic_fallback():
    elem = _parse("""
    <L7p:UnknownAssertion xmlns:L7p="http://www.layer7tech.com/ws/policy">
        <L7p:SomeValue stringValue="test"/>
        <L7p:SomeNumber intValue="42"/>
    </L7p:UnknownAssertion>""")
    config = extract_assertion_config("UnknownAssertion", elem, NS)
    assert config["SomeValue"] == "test"
    assert config["SomeNumber"] == 42
