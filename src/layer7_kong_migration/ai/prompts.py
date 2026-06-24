"""Prompt templates for Claude API calls.

System and user prompts for analyzing Layer 7 assertions and generating
Kong Gateway plugin configurations.
"""

import re

SYSTEM_PROMPT = """You are an expert API gateway migration engineer specializing in converting
Broadcom Layer 7 API Gateway (CA API Gateway) policies to Kong Gateway configurations.

Given a Layer 7 policy assertion (XML), analyze it and produce a Kong Gateway plugin
configuration. Your response MUST be valid JSON with this exact structure:

{
  "kong_plugin_name": "the-kong-plugin",
  "kong_plugin_config": {
    "key": "value"
  },
  "lua_code": "-- Lua code if pre-function/post-function is needed, null otherwise",
  "confidence": 0.0 to 1.0,
  "explanation": "Brief explanation of the mapping",
  "review_notes": ["Items requiring human review"],
  "migration_risks": ["Potential risks or behavioral differences"]
}

Guidelines:
- Prefer standard Kong plugins over custom Lua when possible
- For JavaScript assertions, convert the logic to Lua for pre-function/post-function plugin
- For WS-Security/SOAP assertions, note that Kong is primarily REST-focused
- For protocol-specific routing (JMS, MQ, FTP), suggest architectural alternatives
- Include migration_risks for behavioral differences between Layer 7 and Kong
- Set confidence based on how complete and accurate the mapping is
- For JDBC/LDAP queries in the gateway, suggest moving to backend services
"""

CONDITIONAL_SYSTEM_PROMPT = """You are an expert API gateway migration engineer. The Layer 7 assertion
below has a known Kong plugin mapping, but needs configuration guidance.

Analyze the assertion's specific configuration and provide the optimal
Kong plugin configuration. Your response MUST be valid JSON:

{
  "kong_plugin_name": "the-kong-plugin",
  "kong_plugin_config": {
    "key": "value"
  },
  "lua_code": null,
  "confidence": 0.0 to 1.0,
  "explanation": "Configuration decisions and rationale",
  "review_notes": ["Config items requiring human review"],
  "migration_risks": []
}
"""

TYPE_HINTS: dict[str, str] = {
    "Authentication": "Identify the identity provider type (LDAP, internal, federated) and map to appropriate Kong auth plugin.",
    "SslAssertion": "Check if client certificate auth is required. Map to mtls-auth if so, otherwise just TLS route config.",
    "RequireSaml": "SAML must be converted to OIDC. Identify the IdP, assertion consumer service URL, and attribute mappings.",
    "DecodeJsonWebToken": "Map JWT validation settings: algorithm, public key, claims to validate.",
    "EncodeJsonWebToken": "Map JWT signing: algorithm, key reference, payload claims, expiry.",
    "ThroughputQuota": "Map quota settings to rate-limiting-advanced: window size, limit, counter strategy.",
    "CacheLookup": "Map cache settings to proxy-cache: TTL, cache key, storage strategy.",
    "HttpRoutingAssertion": "Extract backend URL, TLS settings, timeouts, header forwarding rules.",
    "JavaScript": "Convert JavaScript logic to equivalent Lua for Kong's pre-function or post-function plugin.",
    "SetVariable": "Analyze variable usage pattern - may map to request-transformer headers or pre-function Lua.",
    "ComparisonAssertion": "Conditional logic - may map to Kong expressions or pre-function Lua branching.",
    "ForEachLoop": "Loop constructs need Lua implementation. Analyze the iteration pattern and body assertions.",
    "JdbcQuery": "Database queries should move to backend services. Document the query and suggest API-based alternative.",
    "CustomAssertion": "Custom Java assertion - requires complete reimplementation. Document the interface and behavior.",
}

SECRET_PATTERNS = [
    re.compile(r"\$\{secpass\.[^}]+\}"),
    re.compile(r"\$\{gateway\.cluster\.password[^}]*\}"),
    re.compile(r"\$\{stored\.password\.[^}]+\}"),
    re.compile(r"password\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"apikey\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
]


def sanitize_for_prompt(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def build_user_prompt(
    assertion_type: str,
    raw_xml: str,
    configuration: dict,
    resource_content: str = "",
    max_resource_chars: int = 4000,
) -> str:
    safe_xml = sanitize_for_prompt(raw_xml)
    parts = [
        f"## Layer 7 Assertion: {assertion_type}\n",
        f"### Policy XML:\n```xml\n{safe_xml}\n```\n",
        f"### Extracted Configuration:\n```json\n{_format_config(configuration)}\n```\n",
    ]

    if assertion_type in TYPE_HINTS:
        parts.append(f"### Migration Hint:\n{TYPE_HINTS[assertion_type]}\n")

    if resource_content:
        truncated = resource_content[:max_resource_chars]
        if len(resource_content) > max_resource_chars:
            truncated += f"\n... [truncated, {len(resource_content)} chars total]"
        safe_resource = sanitize_for_prompt(truncated)
        parts.append(f"### Resource Content:\n```\n{safe_resource}\n```\n")

    return "\n".join(parts)


def _format_config(config: dict) -> str:
    import json
    clean = {k: v for k, v in config.items() if not k.startswith("_")}
    return json.dumps(clean, indent=2, default=str)
