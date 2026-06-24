"""Tests for Graphman JSON parser."""

import json
import tempfile
from pathlib import Path

import pytest

from layer7_kong_migration.ingestion.graphman import GraphmanParser


@pytest.fixture
def parser():
    return GraphmanParser()


IMPLODED_BUNDLE = {
    "services": [
        {
            "goid": "svc-001",
            "name": "Echo Service",
            "resolutionPath": "/api/v1/echo",
            "enabled": True,
            "folderPath": "/services",
            "policy": {
                "xml": (
                    '<wsp:Policy xmlns:L7p="http://www.layer7tech.com/ws/policy"'
                    ' xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy">'
                    "<wsp:All>"
                    "<L7p:RateLimit><L7p:MaxRequestsPerSecond "
                    'intValue="100"/></L7p:RateLimit>'
                    "<L7p:HttpRoutingAssertion><L7p:ProtectedServiceUrl "
                    'stringValue="http://backend:8080/echo"/>'
                    "</L7p:HttpRoutingAssertion>"
                    "</wsp:All></wsp:Policy>"
                )
            },
        }
    ],
    "policies": [
        {
            "goid": "pol-001",
            "name": "Shared Auth",
            "policyType": "FRAGMENT",
            "folderPath": "/policies",
            "policy": {
                "xml": (
                    '<wsp:Policy xmlns:L7p="http://www.layer7tech.com/ws/policy"'
                    ' xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy">'
                    "<wsp:All>"
                    "<L7p:HttpBasic/>"
                    "</wsp:All></wsp:Policy>"
                )
            },
        }
    ],
    "clusterProperties": [
        {"name": "env.backend.url", "value": "http://backend:8080"},
        {"name": "log.level", "value": "INFO"},
    ],
}


def test_parse_imploded_services(parser):
    bundle = parser._parse_imploded(IMPLODED_BUNDLE, "test", "test.json")
    assert len(bundle.services) >= 1
    svc = next(s for s in bundle.services if s.name == "Echo Service")
    assert svc.resolution_path == "/api/v1/echo"
    assert svc.enabled is True


def test_parse_imploded_assertions(parser):
    bundle = parser._parse_imploded(IMPLODED_BUNDLE, "test", "test.json")
    svc = next(s for s in bundle.services if s.name == "Echo Service")
    types = {a.assertion_type for a in svc.assertions}
    assert "RateLimit" in types
    assert "HttpRoutingAssertion" in types


def test_parse_imploded_shared_policies(parser):
    bundle = parser._parse_imploded(IMPLODED_BUNDLE, "test", "test.json")
    assert len(bundle.shared_policies) == 1
    assert bundle.shared_policies[0].name == "Shared Auth"


def test_parse_imploded_cluster_properties(parser):
    bundle = parser._parse_imploded(IMPLODED_BUNDLE, "test", "test.json")
    assert bundle.cluster_properties["env.backend.url"] == "http://backend:8080"
    assert bundle.cluster_properties["log.level"] == "INFO"


def test_parse_file_json(parser, tmp_path):
    f = tmp_path / "bundle.json"
    f.write_text(json.dumps(IMPLODED_BUNDLE))
    bundle = parser.parse_file(f)
    assert bundle.name == "bundle"
    assert len(bundle.services) >= 1


def test_parse_empty_bundle(parser):
    bundle = parser._parse_imploded({}, "empty", "empty.json")
    assert len(bundle.services) == 0
    assert len(bundle.shared_policies) == 0


def test_code_to_xml_roundtrip(parser):
    code = {
        "All": [
            {"SetVariable": {"VariableToSet": {"stringValue": "myVar"}}},
            {"HttpRoutingAssertion": {}},
        ]
    }
    xml = parser._code_to_xml(code)
    assert "<wsp:All" in xml
    assert "L7p:SetVariable" in xml
    assert "L7p:HttpRoutingAssertion" in xml


def test_extract_policy_xml_from_code(parser):
    data = {
        "name": "Code Policy",
        "policy": {
            "code": {
                "All": [{"RateLimit": {"MaxRequestsPerSecond": {"intValue": 50}}}]
            }
        },
    }
    xml = parser._extract_policy_xml(data)
    assert xml is not None
    assert "wsp:Policy" in xml
    assert "RateLimit" in xml


def test_extract_policy_xml_from_json_string(parser):
    code_obj = {"All": [{"HttpBasic": {}}]}
    data = {
        "name": "JSON String Policy",
        "policy": {"json": json.dumps(code_obj)},
    }
    xml = parser._extract_policy_xml(data)
    assert xml is not None
    assert "HttpBasic" in xml


def test_parse_exploded_directory(parser, tmp_path):
    pol_file = tmp_path / "auth.policy.json"
    pol_file.write_text(
        json.dumps(
            {
                "goid": "p-100",
                "name": "Auth Fragment",
                "policyType": "FRAGMENT",
                "folderPath": "/shared",
                "policy": {
                    "xml": (
                        '<wsp:Policy xmlns:L7p="http://www.layer7tech.com/ws/policy"'
                        ' xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy">'
                        "<wsp:All><L7p:HttpBasic/></wsp:All></wsp:Policy>"
                    )
                },
            }
        )
    )
    bundle = parser._parse_exploded(tmp_path)
    assert len(bundle.shared_policies) == 1
    assert bundle.shared_policies[0].name == "Auth Fragment"


def test_service_policy_type_goes_to_services(parser):
    data = {
        "policies": [
            {
                "goid": "p-200",
                "name": "Service Policy",
                "policyType": "SERVICE",
                "folderPath": "/svc",
                "policy": {
                    "xml": (
                        '<wsp:Policy xmlns:L7p="http://www.layer7tech.com/ws/policy"'
                        ' xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy">'
                        "<wsp:All><L7p:AuditDetailAssertion/></wsp:All></wsp:Policy>"
                    )
                },
            }
        ]
    }
    bundle = parser._parse_imploded(data, "test", "test.json")
    assert len(bundle.services) == 1
    assert bundle.services[0].name == "Service Policy"
