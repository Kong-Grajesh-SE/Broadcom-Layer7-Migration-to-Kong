"""Intermediate Representation models for Layer 7 gateway policies.

These Pydantic models form the central contract between all pipeline stages:
ingestion -> analysis -> AI orchestration -> generation -> reporting.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Complexity(str, Enum):
    DIRECT = "direct"
    CONDITIONAL = "conditional"
    CUSTOM = "custom"


class ReviewFlag(str, Enum):
    NONE = "none"
    IDP_CONFIG_REQUIRED = "idp_config_required"
    CLAIM_MAPPING_REQUIRED = "claim_mapping_required"
    KEY_CONFIG_REQUIRED = "key_config_required"
    TRANSFORM_REVIEW = "transform_review"
    CACHE_STRATEGY = "cache_strategy"
    ROUTING_DECISION = "routing_decision"
    LUA_MIGRATION_REQUIRED = "lua_migration_required"
    CUSTOM_PLUGIN_REQUIRED = "custom_plugin_required"
    SOAP_MIGRATION = "soap_migration"
    PROTOCOL_UNSUPPORTED = "protocol_unsupported"
    SECURITY_REVIEW = "security_review"
    MANUAL_REVIEW = "manual_review"


ASSERTION_REVIEW_REASONS: dict[str, str] = {
    "Authentication": "IdP configuration and credential store mapping required",
    "RequireSaml": "SAML federation config and IdP metadata must be mapped to OIDC/OAuth",
    "SslAssertion": "mTLS certificate trust chain and client cert policies need manual review",
    "SiteMinderAuthenticate": "CA SSO (SiteMinder) maps to openid-connect plugin - requires OIDC IdP migration",
    "WssBasic": "WS-Security credential handling must be redesigned for REST/Kong patterns",
    "WssSignature": "XML digital signature - no direct Kong equivalent, custom plugin needed",
    "HttpRoutingAssertion": "Backend URL, TLS settings, and connection pool config need review",
    "JmsRoutingAssertion": "JMS routing has no Kong equivalent - requires architecture redesign",
    "MqNativeRoutingAssertion": "MQ Native routing requires custom integration or sidecar pattern",
    "JavaScript": "JavaScript must be converted to Lua for Kong pre-function/post-function plugin",
    "XslTransformation": "XSL transforms require custom Kong plugin or pre-function Lua",
    "JsonTransformationAssertion": "Complex JSON transforms may exceed request-transformer-advanced capabilities",
    "Encapsulated": "Encapsulated assertions are reusable fragments - must be inlined or mapped to shared plugins",
    "Include": "Policy fragment includes must be resolved and flattened before migration",
    "ForEachLoop": "Loop constructs need Lua implementation in pre-function plugin",
    "CacheLookup": "Cache strategy (TTL, invalidation, scope) needs review for proxy-cache plugin",
    "ThroughputQuota": "Quota windows, counters, and sync strategy need mapping to rate-limiting-advanced",
    "SetVariable": "Context variable usage patterns must be analyzed for Kong equivalents",
    "ComparisonAssertion": "Conditional logic must be implemented in Lua or route-level expressions",
    "CustomAssertion": "Custom Java assertions require complete reimplementation",
    "JdbcQuery": "Database queries in the gateway path require architectural review",
    "LDAPQuery": "LDAP integration must be mapped to Kong's ldap-auth or custom plugin",
    "SqlAttackProtection": "SQL injection patterns can be implemented in pre-function Lua with regex matching",
    "CodeInjectionProtection": "Code injection rules need equivalent Kong-side validation",
    "RadiusAuthenticate": "RADIUS auth has no direct Kong plugin - requires custom implementation",
    "DocumentStructureThreat": "XML threat limits map to xml-threat-protection plugin (Enterprise) - verify thresholds",
    "JsonDocumentStructureThreat": "JSON threat limits map to json-threat-protection plugin (Enterprise) - verify thresholds",
    "KafkaRoutingAssertion": "Kafka routing maps to kafka-upstream plugin (Enterprise) - configure brokers and topic",
    "SchemaValidation": "XML/JSON schema validation maps to request-validator plugin (Enterprise, JSON only)",
    "GraphqlSchemaValidation": "GraphQL validation maps to graphql-rate-limiting-advanced (Enterprise) - configure cost strategy",
    "SiteMinderAuthorize": "SiteMinder authorization maps to OPA plugin (Enterprise) - Rego policies required",
    "SiteMinderCheckProtected": "SiteMinder resource check maps to OPA plugin (Enterprise) - Rego policies required",
    "ValidateNonSoapSamlToken": "SAML token validation maps to openid-connect plugin (Enterprise) - OIDC migration",
    "CreateSamlToken": "SAML token creation maps to openid-connect plugin (Enterprise) - OIDC migration",
    "CsrfProtection": "CSRF token validation can be implemented in pre-function Lua",
    "TimeRange": "Time-based access control can be implemented in pre-function Lua",
    "EncodeDecode": "Encoding/decoding operations map to pre-function Lua (ngx.encode_base64, etc.)",
    "KeyValueStore": "Key-value store maps to Kong shared dict or pre-function Lua with ngx.shared",
    "KeyValueLookup": "Key-value lookup maps to Kong shared dict or pre-function Lua with ngx.shared",
    "CustomizeErrorResponse": "Error response customization maps to exit-transformer plugin (Enterprise)",
}


class AssertionConfig(BaseModel):
    """A single Layer 7 policy assertion with its extracted configuration."""

    name: str
    assertion_type: str
    complexity: Complexity = Complexity.CUSTOM
    configuration: dict[str, Any] = Field(default_factory=dict)
    kong_mapping: dict[str, Any] | None = None
    review_flag: ReviewFlag = ReviewFlag.NONE
    review_reason: str = ""
    raw_xml: str = ""
    resource_content: str = ""
    confidence: float = 0.0
    tags: list[str] = Field(default_factory=list)


class FlowStep(BaseModel):
    """A step in a policy flow - references an assertion."""

    assertion_name: str
    condition: str = ""
    enabled: bool = True


class Flow(BaseModel):
    """An ordered sequence of assertion steps (AND/OR logic)."""

    name: str = "main"
    logic: str = "all"  # "all" (AND) or "one_or_more" (OR)
    steps: list[FlowStep] = Field(default_factory=list)
    sub_flows: list["Flow"] = Field(default_factory=list)


class Endpoint(BaseModel):
    """A service endpoint with its backend target."""

    name: str
    url: str = ""
    protocol: str = "https"
    tls_version: str = ""
    connection_timeout_ms: int = 30000
    read_timeout_ms: int = 60000


class ServiceDefinition(BaseModel):
    """A Layer 7 published service with its policy and endpoints."""

    name: str
    service_id: str = ""
    folder_path: str = "/"
    resolution_path: str = ""
    enabled: bool = True
    soap: bool = False
    wsdl_url: str = ""
    endpoints: list[Endpoint] = Field(default_factory=list)
    policy_flow: Flow | None = None
    assertions: list[AssertionConfig] = Field(default_factory=list)
    properties: dict[str, str] = Field(default_factory=dict)


class PolicyBundle(BaseModel):
    """Root IR model: a complete Layer 7 gateway export.

    This is the central data structure passed through every pipeline stage.
    Ingestion populates it, analysis classifies assertions, AI enriches CUSTOM
    assertions, and generation converts it to Kong declarative YAML.
    """

    name: str
    source_format: str = "restman"  # "restman", "gmu", "graphman", "policy_export"
    source_path: str = ""
    gateway_version: str = ""
    services: list[ServiceDefinition] = Field(default_factory=list)
    shared_policies: list[ServiceDefinition] = Field(default_factory=list)
    encapsulated_assertions: list[ServiceDefinition] = Field(default_factory=list)
    cluster_properties: dict[str, str] = Field(default_factory=dict)
    jdbc_connections: list[dict[str, Any]] = Field(default_factory=list)
    stored_passwords: list[str] = Field(default_factory=list)
    certificates: list[dict[str, str]] = Field(default_factory=list)

    @property
    def all_assertions(self) -> list[AssertionConfig]:
        assertions = []
        for svc in self.services:
            assertions.extend(svc.assertions)
        for pol in self.shared_policies:
            assertions.extend(pol.assertions)
        for enc in self.encapsulated_assertions:
            assertions.extend(enc.assertions)
        return assertions

    @property
    def metrics(self) -> dict[str, Any]:
        all_a = self.all_assertions
        total = len(all_a)
        if total == 0:
            return {"total": 0, "direct": 0, "conditional": 0, "custom": 0, "automation_rate": 0.0}
        direct = sum(1 for a in all_a if a.complexity == Complexity.DIRECT)
        conditional = sum(1 for a in all_a if a.complexity == Complexity.CONDITIONAL)
        custom = sum(1 for a in all_a if a.complexity == Complexity.CUSTOM)
        return {
            "total": total,
            "direct": direct,
            "conditional": conditional,
            "custom": custom,
            "direct_rate": direct / total,
            "conditional_rate": conditional / total,
            "custom_rate": custom / total,
            "automation_rate": (direct + conditional) / total,
        }
