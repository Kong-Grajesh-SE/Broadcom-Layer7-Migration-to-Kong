"""Plugin generators: assertion-specific Kong plugin config builders.

Each generator takes an AssertionConfig and returns a Kong plugin dict
ready for YAML serialization.
"""

from typing import Any

from layer7_kong_migration.models.ir import AssertionConfig


def generate_plugin(assertion: AssertionConfig, service_name: str) -> dict[str, Any] | None:
    gen = PLUGIN_GENERATORS.get(assertion.assertion_type)
    if gen:
        plugin = gen(assertion)
        if plugin:
            plugin["tags"] = ["migrated-from-layer7", assertion.assertion_type]
            return plugin
    return None


def integrate_ai_results(assertion: AssertionConfig, service_name: str) -> dict[str, Any] | None:
    mapping = assertion.kong_mapping
    if not mapping:
        return None

    plugin_name = mapping.get("kong_plugin_name", "")
    if not plugin_name or plugin_name.startswith("_"):
        return None

    plugin: dict[str, Any] = {
        "name": plugin_name,
        "config": mapping.get("kong_plugin_config", {}),
        "tags": ["migrated-from-layer7", "ai-generated", assertion.assertion_type],
    }

    lua_code = mapping.get("lua_code")
    if lua_code and plugin_name in ("pre-function", "post-function"):
        phase = "access" if plugin_name == "pre-function" else "body_filter"
        plugin["config"] = {phase: [lua_code]}

    review_notes = mapping.get("review_notes", [])
    if review_notes:
        plugin["_review_notes"] = review_notes

    return plugin


def _gen_basic_auth(assertion: AssertionConfig) -> dict[str, Any]:
    return {
        "name": "basic-auth",
        "config": {"hide_credentials": True},
    }


def _gen_key_auth(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    key_name = config.get("key_name", "apikey")
    location = config.get("location", "HEADER").lower()
    key_names = [key_name]
    return {
        "name": "key-auth",
        "config": {
            "key_names": key_names,
            "key_in_header": location in ("header", "both"),
            "key_in_query": location in ("query", "both"),
            "hide_credentials": True,
        },
    }


def _gen_cors(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    return {
        "name": "cors",
        "config": {
            "origins": config.get("accepted_origins", ["*"]),
            "methods": config.get("accepted_methods", ["GET", "POST", "PUT", "DELETE", "OPTIONS"]),
            "headers": config.get("accepted_headers", ["*"]),
            "exposed_headers": [h for h in (config.get("exposed_headers", "") or "").split(",") if h.strip()],
            "max_age": config.get("max_age", 3600),
            "credentials": config.get("allow_credentials", False),
        },
    }


def _gen_rate_limiting(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    rps = config.get("max_requests_per_second", 100)
    return {
        "name": "rate-limiting",
        "config": {
            "second": rps,
            "policy": "local",
            "fault_tolerant": True,
            "hide_client_headers": False,
        },
    }


def _gen_request_size_limiting(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    max_bytes = config.get("max_size_bytes", 5242880)
    max_mb = max_bytes / (1024 * 1024)
    return {
        "name": "request-size-limiting",
        "config": {
            "allowed_payload_size": int(max_mb),
            "size_unit": "megabytes",
        },
    }


def _gen_ip_restriction(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    ip_ranges = config.get("ip_ranges", [])
    allow = config.get("allow_range", True)
    result: dict[str, Any] = {"name": "ip-restriction", "config": {}}
    if allow:
        result["config"]["allow"] = ip_ranges
    else:
        result["config"]["deny"] = ip_ranges
    return result


def _gen_request_termination(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    return {
        "name": "request-termination",
        "config": {
            "status_code": config.get("response_status", 200),
            "content_type": config.get("response_content_type", "application/json"),
            "body": config.get("response_body", ""),
        },
    }


def _gen_http_log(assertion: AssertionConfig) -> dict[str, Any]:
    return {
        "name": "http-log",
        "config": {
            "http_endpoint": "http://REPLACE-WITH-LOG-ENDPOINT:8080/logs",
            "method": "POST",
            "content_type": "application/json",
        },
    }


def _gen_request_transformer(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    atype = assertion.assertion_type
    target = config.get("target_message", "request")

    result: dict[str, Any] = {"name": "request-transformer" if target == "request" else "response-transformer"}
    plugin_config: dict[str, Any] = {}

    if atype == "AddHeader":
        header_name = config.get("header_name", "")
        header_value = config.get("header_value", "")
        if header_name:
            if config.get("remove_existing", False):
                plugin_config["replace"] = {"headers": [f"{header_name}:{header_value}"]}
            else:
                plugin_config["add"] = {"headers": [f"{header_name}:{header_value}"]}
    elif atype == "RemoveHeader":
        header_name = config.get("header_name", "")
        if header_name:
            plugin_config["remove"] = {"headers": [header_name]}

    result["config"] = plugin_config
    return result


def _gen_xml_threat_protection(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    return {
        "name": "xml-threat-protection",
        "config": {
            "checked_content_types": config.get("content_types", ["text/xml", "application/xml"]),
            "max_body_size": config.get("max_size_bytes", 1048576),
            "max_depth": config.get("max_depth", 100),
            "max_children": config.get("max_children", 256),
            "max_attributes": config.get("max_attributes", 128),
            "allow_dtd": config.get("allow_dtd", False),
        },
        "_review_notes": ["Kong Enterprise required", "Verify threat thresholds match Layer 7 policy"],
    }


def _gen_json_threat_protection(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    return {
        "name": "json-threat-protection",
        "config": {
            "max_body_size": config.get("max_size_bytes", 1048576),
            "max_depth": config.get("max_depth", 64),
            "max_array_element_count": config.get("max_array_elements", 8192),
            "max_object_entry_count": config.get("max_object_entries", 1024),
            "max_string_value_length": config.get("max_string_length", 262144),
        },
        "_review_notes": ["Kong Enterprise required", "Verify limits match Layer 7 JSON threat policy"],
    }


def _gen_kafka_upstream(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    return {
        "name": "kafka-upstream",
        "config": {
            "bootstrap_servers": [
                {"host": config.get("broker_host", "REPLACE-KAFKA-HOST"), "port": config.get("broker_port", 9092)}
            ],
            "topic": config.get("topic", "REPLACE-TOPIC-NAME"),
            "forward_method": True,
            "forward_uri": True,
            "forward_headers": True,
            "forward_body": True,
            "producer_request_acks": -1,
        },
        "_review_notes": [
            "Kong Enterprise required",
            "Configure Kafka bootstrap servers and topic",
            "Review SASL/TLS authentication settings",
        ],
    }


def _gen_exit_transformer(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    status = config.get("response_status", 0)
    body_template = config.get("response_body", "")
    return {
        "name": "exit-transformer",
        "config": {
            "functions": [
                "return function(status, body, headers)\n"
                "  -- Customize Kong-generated error responses\n"
                f"  -- Original Layer 7 status: {status}\n"
                "  return status, body, headers\n"
                "end"
            ],
        },
        "_review_notes": [
            "Kong Enterprise required",
            "Implement error response customization in Lua function",
            f"Original Layer 7 response template: {body_template[:200]}" if body_template else "No response template found",
        ],
    }


def _gen_graphql_rate_limiting(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    return {
        "name": "graphql-rate-limiting-advanced",
        "config": {
            "limit": [100],
            "window_size": [60],
            "strategy": "local",
            "cost_strategy": "default",
            "max_cost": config.get("max_query_cost", 0),
        },
        "_review_notes": [
            "Kong Enterprise required",
            "Configure rate limits and cost strategy per GraphQL schema",
            "Review query cost calculation (default vs node_quantifier)",
        ],
    }


def _gen_opa(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    return {
        "name": "opa",
        "config": {
            "opa_host": config.get("policy_server_host", "REPLACE-OPA-HOST"),
            "opa_port": config.get("policy_server_port", 8181),
            "opa_path": "/v1/data/layer7/authz",
            "include_consumer_in_opa_input": True,
            "include_route_in_opa_input": True,
            "include_service_in_opa_input": True,
        },
        "_review_notes": [
            "Kong Enterprise required",
            "Deploy OPA server with Rego policies replicating SiteMinder authorization rules",
            "Map SiteMinder resource/action checks to OPA policy input",
        ],
    }


def _gen_openid_connect(assertion: AssertionConfig) -> dict[str, Any]:
    config = assertion.configuration
    return {
        "name": "openid-connect",
        "config": {
            "issuer": config.get("idp_issuer", "REPLACE-WITH-OIDC-ISSUER-URL"),
            "client_id": ["REPLACE-CLIENT-ID"],
            "client_secret": ["REPLACE-CLIENT-SECRET"],
            "auth_methods": ["authorization_code", "session"],
            "scopes": config.get("scopes", ["openid", "profile"]),
        },
        "_review_notes": [
            "Kong Enterprise required",
            "Migrate SAML/SiteMinder IdP to OIDC-compatible provider",
            "Configure OIDC discovery endpoint, client credentials, and scopes",
        ],
    }


PLUGIN_GENERATORS: dict[str, Any] = {
    "HttpBasic": _gen_basic_auth,
    "LookupApiKey": _gen_key_auth,
    "CorsAssertion": _gen_cors,
    "RateLimit": _gen_rate_limiting,
    "DistributedRateLimit": _gen_rate_limiting,
    "RequestSizeLimit": _gen_request_size_limiting,
    "RemoteIpRange": _gen_ip_restriction,
    "HardcodedResponse": _gen_request_termination,
    "EchoRoutingAssertion": _gen_request_termination,
    "AuditDetailAssertion": _gen_http_log,
    "AuditAssertion": _gen_http_log,
    "AddHeader": _gen_request_transformer,
    "RemoveHeader": _gen_request_transformer,
    # Kong 3.14 Enterprise plugin generators
    "DocumentStructureThreat": _gen_xml_threat_protection,
    "JsonDocumentStructureThreat": _gen_json_threat_protection,
    "KafkaRoutingAssertion": _gen_kafka_upstream,
    "CustomizeErrorResponse": _gen_exit_transformer,
    "GraphqlSchemaValidation": _gen_graphql_rate_limiting,
    "SiteMinderAuthorize": _gen_opa,
    "SiteMinderCheckProtected": _gen_opa,
    "SiteMinderAuthenticate": _gen_openid_connect,
    "ValidateNonSoapSamlToken": _gen_openid_connect,
    "CreateSamlToken": _gen_openid_connect,
}
