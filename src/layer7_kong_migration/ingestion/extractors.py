"""Assertion-specific configuration extractors.

Each extractor pulls structured data from a Layer 7 assertion XML element
into a flat dict stored in AssertionConfig.configuration. This normalizes
the diverse XML structures into a uniform format for downstream stages.
"""

from typing import Any

from lxml import etree

NS_L7P = "http://www.layer7tech.com/ws/policy"


def extract_assertion_config(
    assertion_type: str, elem: etree._Element, ns: dict[str, str]
) -> dict[str, Any]:
    extractor = EXTRACTORS.get(assertion_type, _extract_generic)
    config = extractor(elem, ns)
    config.setdefault("_name", assertion_type)
    config.setdefault("_enabled", _get_bool(elem, "Enabled", True))
    return config


def _get_string(elem: etree._Element, tag: str) -> str:
    child = elem.find(f"L7p:{tag}", {"L7p": NS_L7P})
    if child is None:
        child = elem.find(tag)
    if child is not None:
        val = child.get("stringValue", "") or child.text or ""
        return val.strip()
    return ""


def _get_int(elem: etree._Element, tag: str, default: int = 0) -> int:
    child = elem.find(f"L7p:{tag}", {"L7p": NS_L7P})
    if child is None:
        child = elem.find(tag)
    if child is not None:
        val = child.get("intValue") or child.get("longValue") or child.text
        if val:
            return int(val)
    return default


def _get_goid(elem: etree._Element, tag: str) -> str:
    child = elem.find(f"L7p:{tag}", {"L7p": NS_L7P})
    if child is not None:
        return child.get("goidValue", "") or child.text or ""
    return ""


def _get_bool(elem: etree._Element, tag: str, default: bool = False) -> bool:
    child = elem.find(f"L7p:{tag}", {"L7p": NS_L7P})
    if child is None:
        child = elem.find(tag)
    if child is not None:
        val = child.get("booleanValue", "").lower()
        if val:
            return val == "true"
        if child.text:
            return child.text.strip().lower() == "true"
    return default


def _extract_generic(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    config: dict[str, Any] = {}
    for child in elem:
        tag = etree.QName(child.tag).localname if "}" in child.tag else child.tag
        if child.get("stringValue"):
            config[tag] = child.get("stringValue")
        elif child.get("intValue"):
            config[tag] = int(child.get("intValue", "0"))
        elif child.get("longValue"):
            config[tag] = int(child.get("longValue", "0"))
        elif child.get("booleanValue"):
            config[tag] = child.get("booleanValue") == "true"
        elif child.get("goidValue"):
            config[tag] = child.get("goidValue")
        elif child.text and child.text.strip():
            config[tag] = child.text.strip()
    return config


def _extract_http_routing(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "HttpRoutingAssertion",
        "protected_service_url": _get_string(elem, "ProtectedServiceUrl"),
        "request_header_rules": _extract_header_rules(elem, "RequestHeaderRules"),
        "response_header_rules": _extract_header_rules(elem, "ResponseHeaderRules"),
        "tls_version": _get_string(elem, "TlsVersion"),
        "tls_key_alias": _get_string(elem, "TlsKeyAlias"),
        "connection_timeout": _get_int(elem, "ConnectionTimeout", 30000),
        "read_timeout": _get_int(elem, "Timeout", 60000),
        "follow_redirects": _get_bool(elem, "FollowRedirects", False),
        "http_method": _get_string(elem, "HttpMethod"),
        "proxy_host": _get_string(elem, "ProxyHost"),
        "proxy_port": _get_int(elem, "ProxyPort"),
    }


def _extract_header_rules(elem: etree._Element, tag: str) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    rules_elem = elem.find(f"L7p:{tag}", {"L7p": NS_L7P})
    if rules_elem is None:
        return rules
    for rule in rules_elem.findall(f"L7p:Rules/L7p:item", {"L7p": NS_L7P}):
        rules.append({
            "name": _get_string(rule, "Name"),
            "pass_through": _get_bool(rule, "PassThrough", True),
        })
    return rules


def _extract_rate_limit(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "RateLimit",
        "max_requests_per_second": _get_int(elem, "MaxRequestsPerSecond", 100),
        "max_concurrency": _get_int(elem, "MaxConcurrency", 0),
        "counter_name": _get_string(elem, "CounterName"),
        "hardwired": _get_bool(elem, "Hardwired", False),
    }


def _extract_throughput_quota(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "ThroughputQuota",
        "quota": _get_int(elem, "Quota", 1000),
        "time_unit": _get_string(elem, "TimeUnit") or "PER_DAY",
        "counter_name": _get_string(elem, "CounterName"),
        "counter_strategy": _get_string(elem, "CounterStrategy") or "ALWAYS",
    }


def _extract_http_basic(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {"_name": "HttpBasic"}


def _extract_authentication(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "Authentication",
        "identity_provider_oid": _get_goid(elem, "IdentityProviderOid"),
    }


def _extract_ssl_assertion(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "SslAssertion",
        "require_client_cert": _get_bool(elem, "RequireClientAuthentication", False),
        "tls_version": _get_string(elem, "TlsVersion"),
    }


def _extract_set_variable(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "SetVariable",
        "variable_to_set": _get_string(elem, "VariableToSet"),
        "expression": _get_string(elem, "Expression") or _get_string(elem, "Base64Expression"),
        "data_type": _get_string(elem, "DataType") or "string",
        "content_type": _get_string(elem, "ContentType"),
    }


def _extract_comparison(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "ComparisonAssertion",
        "expression1": _get_string(elem, "Expression1"),
        "expression2": _get_string(elem, "Expression2"),
        "operator": _get_string(elem, "Operator") or "EQUALS",
        "case_sensitive": _get_bool(elem, "CaseSensitive", True),
        "negate": _get_bool(elem, "Negate", False),
    }


def _extract_hardcoded_response(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    body_elem = elem.find(f"L7p:ResponseBody", {"L7p": NS_L7P})
    body = ""
    if body_elem is not None:
        body = body_elem.get("stringValue", "") or body_elem.text or ""
    return {
        "_name": "HardcodedResponse",
        "response_status": _get_int(elem, "ResponseStatus", 200),
        "response_content_type": _get_string(elem, "ResponseContentType") or "text/xml",
        "response_body": body,
        "early_response": _get_bool(elem, "EarlyResponse", False),
    }


def _extract_cors(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    origins: list[str] = []
    origins_elem = elem.find(f"L7p:AcceptedOrigins", {"L7p": NS_L7P})
    if origins_elem is not None:
        for item in origins_elem.findall(f"L7p:item", {"L7p": NS_L7P}):
            val = item.get("stringValue", "") or item.text or ""
            if val:
                origins.append(val)

    methods: list[str] = []
    methods_elem = elem.find(f"L7p:AcceptedMethods", {"L7p": NS_L7P})
    if methods_elem is not None:
        for item in methods_elem.findall(f"L7p:item", {"L7p": NS_L7P}):
            val = item.get("stringValue", "") or item.text or ""
            if val:
                methods.append(val)

    headers: list[str] = []
    headers_elem = elem.find(f"L7p:AcceptedHeaders", {"L7p": NS_L7P})
    if headers_elem is not None:
        for item in headers_elem.findall(f"L7p:item", {"L7p": NS_L7P}):
            val = item.get("stringValue", "") or item.text or ""
            if val:
                headers.append(val)

    return {
        "_name": "CorsAssertion",
        "accepted_origins": origins,
        "accepted_methods": methods,
        "accepted_headers": headers,
        "exposed_headers": _get_string(elem, "ExposedHeaders"),
        "max_age": _get_int(elem, "MaxAge", 3600),
        "allow_credentials": _get_bool(elem, "AllowCredentials", False),
    }


def _extract_request_size_limit(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "RequestSizeLimit",
        "max_size_bytes": _get_int(elem, "MaxSize", 5242880),
    }


def _extract_ip_range(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    ranges: list[str] = []
    range_elem = elem.find(f"L7p:IpRange", {"L7p": NS_L7P})
    if range_elem is not None:
        val = range_elem.get("stringValue", "") or range_elem.text or ""
        if val:
            ranges.append(val)
    return {
        "_name": "RemoteIpRange",
        "ip_ranges": ranges,
        "allow_range": _get_bool(elem, "AllowRange", True),
    }


def _extract_cache_lookup(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "CacheLookup",
        "cache_id": _get_string(elem, "CacheId"),
        "max_entry_age_millis": _get_int(elem, "MaxEntryAgeMillis", 300000),
        "max_entries": _get_int(elem, "MaxEntries", 1000),
    }


def _extract_cache_storage(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "CacheStorage",
        "cache_id": _get_string(elem, "CacheId"),
        "max_entry_size_bytes": _get_int(elem, "MaxEntrySizeBytes", 1048576),
    }


def _extract_add_header(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "AddHeader",
        "header_name": _get_string(elem, "HeaderName"),
        "header_value": _get_string(elem, "HeaderValue"),
        "remove_existing": _get_bool(elem, "RemoveExisting", False),
        "target_message": _get_string(elem, "Target") or "request",
    }


def _extract_remove_header(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "RemoveHeader",
        "header_name": _get_string(elem, "HeaderName"),
        "target_message": _get_string(elem, "Target") or "request",
    }


def _extract_regex(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "Regex",
        "regex_expression": _get_string(elem, "Regex") or _get_string(elem, "RegexExpression"),
        "auto_target": _get_bool(elem, "AutoTarget", True),
        "other_target_message_variable": _get_string(elem, "OtherTargetMessageVariable"),
        "replace": _get_bool(elem, "Replace", False),
        "replacement": _get_string(elem, "Replacement"),
        "capture_var": _get_string(elem, "CaptureVar"),
    }


def _extract_javascript(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    script = ""
    script_elem = elem.find(f"L7p:Script", {"L7p": NS_L7P})
    if script_elem is not None:
        script = script_elem.get("stringValue", "") or script_elem.text or ""
    return {
        "_name": "JavaScript",
        "script_name": _get_string(elem, "ScriptName"),
        "script": script,
        "execution_timeout": _get_int(elem, "ExecutionTimeout", 10000),
    }


def _extract_audit_detail(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "AuditDetailAssertion",
        "detail": _get_string(elem, "Detail"),
        "level": _get_string(elem, "Level") or "INFO",
        "logging_only": _get_bool(elem, "LoggingOnly", False),
    }


def _extract_customize_error(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "CustomizeErrorResponse",
        "content": _get_string(elem, "Content"),
        "content_type": _get_string(elem, "ContentType") or "text/xml",
        "http_status": _get_int(elem, "HttpStatus", 500),
        "extra_headers": _get_string(elem, "ExtraHeaders"),
    }


def _extract_xsl_transformation(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "XslTransformation",
        "resource_url": _get_string(elem, "ResourceUrl"),
        "direction": _get_string(elem, "Direction") or "REQUEST",
        "xslt_content": _get_string(elem, "XslContent"),
    }


def _extract_json_transform(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "JsonTransformationAssertion",
        "transformation": _get_string(elem, "Transformation"),
        "root_tag": _get_string(elem, "RootTag"),
        "direction": _get_string(elem, "Direction") or "REQUEST",
    }


def _extract_schema_validation(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "SchemaValidation",
        "resource_url": _get_string(elem, "ResourceUrl"),
        "target": _get_string(elem, "Target") or "REQUEST",
    }


def _extract_json_schema(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "JsonSchemaAssertion",
        "resource_url": _get_string(elem, "ResourceUrl"),
        "target": _get_string(elem, "Target") or "REQUEST",
    }


def _extract_encode_jwt(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "EncodeJsonWebToken",
        "algorithm": _get_string(elem, "SignatureAlgorithm") or "RS256",
        "key_id": _get_string(elem, "PrivateKeyGoid"),
        "source_variable": _get_string(elem, "SourceVariable"),
        "target_variable": _get_string(elem, "TargetVariable"),
        "expiry_seconds": _get_int(elem, "ExpirySeconds", 3600),
    }


def _extract_decode_jwt(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "DecodeJsonWebToken",
        "source_variable": _get_string(elem, "SourceVariable"),
        "target_variable": _get_string(elem, "TargetVariable"),
        "validate_signature": _get_bool(elem, "ValidateSignature", True),
    }


def _extract_sql_attack_protection(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "SqlAttackProtection",
        "include_url": _get_bool(elem, "IncludeUrl", True),
        "include_body": _get_bool(elem, "IncludeBody", True),
        "include_url_query_string": _get_bool(elem, "IncludeUrlQueryString", True),
    }


def _extract_code_injection_protection(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "CodeInjectionProtection",
        "include_url_path": _get_bool(elem, "IncludeUrlPath", True),
        "include_body": _get_bool(elem, "IncludeBody", True),
        "include_url_query_string": _get_bool(elem, "IncludeUrlQueryString", True),
        "html_javascript_injection": _get_bool(elem, "HtmlJavaScriptInjection", True),
        "php_eval_injection": _get_bool(elem, "PhpEvalInjection", True),
        "shell_injection": _get_bool(elem, "ShellInjection", True),
        "ldap_injection": _get_bool(elem, "LdapInjection", True),
        "xpath_injection": _get_bool(elem, "XpathInjection", True),
    }


def _extract_lookup_api_key(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "LookupApiKey",
        "location": _get_string(elem, "Location") or "HEADER",
        "key_name": _get_string(elem, "KeyName") or "apikey",
    }


def _extract_for_each_loop(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "ForEachLoop",
        "loop_variable": _get_string(elem, "LoopVariable"),
        "variable_prefix": _get_string(elem, "VariablePrefix"),
        "iteration_limit": _get_int(elem, "IterationLimit", 100),
    }


def _extract_encapsulated(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "Encapsulated",
        "encapsulated_assertion_config_guid": _get_string(elem, "EncapsulatedAssertionConfigGuid")
        or _get_string(elem, "EncapsulatedAssertionConfigName"),
    }


def _extract_include(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "Include",
        "policy_guid": _get_string(elem, "PolicyGuid"),
        "policy_name": _get_string(elem, "PolicyName"),
    }


def _extract_time_range(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "TimeRange",
        "start_time": _get_string(elem, "StartTime"),
        "end_time": _get_string(elem, "EndTime"),
        "start_day_of_week": _get_int(elem, "StartDayOfWeek", 1),
        "end_day_of_week": _get_int(elem, "EndDayOfWeek", 7),
        "timezone": _get_string(elem, "TimeZone") or "UTC",
    }


def _extract_json_path(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "JsonPathAssertion",
        "expression": _get_string(elem, "Expression"),
        "target": _get_string(elem, "Target") or "REQUEST",
        "evaluate_as_expression": _get_bool(elem, "EvaluateAsExpression", False),
    }


def _extract_aws_lambda(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "AwsLambda",
        "function_name": _get_string(elem, "FunctionName"),
        "region": _get_string(elem, "Region"),
        "qualifier": _get_string(elem, "Qualifier"),
    }


# --- Extractors for real-world assertions found in Layer 7 Utilities ---


def _extract_jdbc_query(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "JdbcQuery",
        "connection_name": _get_string(elem, "ConnectionName"),
        "sql_query": _get_string(elem, "SqlQuery"),
        "convert_variables_to_strings": _get_bool(elem, "ConvertVariablesToStrings", True),
        "max_records": _get_int(elem, "MaxRecords", 100),
        "query_timeout": _get_string(elem, "QueryTimeout"),
    }


def _extract_cassandra_query(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "CassandraQuery",
        "connection_name": _get_string(elem, "ConnectionName"),
        "query_document": _get_string(elem, "QueryDocument"),
        "fetch_size": _get_int(elem, "FetchSize", 5000),
        "max_records": _get_int(elem, "MaxRecords", 10),
        "query_timeout": _get_string(elem, "QueryTimeout"),
    }


def _extract_jms_routing(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "JmsRoutingAssertion",
        "endpoint_name": _get_string(elem, "EndpointName"),
    }


def _extract_mq_native_routing(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "MqNativeRouting",
        "connector_name": _get_string(elem, "SsgActiveConnectorName"),
        "put_message_timeout": _get_string(elem, "PutMessageTimeout"),
    }


def _extract_encode_decode(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "EncodeDecode",
        "source_variable_name": _get_string(elem, "SourceVariableName"),
        "target_variable_name": _get_string(elem, "TargetVariableName"),
        "target_content_type": _get_string(elem, "TargetContentType"),
        "transform_type": _get_string(elem, "TransformType") or "BASE64_ENCODE",
        "character_encoding": _get_string(elem, "CharacterEncoding"),
    }


def _extract_request_xpath(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    expr = ""
    xpath_elem = elem.find(f"L7p:XpathExpression", {"L7p": NS_L7P})
    if xpath_elem is not None:
        expr_elem = xpath_elem.find(f"L7p:Expression", {"L7p": NS_L7P})
        if expr_elem is not None:
            expr = expr_elem.get("stringValue", "") or expr_elem.text or ""
    return {
        "_name": "RequestXpathAssertion",
        "variable_prefix": _get_string(elem, "VariablePrefix"),
        "xpath_expression": expr,
        "xpath_version": _get_string(elem, "XpathVersion") or "1.0",
    }


def _extract_response_xpath(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    config = _extract_request_xpath(elem, ns)
    config["_name"] = "ResponseXpathAssertion"
    return config


def _extract_evaluate_json_path(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "EvaluateJsonPathExpressionV2",
        "expression": _get_string(elem, "Expression"),
        "variable_prefix": _get_string(elem, "VariablePrefix") or _get_string(elem, "OutputVariable"),
        "source": _get_string(elem, "OtherTargetMessageVariable"),
        "evaluate_as_expression": _get_bool(elem, "EvaluateAsExpression", False),
    }


def _extract_hardcoded_response_full(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    body = ""
    body_elem = elem.find(f"L7p:ResponseBody", {"L7p": NS_L7P})
    if body_elem is not None:
        body = body_elem.get("stringValue", "") or body_elem.get("stringValueReference", "") or body_elem.text or ""
    return {
        "_name": "HardcodedResponse",
        "response_status": _get_int(elem, "ResponseStatus", 200),
        "response_content_type": _get_string(elem, "ResponseContentType") or "text/xml",
        "response_body": body,
        "early_response": _get_bool(elem, "EarlyResponse", False),
    }


def _extract_uuid_generator(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "UUIDGenerator",
        "variable_name": _get_string(elem, "VariableName"),
    }


def _extract_cookie_credential(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "CookieCredentialSource",
        "cookie_name": _get_string(elem, "CookieName"),
    }


def _extract_raise_error(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {"_name": "RaiseError"}


def _extract_false_assertion(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {"_name": "FalseAssertion"}


def _extract_true_assertion(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {"_name": "TrueAssertion"}


def _extract_comment(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "CommentAssertion",
        "comment": _get_string(elem, "Comment"),
    }


def _extract_split(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "Split",
        "expression": _get_string(elem, "Expression") or _get_string(elem, "InputVariable"),
        "split_pattern": _get_string(elem, "SplitPattern"),
        "variable_prefix": _get_string(elem, "VariablePrefix"),
    }


def _extract_join(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "Join",
        "variable_name": _get_string(elem, "VariableName"),
        "join_substring": _get_string(elem, "JoinSubstring"),
    }


def _extract_manipulate_multivalued(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "ManipulateMultiValuedVariable",
        "variable_name": _get_string(elem, "VariableName"),
        "operation": _get_string(elem, "Operation"),
    }


def _extract_map_value(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "MapValue",
        "source_variable": _get_string(elem, "SourceVariable") or _get_string(elem, "InputExpr"),
        "output_variable": _get_string(elem, "OutputVariable") or _get_string(elem, "OutputVar"),
    }


def _extract_validate_nonsaml(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "ValidateNonSoapSamlToken",
        "version": _get_int(elem, "Version", 2),
    }


def _extract_create_saml_token(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "CreateSamlToken",
        "version": _get_int(elem, "Version", 2),
        "name_format": _get_string(elem, "NameFormat"),
    }


def _extract_siteminder_authenticate(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "SiteMinderAuthenticate",
        "agent_name": _get_string(elem, "SmAgentName"),
        "sso_zone": _get_string(elem, "SsoZoneName"),
        "create_sso_token": _get_bool(elem, "CreateSsoToken", False),
        "use_sm_cookie": _get_bool(elem, "UseSMCookie", False),
    }


def _extract_siteminder_check_protected(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "SiteMinderCheckProtected",
        "agent_name": _get_string(elem, "SmAgentName"),
        "protected_resource": _get_string(elem, "ProtectedResource"),
    }


def _extract_lookup_trusted_cert(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "LookupTrustedCertificate",
        "trusted_cert_name": _get_string(elem, "TrustedCertificateName"),
    }


def _extract_validate_certificate(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "ValidateCertificate",
        "validation_type": _get_string(elem, "ValidationType"),
    }


def _extract_custom_assertion(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    config = _extract_generic(elem, ns)
    config["_name"] = "CustomAssertion"
    return config


def _extract_export_variables(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "ExportVariables",
    }


def _extract_json_transformation(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    return {
        "_name": "JsonTransformation",
        "transformation": _get_string(elem, "Transformation"),
        "root_tag_string": _get_string(elem, "RootTagString"),
    }


def _extract_code_injection_protection_v2(elem: etree._Element, ns: dict[str, str]) -> dict[str, Any]:
    """Handles CodeInjectionProtectionAssertion (note: different XML tag than CodeInjectionProtection)."""
    return {
        "_name": "CodeInjectionProtectionAssertion",
        "include_url_path": _get_bool(elem, "IncludeUrlPath", True),
        "include_body": _get_bool(elem, "IncludeBody", True),
        "include_url_query_string": _get_bool(elem, "IncludeUrlQueryString", True),
        "target": _get_string(elem, "Target") or "REQUEST",
    }


EXTRACTORS: dict[str, Any] = {
    "HttpRoutingAssertion": _extract_http_routing,
    "Http2RoutingAssertion": _extract_http_routing,
    "RateLimit": _extract_rate_limit,
    "DistributedRateLimit": _extract_rate_limit,
    "ThroughputQuota": _extract_throughput_quota,
    "HttpBasic": _extract_http_basic,
    "Authentication": _extract_authentication,
    "SslAssertion": _extract_ssl_assertion,
    "SetVariable": _extract_set_variable,
    "ComparisonAssertion": _extract_comparison,
    "HardcodedResponse": _extract_hardcoded_response_full,
    "CorsAssertion": _extract_cors,
    "RequestSizeLimit": _extract_request_size_limit,
    "RemoteIpRange": _extract_ip_range,
    "CacheLookup": _extract_cache_lookup,
    "CacheStorage": _extract_cache_storage,
    "AddHeader": _extract_add_header,
    "RemoveHeader": _extract_remove_header,
    "Regex": _extract_regex,
    "JavaScript": _extract_javascript,
    "AuditDetailAssertion": _extract_audit_detail,
    "AuditAssertion": _extract_audit_detail,
    "CustomizeErrorResponse": _extract_customize_error,
    "XslTransformation": _extract_xsl_transformation,
    "JsonTransformationAssertion": _extract_json_transform,
    "SchemaValidation": _extract_schema_validation,
    "JsonSchemaAssertion": _extract_json_schema,
    "EncodeJsonWebToken": _extract_encode_jwt,
    "DecodeJsonWebToken": _extract_decode_jwt,
    "SqlAttackProtection": _extract_sql_attack_protection,
    "CodeInjectionProtection": _extract_code_injection_protection,
    "LookupApiKey": _extract_lookup_api_key,
    "ForEachLoop": _extract_for_each_loop,
    "Encapsulated": _extract_encapsulated,
    "Include": _extract_include,
    "TimeRange": _extract_time_range,
    "JsonPathAssertion": _extract_json_path,
    "JsonPathAssertionV2": _extract_json_path,
    "AwsLambda": _extract_aws_lambda,
    # Real-world extractors from Layer 7 Utilities
    "JdbcQuery": _extract_jdbc_query,
    "CassandraQuery": _extract_cassandra_query,
    "JmsRoutingAssertion": _extract_jms_routing,
    "MqNativeRouting": _extract_mq_native_routing,
    "MqNativeRoutingAssertion": _extract_mq_native_routing,
    "EncodeDecode": _extract_encode_decode,
    "RequestXpathAssertion": _extract_request_xpath,
    "ResponseXpathAssertion": _extract_response_xpath,
    "EvaluateJsonPathExpression": _extract_evaluate_json_path,
    "EvaluateJsonPathExpressionV2": _extract_evaluate_json_path,
    "UUIDGenerator": _extract_uuid_generator,
    "CookieCredentialSource": _extract_cookie_credential,
    "RaiseError": _extract_raise_error,
    "FalseAssertion": _extract_false_assertion,
    "TrueAssertion": _extract_true_assertion,
    "CommentAssertion": _extract_comment,
    "Split": _extract_split,
    "Join": _extract_join,
    "JoinVariable": _extract_join,
    "ManipulateMultiValuedVariable": _extract_manipulate_multivalued,
    "ManipulateMultivalued": _extract_manipulate_multivalued,
    "MapValue": _extract_map_value,
    "ValidateNonSoapSamlToken": _extract_validate_nonsaml,
    "CreateSamlToken": _extract_create_saml_token,
    "SiteMinderAuthenticate": _extract_siteminder_authenticate,
    "SiteMinderCheckProtected": _extract_siteminder_check_protected,
    "LookupTrustedCertificate": _extract_lookup_trusted_cert,
    "ValidateCertificate": _extract_validate_certificate,
    "CustomAssertion": _extract_custom_assertion,
    "ExportVariables": _extract_export_variables,
    "JsonTransformation": _extract_json_transformation,
    "CodeInjectionProtectionAssertion": _extract_code_injection_protection_v2,
    "NonSoapDecryptElement": _extract_generic,
}
