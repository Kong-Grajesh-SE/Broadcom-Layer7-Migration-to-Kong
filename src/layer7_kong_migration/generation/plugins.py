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
}
