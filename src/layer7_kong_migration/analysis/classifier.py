"""Three-tier assertion classifier.

Classifies each Layer 7 assertion as DIRECT (auto-generate Kong config),
CONDITIONAL (generate with review flags), or CUSTOM (requires AI analysis).
"""

from layer7_kong_migration.models.ir import (
    ASSERTION_REVIEW_REASONS,
    AssertionConfig,
    Complexity,
    PolicyBundle,
    ReviewFlag,
)

DIRECT_ASSERTIONS: dict[str, str] = {
    "HttpBasic": "basic-auth",
    "LookupApiKey": "key-auth",
    "CorsAssertion": "cors",
    "RateLimit": "rate-limiting",
    "DistributedRateLimit": "rate-limiting-advanced",
    "RequestSizeLimit": "request-size-limiting",
    "RemoteIpRange": "ip-restriction",
    "RemoteIpAddressRange": "ip-restriction",
    "HardcodedResponse": "request-termination",
    "EchoRoutingAssertion": "request-termination",
    "AuditDetailAssertion": "http-log",
    "AuditAssertion": "http-log",
    "AddHeader": "request-transformer",
    "RemoveHeader": "request-transformer",
    "CommentAssertion": "_skip",
    "TrueAssertion": "_skip",
    "FalseAssertion": "_skip",
    "UUIDGenerator": "pre-function",
    "RaiseError": "request-termination",
    "EchoRouting": "request-termination",
}

CONDITIONAL_ASSERTIONS: dict[str, tuple[str, ReviewFlag]] = {
    "Authentication": ("basic-auth", ReviewFlag.IDP_CONFIG_REQUIRED),
    "SslAssertion": ("mtls-auth", ReviewFlag.SECURITY_REVIEW),
    "RequireSaml": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    "DecodeJsonWebToken": ("jwt", ReviewFlag.KEY_CONFIG_REQUIRED),
    "EncodeJsonWebToken": ("jwt-signer", ReviewFlag.KEY_CONFIG_REQUIRED),
    "ThroughputQuota": ("rate-limiting-advanced", ReviewFlag.TRANSFORM_REVIEW),
    "CacheLookup": ("proxy-cache", ReviewFlag.CACHE_STRATEGY),
    "CacheStorage": ("proxy-cache", ReviewFlag.CACHE_STRATEGY),
    "HttpRoutingAssertion": ("_upstream", ReviewFlag.ROUTING_DECISION),
    "Http2RoutingAssertion": ("_upstream", ReviewFlag.ROUTING_DECISION),
    "JsonSchemaAssertion": ("request-validator", ReviewFlag.TRANSFORM_REVIEW),
    "OpenApiValidation": ("request-validator", ReviewFlag.TRANSFORM_REVIEW),
    "SwaggerAssertion": ("request-validator", ReviewFlag.TRANSFORM_REVIEW),
    "CustomizeErrorResponse": ("exit-transformer", ReviewFlag.TRANSFORM_REVIEW),
    "Regex": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "SetVariable": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "ComparisonAssertion": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "Include": ("_fragment", ReviewFlag.MANUAL_REVIEW),
    "Encapsulated": ("_encass", ReviewFlag.MANUAL_REVIEW),
    "AwsLambda": ("aws-lambda", ReviewFlag.ROUTING_DECISION),
    "JsonTransformationAssertion": ("request-transformer-advanced", ReviewFlag.TRANSFORM_REVIEW),
    "JsonPathAssertion": ("jq", ReviewFlag.TRANSFORM_REVIEW),
    "JsonPathAssertionV2": ("jq", ReviewFlag.TRANSFORM_REVIEW),
    "EvaluateJsonPathExpression": ("jq", ReviewFlag.TRANSFORM_REVIEW),
    "EvaluateJsonPathExpressionV2": ("jq", ReviewFlag.TRANSFORM_REVIEW),
    "CookieCredentialSource": ("session", ReviewFlag.IDP_CONFIG_REQUIRED),
    "ExportVariables": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "JsonTransformation": ("request-transformer-advanced", ReviewFlag.TRANSFORM_REVIEW),
    "LookupTrustedCertificate": ("mtls-auth", ReviewFlag.SECURITY_REVIEW),
    "ValidateCertificate": ("mtls-auth", ReviewFlag.SECURITY_REVIEW),
    "CodeInjectionProtectionAssertion": ("bot-detection", ReviewFlag.SECURITY_REVIEW),
    # --- XML tag name aliases (actual L7p: tag names from real policies) ---
    "JSONSchemaAssertion": ("request-validator", ReviewFlag.TRANSFORM_REVIEW),
    "OpenApi": ("request-validator", ReviewFlag.TRANSFORM_REVIEW),
    "JwtEncode": ("jwt-signer", ReviewFlag.KEY_CONFIG_REQUIRED),
    "SqlAttackProtectionAssertion": ("pre-function", ReviewFlag.SECURITY_REVIEW),
    "JsonDocumentStructureAssertion": ("json-threat-protection", ReviewFlag.SECURITY_REVIEW),
    "OversizedTextAssertion": ("xml-threat-protection", ReviewFlag.SECURITY_REVIEW),
    "CertificateAttributes": ("mtls-auth", ReviewFlag.SECURITY_REVIEW),
    "CrossSiteScriptingProtectionAssertion": ("pre-function", ReviewFlag.SECURITY_REVIEW),
    # --- Kong 3.14 Enterprise plugin promotions ---
    "DocumentStructureThreat": ("xml-threat-protection", ReviewFlag.SECURITY_REVIEW),
    "JsonDocumentStructureThreat": ("json-threat-protection", ReviewFlag.SECURITY_REVIEW),
    "KafkaRoutingAssertion": ("kafka-upstream", ReviewFlag.ROUTING_DECISION),
    "SchemaValidation": ("request-validator", ReviewFlag.TRANSFORM_REVIEW),
    "GraphqlSchemaValidation": ("graphql-rate-limiting-advanced", ReviewFlag.TRANSFORM_REVIEW),
    "SiteMinderAuthenticate": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    "SiteMinderAuthorize": ("opa", ReviewFlag.IDP_CONFIG_REQUIRED),
    "SiteMinderCheckProtected": ("opa", ReviewFlag.SECURITY_REVIEW),
    "ValidateNonSoapSamlToken": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    "CreateSamlToken": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    # --- Pre-function implementations viable in Kong 3.14 ---
    "SqlAttackProtection": ("pre-function", ReviewFlag.SECURITY_REVIEW),
    "CsrfProtection": ("pre-function", ReviewFlag.SECURITY_REVIEW),
    "TimeRange": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "EncodeDecode": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "KeyValueStore": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "KeyValueLookup": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
}

CUSTOM_ASSERTIONS: set[str] = {
    "JavaScript",
    "XslTransformation",
    "WssBasic",
    "WssDigest",
    "WssSignature",
    "WssKerberos",
    "RadiusAuthenticate",
    "JmsRoutingAssertion",
    "MqNativeRoutingAssertion",
    "FtpRoutingAssertion",
    "SshRoutingAssertion",
    "RawTcpRoutingAssertion",
    "JdbcQuery",
    "CassandraQuery",
    "LDAPQuery",
    "LDAPWrite",
    "CustomAssertion",
    "CodeInjectionProtection",
    "ForEachLoop",
    "XpathCredential",
    "RequestXpathAssertion",
    "ResponseXpathAssertion",
    "WsSecurity",
    "WssEncryptElement",
    "WssSignElement",
    "AddXmlElement",
    "RemoveXmlElement",
    "HttpFormPost",
    "MimeToHttpForm",
    "AccumulateData",
    "ManipulateMultivalued",
    "MapValue",
    "Split",
    "JoinVariable",
    "Join",
    "MqNativeRouting",
    "NonSoapDecryptElement",
    "ManipulateMultiValuedVariable",
    # Discovered from Layer7-Community/Sample-Policies
    "Email",
    "RESTGatewayManagement",
}


class AssertionClassifier:
    def classify_bundle(self, bundle: PolicyBundle) -> PolicyBundle:
        for svc in bundle.services:
            for assertion in svc.assertions:
                self._classify(assertion)
        for pol in bundle.shared_policies:
            for assertion in pol.assertions:
                self._classify(assertion)
        for enc in bundle.encapsulated_assertions:
            for assertion in enc.assertions:
                self._classify(assertion)
        return bundle

    def _classify(self, assertion: AssertionConfig) -> None:
        atype = assertion.assertion_type

        if atype in DIRECT_ASSERTIONS:
            assertion.complexity = Complexity.DIRECT
            assertion.confidence = 1.0
            return

        if atype in CONDITIONAL_ASSERTIONS:
            plugin, flag = CONDITIONAL_ASSERTIONS[atype]
            assertion.complexity = Complexity.CONDITIONAL
            assertion.review_flag = flag
            assertion.review_reason = ASSERTION_REVIEW_REASONS.get(atype, "")
            assertion.confidence = 0.7
            return

        assertion.complexity = Complexity.CUSTOM
        assertion.review_flag = ReviewFlag.CUSTOM_PLUGIN_REQUIRED
        assertion.review_reason = ASSERTION_REVIEW_REASONS.get(
            atype, f"No direct Kong mapping for {atype} - requires AI analysis or custom plugin"
        )
        assertion.confidence = 0.0
