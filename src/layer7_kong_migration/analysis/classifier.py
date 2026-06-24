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
    "HttpDigest": "basic-auth",
    "LookupApiKey": "key-auth",
    "ManageApiKey": "key-auth",
    "CorsAssertion": "cors",
    "CORS": "cors",
    "RateLimit": "rate-limiting",
    "DistributedRateLimit": "rate-limiting-advanced",
    "RequestSizeLimit": "request-size-limiting",
    "RemoteIpRange": "ip-restriction",
    "RemoteIpAddressRange": "ip-restriction",
    "HardcodedResponse": "request-termination",
    "EchoRoutingAssertion": "request-termination",
    "AuditDetailAssertion": "http-log",
    "AuditAssertion": "http-log",
    "AuditDetail": "http-log",
    "Audit": "http-log",
    "AuditRecordToXml": "http-log",
    "AddHeader": "request-transformer",
    "RemoveHeader": "request-transformer",
    "ContentType": "request-transformer",
    "CommentAssertion": "_skip",
    "Comment": "_skip",
    "TrueAssertion": "_skip",
    "True": "_skip",
    "FalseAssertion": "_skip",
    "False": "_skip",
    "UUIDGenerator": "pre-function",
    "GeneratePassword": "pre-function",
    "GenerateSecurityHash": "pre-function",
    "RaiseError": "request-termination",
    "EchoRouting": "request-termination",
    "MessageBuffering": "_skip",
    "BufferData": "_skip",
    "SnmpTrap": "http-log",
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
    "SqlAttack": ("pre-function", ReviewFlag.SECURITY_REVIEW),
    "CsrfProtection": ("pre-function", ReviewFlag.SECURITY_REVIEW),
    "TimeRange": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "EncodeDecode": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "KeyValueStore": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "KeyValueStorage": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "KeyValueLookup": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "KeyValueRemove": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "KeyValueStatistics": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    # --- Graphman catalog: auth & identity ---
    "OAuth2Introspection": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    "HttpNegotiate": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    "KerberosAuthentication": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    "NtlmAuthentication": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    "SiteMinderChangePassword": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    "SiteMinderEnableUser": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    "SpecificUser": ("acl", ReviewFlag.IDP_CONFIG_REQUIRED),
    "MemberOfGroup": ("acl", ReviewFlag.IDP_CONFIG_REQUIRED),
    "IdentityAttributes": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "VariableCredentialSource": ("pre-function", ReviewFlag.IDP_CONFIG_REQUIRED),
    "ManageCookie": ("session", ReviewFlag.TRANSFORM_REVIEW),
    "Radius": ("pre-function", ReviewFlag.IDP_CONFIG_REQUIRED),
    # --- Graphman catalog: JWT & crypto ---
    "JwtDecode": ("jwt", ReviewFlag.KEY_CONFIG_REQUIRED),
    "CreateJsonWebKey": ("jwt-signer", ReviewFlag.KEY_CONFIG_REQUIRED),
    "GenerateOAuthSignatureBaseString": ("pre-function", ReviewFlag.KEY_CONFIG_REQUIRED),
    "CsrSigner": ("pre-function", ReviewFlag.KEY_CONFIG_REQUIRED),
    # --- Graphman catalog: GraphQL & validation ---
    "GatewayGraphQL": ("graphql-rate-limiting-advanced", ReviewFlag.TRANSFORM_REVIEW),
    "GraphQLExtractValue": ("jq", ReviewFlag.TRANSFORM_REVIEW),
    "GraphQLSchemaValidation": ("graphql-rate-limiting-advanced", ReviewFlag.TRANSFORM_REVIEW),
    "OdataValidation": ("request-validator", ReviewFlag.TRANSFORM_REVIEW),
    "ApplyJSONPatch": ("jq", ReviewFlag.TRANSFORM_REVIEW),
    # --- Graphman catalog: Kafka ---
    "KafkaRouting": ("kafka-upstream", ReviewFlag.ROUTING_DECISION),
    "KafkaConsumer": ("kafka-upstream", ReviewFlag.ROUTING_DECISION),
    "KafkaTransact": ("kafka-upstream", ReviewFlag.ROUTING_DECISION),
    # --- Graphman catalog: rate limiting & circuit breaker ---
    "CircuitBreaker": ("pre-function", ReviewFlag.TRANSFORM_REVIEW),
    "RateLimitQuery": ("rate-limiting-advanced", ReviewFlag.TRANSFORM_REVIEW),
    "ThroughputQuotaQuery": ("rate-limiting-advanced", ReviewFlag.TRANSFORM_REVIEW),
    # --- Graphman catalog: routing & transport ---
    "HttpRouting": ("_upstream", ReviewFlag.ROUTING_DECISION),
    "Http2Routing": ("_upstream", ReviewFlag.ROUTING_DECISION),
    "Http2Transport": ("_upstream", ReviewFlag.ROUTING_DECISION),
    "Ssl": ("mtls-auth", ReviewFlag.SECURITY_REVIEW),
    "Swagger": ("request-validator", ReviewFlag.TRANSFORM_REVIEW),
    "JSONSchema": ("request-validator", ReviewFlag.TRANSFORM_REVIEW),
    "JsonDocumentStructure": ("json-threat-protection", ReviewFlag.SECURITY_REVIEW),
    "OversizedText": ("xml-threat-protection", ReviewFlag.SECURITY_REVIEW),
    # --- Graphman catalog: observability ---
    "OtelMeter": ("opentelemetry", ReviewFlag.TRANSFORM_REVIEW),
    "IcapAntivirusScanner": ("pre-function", ReviewFlag.SECURITY_REVIEW),
    # --- Graphman catalog: data manipulation ---
    "HtmlFormData": ("request-transformer", ReviewFlag.TRANSFORM_REVIEW),
    "ReplaceTagContent": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "SelectElement": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "LookupDynamicContextVariables": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "IndexLookupByItem": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "ItemLookupByIndex": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    # --- Graphman catalog: SAML aliases ---
    "RequireWssSaml": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    "RequireWssSaml2": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    "SamlIssuer": ("openid-connect", ReviewFlag.IDP_CONFIG_REQUIRED),
    "SetSamlStatus": ("pre-function", ReviewFlag.IDP_CONFIG_REQUIRED),
    # --- Community custom assertions (Layer7-Community/Assertions) ---
    "EvaluateMathExpressionAssertion": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "DelayAssertion": ("pre-function", ReviewFlag.LUA_MIGRATION_REQUIRED),
    "InjectionFilterAssertion": ("pre-function", ReviewFlag.SECURITY_REVIEW),
}

CUSTOM_ASSERTIONS: set[str] = {
    # --- Scripting & transformation ---
    "JavaScript",
    "XslTransformation",
    # --- WS-Security / SOAP ---
    "WssBasic",
    "WssDigest",
    "WssSignature",
    "WssKerberos",
    "WsSecurity",
    "WssEncryptElement",
    "WssSignElement",
    "WssConfiguration",
    "WssReplayProtection",
    "WssVersion",
    "Wssp",
    "WsiBsp",
    "WsiSaml",
    "AddWsAddressing",
    "WsAddressing",
    "AddWssSecurityToken",
    "AddWssTimestamp",
    "AddWssUsernameToken",
    "EncryptedUsernameToken",
    "RequireWssEncryptedElement",
    "RequireWssSignedElement",
    "RequireWssTimestamp",
    "RequireWssX509Cert",
    "RequestWssKerberos",
    "NonSoapDecryptElement",
    "NonSoapEncryptElement",
    "NonSoapSignElement",
    "NonSoapVerifyElement",
    "NonSoapCheckVerifyResults",
    # --- SAML protocol ---
    "SamlBrowserArtifact",
    "SamlProtocol",
    "SamlpRequestBuilder",
    "SamlpResponseBuilder",
    "SamlpResponseEvaluation",
    "ProcessSamlAttributeQueryRequest",
    "ProcessSamlAuthnRequest",
    # --- WS-Federation & WS-Trust ---
    "WsFederationPassiveTokenExchange",
    "WsFederationPassiveTokenRequest",
    "WsTrustCredentialExchange",
    # --- SecureConversation ---
    "SecureConversation",
    "CreateSecurityContextToken",
    "CancelSecurityContext",
    "EstablishOutboundSecureConversation",
    "LookupOutboundSecureConversationSession",
    "BuildRstSoapRequest",
    "BuildRstrSoapResponse",
    "ProcessRstrSoapResponse",
    # --- Protocol routing ---
    "RadiusAuthenticate",
    "JmsRoutingAssertion",
    "JmsRouting",
    "MqNativeRoutingAssertion",
    "MqNativeRouting",
    "MqNativeSupport",
    "FtpRoutingAssertion",
    "SshRoutingAssertion",
    "SshRouteAssertion",
    "RawTcpRoutingAssertion",
    "SimpleRawTransport",
    "SFTPResponse",
    # --- Database ---
    "JdbcQuery",
    "BulkJdbcInsert",
    "CassandraQuery",
    "LDAPQuery",
    "LDAPWrite",
    "LDAPUpdate",
    "MysqlClusterInfo",
    "MysqlCounter",
    # --- WebSocket ---
    "WebSocket",
    "WebSocketConnect",
    "WebSocketEntityManager",
    "WebSocketMessageInjection",
    "WebSocketValidation",
    # --- XMPP ---
    "XMPPAssociateSessions",
    "XMPPCloseSession",
    "XMPPGetAssociatedSessionId",
    "XMPPGetRemoteCertificate",
    "XMPPGetSessionAttribute",
    "XMPPOpenServerSession",
    "XMPPSendToRemoteHost",
    "XMPPSetSessionAttribute",
    "XMPPStartTLS",
    # --- XACML ---
    "XacmlPdpAssertion",
    "XacmlRequestBuilderAssertion",
    # --- MTOM ---
    "MTOMDecodeAssertion",
    "MTOMEncodeAssertion",
    "MTOMValidateAssertion",
    # --- Routing strategy ---
    "CreateRoutingStrategy",
    "ExecuteRoutingStrategy",
    "ProcessRoutingStrategyResult",
    # --- XML & XPath ---
    "AddXmlElement",
    "RemoveXmlElement",
    "RemoveElement",
    "RequestXpathAssertion",
    "RequestXpath",
    "ResponseXpathAssertion",
    "ResponseXpath",
    "XpathCredential",
    "XpathCredentialSource",
    "RequestSwA",
    # --- Identity & custom ---
    "CustomAssertion",
    "CodeInjectionProtection",
    "GenericIdentityManagementService",
    "GatewayManagement",
    "ManagePortalResource",
    "RetrieveServiceWsdl",
    # --- Data manipulation ---
    "ForEachLoop",
    "HttpFormPost",
    "InverseHttpFormPost",
    "MimeToHttpForm",
    "AccumulateData",
    "ManipulateMultivalued",
    "ManipulateMultiValuedVariable",
    "MapValue",
    "Split",
    "JoinVariable",
    "Join",
    "MessageContextAssertion",
    # --- Increments & counters ---
    "GetIncrement",
    "GetApiIncrement",
    "IncrementPostBack",
    "ProcessIncrement",
    # --- UDDI & other ---
    "UDDINotification",
    "FtpCredential",
    "SshCredential",
    # --- Discovered from Layer7-Community repos ---
    "Email",
    "RESTGatewayManagement",
    "SshCommandAssertion",
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
