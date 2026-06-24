# Broadcom Layer 7 to Kong Migration Framework
## Technical Specification - Kong Gateway Enterprise Edition

**Version 1.0 | June 2026**
**Status: ACTIVE DEVELOPMENT**

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Technology Stack](#2-technology-stack)
3. [Framework Architecture](#3-framework-architecture)
4. [Execution Modes](#4-execution-modes)
5. [Distribution & Deployment](#5-distribution--deployment)
6. [Reference Test Corpus](#6-reference-test-corpus)
7. [Validation Environment](#7-validation-environment)
8. [Layer 7 Parsing Specifications](#8-layer-7-parsing-specifications)
9. [Kong Generation Specifications](#9-kong-generation-specifications)
10. [Kong Enterprise Plugin Reference](#10-kong-enterprise-plugin-reference)
11. [Assertion-to-Plugin Mapping Reference](#11-assertion-to-plugin-mapping-reference)
12. [Intermediate Representation Schema](#12-intermediate-representation-schema)
13. [Vault and Secrets Migration](#13-vault-and-secrets-migration)
14. [Knowledge Extension Framework](#14-knowledge-extension-framework)
15. [AI Orchestration Layer](#15-ai-orchestration-layer)
16. [Implementation Status](#16-implementation-status)
17. [Appendices](#17-appendices)

---

## 1. Executive Summary

### 1.1 Purpose

This specification defines the architecture and implementation of a Claude Code-powered automation framework designed to accelerate Broadcom Layer 7 API Gateway (CA API Gateway) to Kong Gateway Enterprise migrations. The framework automates 75–85% of migration work while intelligently identifying edge cases requiring manual intervention or AI-assisted analysis.

### 1.2 Scope

The framework addresses migrations from Broadcom Layer 7 API Gateway (versions 9.x, 10.x, 11.x) to **Kong Gateway Enterprise** deployed in hybrid, on-premise, or cloud-managed environments. It supports all major Layer 7 export formats: RESTMAN XML bundles, GMU export directories, Graphman JSON (imploded and exploded), and standalone policy XML.

### 1.3 Target Outcomes

| Metric | Target | Current Status |
|--------|--------|----------------|
| Config Generated Rate | ≥80% on enterprise exports | 83% on OTK bundle (130 policies) |
| Time Reduction | 50–60% vs. manual migration | Estimated |
| Accuracy Rate | >95% for automated conversions | Validated for DIRECT assertions |
| Review Flag Precision | >90% correct identification of edge cases | Implemented |
| Pattern Match Rate | >70% for learned patterns | Implemented |
| AI-Enhanced Coverage | CUSTOM assertions analyzed by Claude | Implemented |
| Ingestion Success Rate | 100% of test corpus samples | 100% (all samples + OTK) |
| Classification Accuracy | 95% match to expected complexity | Validated |
| Unit Test Pass Rate | 100% | **58/58 tests passing** |
| Assertion Types Classified | >100 | **273 types across 3 tiers** |
| Assertion Extractors | >50 | **72 registered extractors** |
| Vault Migration | Cluster props, secrets, certs, keys | Implemented |

### 1.4 Implementation Status Summary

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 1: Core Infrastructure | **COMPLETE** | 100% |
| Phase 2: Ingestion (RESTMAN + Graphman) | **COMPLETE** | 100% |
| Phase 3: Three-Tier Classification | **COMPLETE** | 100% |
| Phase 4: Plugin Generation (DIRECT) | **COMPLETE** | 100% |
| Phase 5: Pattern Matcher | **COMPLETE** | 100% |
| Phase 6: AI-Assisted Migration | **COMPLETE** | 100% |
| Phase 7: Vault & Secrets Migration | **COMPLETE** | 100% |
| Phase 8: Reporting (HTML + Talking Points) | **COMPLETE** | 100% |
| Phase 9: Real Policy Validation (OTK) | **COMPLETE** | 100% |
| Phase 10: Multi-Agent Parallel Execution | Planned | 0% |
| Phase 11: Behavioral Tests | Planned | 0% |
| Phase 12: Release Kit | Planned | 0% |

---

## 2. Technology Stack

### 2.1 Design Principles

- **Field Modifiability** - Consultants can adjust mappings and patterns in customer environments without complex build cycles
- **Minimal Dependencies** - Core functionality works with a focused set of well-maintained libraries
- **Security** - Safe handling of untrusted input (customer-provided gateway bundles) via `defusedxml` XXE prevention
- **Performance** - Efficient processing for batch migrations across hundreds of services
- **Enterprise-First** - Generated configurations target Kong Gateway Enterprise features and plugins
- **Format Agnostic** - Supports all Layer 7 export formats (RESTMAN, GMU, Graphman, standalone XML)

### 2.2 Core Technologies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Language | Python | 3.12+ | Primary development language |
| Package Manager | uv | Latest | Dependency management and virtual environments |
| Configuration | Dynaconf | 3.2+ | Multi-environment settings management |
| Secrets | `.secrets.toml` | - | API key and credential management (gitignored) |
| CLI | Typer | 0.12+ | Type-safe command-line interface |
| Rich Output | Rich | 13.7+ | Terminal formatting and tables |
| Templating | Jinja2 | 3.1+ | Template rendering for reports |

### 2.3 Python Dependency Management

**Always use `uv` - never `pip` directly.**

```bash
uv sync                       # Install/update all dependencies
uv run migrate --help         # Run CLI
uv run pytest tests/          # Run unit tests
```

### 2.4 XML, JSON, and YAML Processing

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| XML Parsing | lxml | 5.1+ | Layer 7 policy XML parsing with XPath and namespace support |
| XML Security | defusedxml | 0.7+ | Safe parsing (prevents XXE, entity expansion attacks) |
| YAML Processing | ruamel.yaml | 0.18+ | Kong config generation with comment preservation |
| JSON Parsing | stdlib `json` | - | Graphman bundle parsing |

### 2.5 HTTP, AI, and Data Validation

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Data Validation | Pydantic | 2.5+ | Intermediate Representation schema validation |
| AI Integration | anthropic | 0.40+ | Claude API for CUSTOM assertion analysis |

### 2.6 Testing Framework

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Test Runner | pytest | 9.1+ | Unit and integration tests |
| Coverage | pytest-cov | 7.1+ | Test coverage reporting |
| Linting | Ruff | 0.5+ | Python linting and formatting |
| Type Checking | mypy | 1.8+ | Static type analysis (strict mode) |

### 2.7 Version Compatibility

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.10 | 3.12+ |
| Kong Gateway Enterprise | 3.4 | 3.14+ |
| Docker | 24.0 | 25.0+ |
| Docker Compose | 2.20 | 2.24+ |
| Layer 7 Gateway | 9.x | 10.x / 11.x |

---

## 3. Framework Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                LAYER 7 → KONG MIGRATION FRAMEWORK                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────┐   │
│  │    INGESTION     │───▶│    ANALYSIS       │───▶│   PATTERN MATCHER   │   │
│  │     MODULE       │    │     ENGINE        │    │        [✓]          │   │
│  │      [✓]         │    │      [✓]          │    │                     │   │
│  │ • RESTMAN XML    │    │ • 3-Tier Classify │    │ • Weighted scoring  │   │
│  │ • Graphman JSON  │    │ • 35 DIRECT       │    │ • 20 pattern files  │   │
│  │ • GMU Directory  │    │ • 109 CONDITIONAL │    │ • AI-learned cache  │   │
│  │ • Standalone XML │    │ • 129 CUSTOM      │    │ • 2 ref catalogs    │   │
│  └──────────────────┘    └──────────────────┘    └──────────────────────┘   │
│         │                        │                        │                 │
│         ▼                        ▼                        ▼                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                KNOWLEDGE REFERENCE LIBRARY                           │   │
│  │  Assertion Mappings [✓] | Patterns [✓] | AI Cache [✓] | OTK [✓]      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│         ┌────────────────────┼────────────────────┐                         │
│         ▼                    ▼                    ▼                         │
│  ┌───────────────┐  ┌───────────────────┐  ┌──────────────────┐             │
│  │  GENERATION   │  │  VAULT & SECRETS  │  │   AI ANALYSIS    │             │
│  │    ENGINE     │  │     MAPPER        │  │   ORCHESTRATOR   │             │
│  │     [✓]       │  │      [✓]          │  │      [✓]         │             │
│  │ • Kong YAML   │  │ • Cluster Props   │  │ • Pattern Match  │             │
│  │ • 23 plugin   │  │ • Stored Passwords│  │ • Cache Check    │             │
│  │   generators  │  │ • Certificates    │  │ • Claude API     │             │
│  │ • Vault refs  │  │ • JDBC Creds      │  │ • Pattern Learn  │             │
│  └───────┬───────┘  │ • JWT Keys        │  └──────────────────┘             │
│          │          └───────────────────┘                                   │
│          ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    REPORTING LAYER [✓]                               │   │
│  │   HTML Report | Talking Points | Vault Reference Map | Env Template  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │               VALIDATION ENVIRONMENT [✓]                             │   │
│  │   Kong 3.14 Docker | Node Mock API | 58 Unit Tests                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Module Specifications

#### 3.2.1 Ingestion Module

**Purpose:** Parse and normalize Layer 7 gateway exports into a structured intermediate representation.

**Implementation:** `src/layer7_kong_migration/ingestion/`

- `bundle.py` - `BundleLoader` class: auto-detects format, delegates to appropriate parser
- `parser.py` - `PolicyParser` class: XML namespace handling (`l7:`, `L7p:`, `wsp:`, `exp:`)
- `extractors.py` - 72 assertion-specific extractors with dispatch table
- `graphman.py` - `GraphmanParser` class: imploded JSON, exploded directory, JSON-to-XML code conversion

**Supported Formats:**

| Format | Detection | Parser |
|--------|-----------|--------|
| RESTMAN Item XML | Root `<l7:Item>` | `PolicyParser._parse_restman_item()` |
| RESTMAN Bundle XML | Root `<l7:Bundle>` | `PolicyParser._parse_restman_bundle()` |
| Policy Export XML | Root `<exp:Export>` | `PolicyParser._parse_policy_export()` |
| Standalone Policy XML | Root `<wsp:Policy>` or `<wsp:All>` | `PolicyParser._parse_standalone_policy()` |
| Graphman JSON (imploded) | `.json` with `policies`/`services` arrays | `GraphmanParser._parse_imploded()` |
| Graphman JSON (exploded) | Directory with `*.policy.json` files | `GraphmanParser._parse_exploded()` |
| ZIP archive | `.zip` extension | Auto-extracts, parses directory |
| GMU directory | Directory with `.xml`/`.json` files | Iterates all files, merges results |

**Key Libraries:** `lxml` (XPath), `defusedxml` (XXE prevention), `Pydantic` (validation)

**XML Namespaces:**

| Prefix | URI | Purpose |
|--------|-----|---------|
| `l7:` | `http://ns.l7tech.com/2010/04/gateway-management` | RESTMAN management API |
| `L7p:` | `http://www.layer7tech.com/ws/policy` | Policy assertion elements |
| `wsp:` | `http://schemas.xmlsoap.org/ws/2002/12/policy` | WS-Policy structure (All, OneOrMore) |
| `exp:` | `http://www.layer7tech.com/ws/policy/export` | Policy Manager export format |

#### 3.2.2 Analysis Engine

**Purpose:** Classify assertions by migration complexity and identify transformation requirements.

**Implementation:** `src/layer7_kong_migration/analysis/`

- `classifier.py` - `AssertionClassifier` with three classification tiers
- `mapper.py` - Policy-to-plugin mapping utilities from YAML knowledge base

**Classification Tiers:**

| Tier | Count | Confidence | Action |
|------|-------|------------|--------|
| DIRECT | 35 types | 1.0 | Auto-generate Kong plugin config |
| CONDITIONAL | 109 types | 0.7 | Generate with review flags |
| CUSTOM | 129 types | 0.0 | Requires AI analysis or manual implementation |

#### 3.2.3 Pattern Matcher

**Purpose:** Match assertions against learned patterns for auto-generation of previously CUSTOM assertions.

**Implementation:** `src/layer7_kong_migration/patterns/`

- `matcher.py` - `PatternMatcher` with weighted similarity scoring
- `library.py` - `PatternLibrary` loads YAML pattern files from `knowledge/patterns/`

**Confidence Thresholds:**
- **≥85%** - Auto-generate, low review priority
- **60–84%** - Auto-generate with HIGH review flag
- **<60%** - Escalate to CUSTOM

**Similarity Scoring Weights:**

| Factor | Weight |
|--------|--------|
| Assertion type match | 35% |
| Config key overlap | 25% |
| Keyword overlap | 15% |
| Config value similarity | 15% |
| Metadata match | 10% |

#### 3.2.4 Generation Engine

**Purpose:** Produce Kong Gateway Enterprise configurations from analyzed Layer 7 bundles.

**Implementation:** `src/layer7_kong_migration/generation/`

- `kong.py` - `KongGenerator` produces Kong YAML v3.0 with optional vault reference resolution
- `plugins.py` - 23 assertion-specific plugin generators with dispatch table
- `vaults.py` - `VaultMapper` maps cluster properties, secrets, certificates, and keys to Kong vaults

**Implemented Plugin Generators (16 functions, 23 dispatch entries):**

| Generator | Layer 7 Assertion | Kong Enterprise Plugin |
|-----------|-------------------|------------------------|
| `_gen_basic_auth` | HttpBasic | basic-auth |
| `_gen_key_auth` | LookupApiKey | key-auth |
| `_gen_cors` | CorsAssertion | cors |
| `_gen_rate_limiting` | RateLimit, DistributedRateLimit | rate-limiting / rate-limiting-advanced |
| `_gen_request_size_limiting` | RequestSizeLimit | request-size-limiting |
| `_gen_ip_restriction` | RemoteIpRange | ip-restriction |
| `_gen_request_termination` | HardcodedResponse, EchoRoutingAssertion | request-termination |
| `_gen_http_log` | AuditDetailAssertion, AuditAssertion | http-log |
| `_gen_request_transformer` | AddHeader, RemoveHeader | request-transformer / response-transformer |
| `_gen_xml_threat_protection` | DocumentStructureThreat | xml-threat-protection (Enterprise) |
| `_gen_json_threat_protection` | JsonDocumentStructureThreat | json-threat-protection (Enterprise) |
| `_gen_kafka_upstream` | KafkaRoutingAssertion | kafka-upstream (Enterprise) |
| `_gen_exit_transformer` | CustomizeErrorResponse | exit-transformer (Enterprise) |
| `_gen_graphql_rate_limiting` | GraphqlSchemaValidation | graphql-rate-limiting-advanced (Enterprise) |
| `_gen_opa` | SiteMinderAuthorize, SiteMinderCheckProtected | opa (Enterprise) |
| `_gen_openid_connect` | SiteMinderAuthenticate, ValidateNonSoapSamlToken, CreateSamlToken | openid-connect (Enterprise) |
| `integrate_ai_results` | (any AI-analyzed) | AI-generated plugin config |

#### 3.2.5 Vault & Secrets Mapper

**Purpose:** Map Layer 7 gateway-wide configuration entities to Kong's native secret management.

**Implementation:** `src/layer7_kong_migration/generation/vaults.py`

**Entity Mapping:**

| Layer 7 Entity | Kong Entity | Details |
|----------------|-------------|---------|
| Cluster Properties | Kong Vaults (`{vault://...}`) | Runtime resolution from env vars or secrets manager |
| Stored Passwords | Kong Vaults (secret entries) | Redacted in env template |
| Certificates | Kong Certificates / CA Certificates | TLS/mTLS with SNI mapping |
| JWT Keys (from assertions) | Kong Keys / Key Sets | JWK format for jwt/jwt-signer plugins |
| JDBC Connections (credentials) | Kong Vaults (URL, user, password) | Connection string decomposed |

**Supported Vault Backends:**

| Backend | Kong Plugin Name | Use Case |
|---------|-----------------|----------|
| `env` | `env` | Environment variables (default, simplest) |
| `aws` | `aws` | AWS Secrets Manager |
| `hcv` | `hcv` | HashiCorp Vault |
| `gcp` | `gcp` | GCP Secret Manager |

**Output Files:**
- `kong-vaults.yaml` - Kong declarative config for vaults, certificates, keys
- `vault.env.template` - Environment variable template with `L7_MIGRATED_` prefix
- `vault-reference-map.txt` - Layer 7 name → Kong vault reference lookup

#### 3.2.6 Review Flag Module

**Purpose:** Identify and document items requiring human review.

**Flag Categories:**

| Flag | Description |
|------|-------------|
| `IDP_CONFIG_REQUIRED` | Identity provider type determines exact Kong auth plugin |
| `CLAIM_MAPPING_REQUIRED` | JWT/SAML claim mappings need adjustment |
| `KEY_CONFIG_REQUIRED` | JWT signing/validation key configuration needed |
| `TRANSFORM_REVIEW` | Complex transformations may exceed plugin capabilities |
| `CACHE_STRATEGY` | Cache TTL, scope, and invalidation strategy need review |
| `ROUTING_DECISION` | Backend URL, TLS settings, connection pool config need review |
| `LUA_MIGRATION_REQUIRED` | JavaScript/logic must be converted to Lua |
| `CUSTOM_PLUGIN_REQUIRED` | No Kong equivalent - requires custom plugin |
| `SOAP_MIGRATION` | SOAP services need API modernization |
| `PROTOCOL_UNSUPPORTED` | JMS, MQ, FTP, SSH - requires architectural redesign |
| `SECURITY_REVIEW` | mTLS, certificate validation needs security team review |
| `MANUAL_REVIEW` | Encapsulated assertions, policy fragments need manual resolution |

#### 3.2.7 Reporting Layer

**Purpose:** Generate customer-facing migration reports and talking points.

**Implementation:** `src/layer7_kong_migration/reporting/`

- `html_report.py` - `HTMLReportGenerator`: self-contained HTML with inline CSS, metrics cards, assertion table, Kong YAML preview, gauge charts
- `talking_points.py` - `TalkingPointsGenerator`: Markdown talking points with timeline estimates, executive summary, tier explanations, business value

---

## 4. Execution Modes

### 4.1 Dual-Mode Architecture

| Mode | Tool | Use Case | Throughput |
|------|------|----------|------------|
| Interactive | Claude Code | Pattern discovery, single service, edge cases | Single service |
| Scaled | Agent SDK | Batch processing, production migrations | 50+ services/hour (planned) |

### 4.2 Interactive Mode CLI Commands

```bash
# Analyze a Layer 7 bundle
uv run migrate analyze /path/to/bundle.xml

# Generate Kong Enterprise configuration
uv run migrate generate /path/to/bundle.xml --output kong.yaml

# Generate with AI analysis of CUSTOM assertions
uv run migrate generate /path/to/bundle.xml --ai --output kong.yaml

# Generate with AI analysis of both CUSTOM and CONDITIONAL
uv run migrate generate /path/to/bundle.xml --ai --ai-conditional --output kong.yaml

# Generate vault/secrets migration
uv run migrate vaults /path/to/bundle.xml -b env -o vault-output/
uv run migrate vaults /path/to/bundle.xml -b aws -o vault-output/

# Generate HTML migration report
uv run migrate report /path/to/bundle.xml --ai -o report.html

# Generate customer-facing talking points
uv run migrate talking-points /path/to/bundle.xml -o points.md

# Pattern operations
uv run migrate pattern list
uv run migrate pattern search "rate limit"
```

### 4.3 Graphman JSON Support

The framework natively handles Graphman exports - the modern management API format used by Layer 7 11.x:

```bash
# Imploded Graphman bundle (single JSON file)
uv run migrate analyze /path/to/graphman-bundle.json

# Exploded Graphman directory (individual .policy.json files)
uv run migrate analyze /path/to/graphman-export/

# OTK (OAuth Token Kit) customizations
uv run migrate analyze /path/to/otk-customizations-single.json
```

---

## 5. Distribution & Deployment

### 5.1 Deployment Models

| Model | Claude Provider | Network | Use Case |
|-------|----------------|---------|----------|
| Direct API | Anthropic | Internet | Standard deployments |
| AWS Bedrock | Amazon | AWS VPC | AWS-centric customers |
| Google Vertex AI | Google | GCP VPC | GCP-centric customers |
| Azure AI Foundry | Microsoft | Azure VNet | Azure-centric customers |

### 5.2 Data Flow Security

```
┌─────────────────────────────────────────────────────────────────┐
│                    CUSTOMER NETWORK                             │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │  Layer 7     │    │   Migration  │    │   Generated      │   │
│  │  Exports     │───▶│   Framework  │───▶│   Kong Configs   │   │
│  │  (Source)    │    │   (Local)    │    │   (Output)       │   │
│  │              │    │              │    │   + Vault Config │   │
│  └──────────────┘    └──────┬───────┘    └──────────────────┘   │
│                             │                                   │
│                             │ Structured Prompts Only           │
│                             │ (Secrets sanitized before sending)│
│                             ▼                                   │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              ▼
               ┌──────────────────────────┐
               │     Claude API           │
               │  (Anthropic / Bedrock /  │
               │   Vertex / Foundry)      │
               └──────────────────────────┘
```

**Secret Sanitization:** Before any assertion XML is sent to Claude, the `sanitize_for_prompt()` function strips:
- `${secpass.*}` gateway secret references
- `${gateway.cluster.password*}` cluster passwords
- `${stored.password.*}` stored password references
- Inline password/apikey assignments

### 5.3 Project Structure

```
layer7-kong-migration/
├── README.md
├── CLAUDE.md                           # Claude Code context
├── pyproject.toml
├── .python-version                     # 3.13
│
├── src/
│   └── layer7_kong_migration/
│       ├── cli.py                      # Typer CLI entry point (7 commands)
│       ├── ingestion/                  # XML/JSON parsing, bundle loading
│       │   ├── bundle.py              # BundleLoader (XML, ZIP, JSON, directory)
│       │   ├── parser.py             # PolicyParser (RESTMAN, standalone, export)
│       │   ├── extractors.py         # 72 assertion-specific extractors
│       │   └── graphman.py           # GraphmanParser (imploded, exploded, code-to-XML)
│       ├── analysis/                   # Assertion classification, mapping
│       │   ├── classifier.py          # 3-tier: 35 DIRECT, 109 CONDITIONAL, 129 CUSTOM
│       │   └── mapper.py             # YAML mapping loader
│       ├── generation/                 # Kong YAML + vault generation
│       │   ├── kong.py               # KongGenerator (declarative YAML v3.0)
│       │   ├── plugins.py            # 23 plugin generators + AI integration
│       │   └── vaults.py             # VaultMapper (env, aws, hcv, gcp backends)
│       ├── patterns/                   # Pattern matching engine
│       │   ├── matcher.py            # Weighted similarity scoring
│       │   └── library.py            # YAML pattern library loader
│       ├── ai/                         # Claude API integration
│       │   ├── analyzer.py           # AIAnalyzer orchestrator
│       │   ├── client.py             # Claude API wrapper with retry/rate-limit
│       │   ├── prompts.py            # System/user prompt templates + sanitization
│       │   ├── cache.py              # MD5-keyed YAML cache
│       │   ├── learner.py            # High-confidence → reusable pattern extraction
│       │   └── config.py             # Dynaconf settings loader
│       ├── reporting/                  # HTML report + talking points
│       │   ├── html_report.py        # Self-contained HTML with inline CSS
│       │   └── talking_points.py     # Markdown talking points
│       ├── models/                     # Pydantic IR and Kong output models
│       │   ├── ir.py                 # PolicyBundle, AssertionConfig, Flow, Endpoint
│       │   └── kong.py              # KongConfig, KongService, KongVault, KongKey, etc.
│       └── utils/
│           └── xml.py                # XML utility helpers
│
├── config/
│   ├── settings.toml                   # AI model, thresholds, cache settings
│   └── .secrets.toml                   # ANTHROPIC_API_KEY (gitignored)
│
├── knowledge/
│   ├── mappings/
│   │   └── assertion-to-plugin.yaml   # 54 assertion→plugin mappings with notes
│   ├── patterns/                       # 20 migration pattern files
│   │   ├── rate-limit-basic.yaml      # Basic rate limiting
│   │   ├── cors-standard.yaml         # CORS configuration
│   │   ├── basic-auth-ldap.yaml       # LDAP authentication
│   │   ├── jwt-decode-validate.yaml   # JWT validation + claims
│   │   ├── jwt-validation-claims.yaml # JWT claims mapping
│   │   ├── oauth2-token-validation.yaml # OAuth2 token introspection
│   │   ├── backend-routing.yaml       # HTTP routing + TLS
│   │   ├── org-rate-quota.yaml        # Org-level throughput quota
│   │   ├── json-schema-validation.yaml # JSON schema validation
│   │   ├── xml-schema-validation.yaml # XML schema validation
│   │   ├── graphql-depth-limiting.yaml # GraphQL depth + cost limiting
│   │   ├── mtls-certificate-validation.yaml # mTLS client cert
│   │   ├── threat-protection-layered.yaml # SQL/XSS/XML threat protection
│   │   ├── log4shell-security-filter.yaml # Log4Shell pattern detection
│   │   ├── opa-integration.yaml       # OPA authorization (JWT + RBAC)
│   │   ├── ai-gateway-proxy.yaml      # AI Gateway LLM proxy
│   │   ├── otk-fapi-compliance.yaml   # FAPI/CIBA compliance
│   │   ├── config-cache-scheduled.yaml # Scheduled tasks + caching
│   │   ├── metrics-offboxing.yaml     # Prometheus/OpenTelemetry metrics
│   │   └── custom-assertions-extended.yaml # SSH, math, delay, injection filter
│   └── reference/                      # Authoritative catalogs
│       ├── assertion-type-catalog.yaml # All 273 assertion types by category
│       └── graphman-entity-types.yaml  # 47 active + 11 deprecated entity types
│
├── samples/                            # Test bundles
│   ├── simple-auth-service/           # 9 assertions (100% automation)
│   ├── rate-limited-service/          # 8 assertions (100% automation)
│   ├── complex-routing-service/       # 16 assertions (75% automation)
│   └── real-policies/                 # Real Layer 7 policies from production
│       ├── audit/                     # Audit filter/viewer policies
│       ├── cassandra/                 # Cassandra query policies
│       ├── jdbc/                      # JDBC query policies
│       ├── jms/                       # JMS routing policies
│       ├── mqnative/                  # MQ Native routing policies
│       ├── idprovider/               # Identity provider policies
│       ├── global/                    # Global received/completed policies
│       ├── routing/                   # Basic auth, cluster property policies
│       └── otk/                       # OTK: 130 OAuth/OIDC policies (Graphman JSON)
│
├── tests/                              # 58 unit tests
│   └── unit/
│       ├── test_parser.py            # 8 tests - XML parsing
│       ├── test_classifier.py        # 15 tests - classification matrix
│       ├── test_extractors.py        # 6 tests - assertion extractors
│       ├── test_generator.py         # 6 tests - Kong YAML generation
│       ├── test_graphman.py          # 11 tests - Graphman JSON parser
│       └── test_vaults.py            # 12 tests - vault/secrets mapping
│
├── validation/                         # Kong Enterprise Docker environment
│   ├── docker-compose.yml             # Kong 3.14 + Node mock API
│   ├── kong.yaml                      # Generated config for testing
│   └── mock-api/
│       └── server.js                  # Echo server (Node.js)
│
├── bin/                                # Shell scripts
│   ├── validation-up.sh               # Start Kong + mock API
│   ├── validation-reload.sh           # Reload Kong config
│   └── validation-down.sh             # Tear down environment
│
└── doc/
    └── Layer7_Kong_Migration_Framework_Specification_v1.0.md  ← this file
```

### 5.4 Installation

```bash
cd layer7-kong-migration
uv sync
uv run migrate --help  # Verify installation
```

---

## 6. Reference Test Corpus

### 6.1 Overview

The Reference Test Corpus contains synthetic sample bundles and real Layer 7 production policies including the complete OTK (OAuth Token Kit) customization set.

### 6.2 Sample Bundles

| Sample | Assertions | Automation Rate | Assertion Types |
|--------|------------|-----------------|-----------------|
| `simple-auth-service` | 9 | **100%** (6D/3C/0X) | HttpBasic, Authentication, SslAssertion, RateLimit, CorsAssertion, RequestSizeLimit, AddHeader, HttpRoutingAssertion, AuditDetailAssertion |
| `rate-limited-service` | 8 | **100%** (3D/5C/0X) | LookupApiKey, RemoteIpRange, RateLimit, ThroughputQuota, CacheLookup, CacheStorage, DecodeJsonWebToken, HttpRoutingAssertion |
| `complex-routing-service` | 16 | **75%** (4D/8C/4X) | SslAssertion, DecodeJsonWebToken, SetVariable, SqlAttackProtection, CodeInjectionProtection, JavaScript, JsonSchemaAssertion, Regex, ComparisonAssertion, ForEachLoop, HttpRoutingAssertion, AddHeader, AuditDetailAssertion, RequestSizeLimit, CustomizeErrorResponse |

### 6.3 Real Production Policies

| Source | Format | Policies | Assertions | Unique Types |
|--------|--------|----------|------------|--------------|
| OTK Customizations | Graphman JSON | 130 | 1,596 | 44 |
| Audit policies | XML | 3 | 23 | - |
| JDBC policies | XML | 2 | - | - |
| JMS policy | XML | 1 | - | - |
| MQ Native policy | XML | 1 | - | - |
| Cassandra policy | XML | 1 | - | - |
| Identity provider | XML | 1 | - | - |
| Global policies | XML | 2 | - | - |
| Routing policies | XML | 2 | - | - |

### 6.4 OTK (OAuth Token Kit) Analysis Results

The OTK bundle is the highest-fidelity test - 130 real OAuth/OIDC customization policies from Broadcom's official toolkit.

| Metric | Value |
|--------|-------|
| Total assertions | 1,596 |
| DIRECT | 674 (42%) |
| CONDITIONAL | 649 (41%) |
| CUSTOM | 273 (17%) |
| **Automation rate** | **83%** |
| Unique assertion types | 44 |
| Cluster properties | 79 |
| JWT Key Sets generated | 15 |
| JWT Keys generated | 21 |
| Secrets requiring replacement | 48 |

**OTK Assertion Type Distribution:**

| Type | Count | Classification |
|------|-------|---------------|
| SetVariable | High | CONDITIONAL |
| HttpRoutingAssertion | High | CONDITIONAL |
| ComparisonAssertion | High | CONDITIONAL |
| AddHeader | High | DIRECT |
| CommentAssertion | High | DIRECT |
| RaiseError | Moderate | DIRECT |
| FalseAssertion | Moderate | DIRECT |
| DecodeJsonWebToken | Moderate | CONDITIONAL |
| EncodeJsonWebToken | Moderate | CONDITIONAL |
| EvaluateJsonPathExpression | Moderate | CONDITIONAL |
| Include | Moderate | CONDITIONAL |
| Encapsulated | Moderate | CONDITIONAL |
| CustomAssertion | Moderate | CUSTOM |
| JavaScript | Moderate | CUSTOM |
| ForEachLoop | Low | CUSTOM |

---

## 7. Validation Environment

### 7.1 Overview

The Validation Environment provides runtime verification that generated Kong Enterprise configurations deploy and behave correctly.

**Components:**
- Kong Gateway 3.14 (Docker, DB-less declarative mode)
- Mock API Service (Node.js echo server)
- Shell scripts for lifecycle management

### 7.2 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     VALIDATION ENVIRONMENT                              │
│                                                                         │
│  ┌──────────────┐   :8000   ┌──────────────────┐   :8080  ┌──────────┐  │
│  │    Test      │──────────▶│  Kong Gateway     │─────────▶│ Mock API │ │
│  │   Runner     │           │   (DB-less)       │          │ (Node)   │ │
│  │   (pytest)   │           └────────┬──────────┘          └──────────┘ │
│  └──────────────┘                    │ :8001                            │
│                            ┌─────────┴────────┐                         │
│                            │   Admin API      │                         │
│                            │  (Health + Info) │                         │
│                            └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Shell Scripts

```bash
bin/validation-up.sh      # Start Kong 3.14 + Node mock API, wait for health
bin/validation-reload.sh  # Copy kong.yaml and reload Kong config
bin/validation-down.sh    # Stop environment
```

### 7.4 Test Suite Summary

**Unit Tests (58 tests):**

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `test_parser.py` | 8 | XML parsing (standalone, RESTMAN, config extraction, raw XML) |
| `test_classifier.py` | 15 | Classification (direct/conditional/custom, parametrized matrix) |
| `test_extractors.py` | 6 | Assertion extractors (rate limit, CORS, HTTP routing, JavaScript) |
| `test_generator.py` | 6 | Kong YAML generation (services, routes, plugins, consumers, tags) |
| `test_graphman.py` | 11 | Graphman parser (imploded, exploded, code-to-XML, cluster props) |
| `test_vaults.py` | 12 | Vault mapper (cluster props, secrets, JDBC, certs, env manifest) |

---

## 8. Layer 7 Parsing Specifications

### 8.1 Layer 7 Policy Structure

Layer 7 policies use a WS-Policy XML structure with `L7p:` namespaced assertion elements:

```xml
<wsp:Policy xmlns:L7p="http://www.layer7tech.com/ws/policy"
            xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy">
    <wsp:All wsp:Usage="Required">
        <L7p:SslAssertion>
            <L7p:RequireClientAuthentication booleanValue="true"/>
        </L7p:SslAssertion>
        <L7p:HttpBasic/>
        <L7p:Authentication>
            <L7p:IdentityProviderOid goidValue="00000000..."/>
        </L7p:Authentication>
        <L7p:RateLimit>
            <L7p:MaxRequestsPerSecond intValue="100"/>
        </L7p:RateLimit>
        <L7p:HttpRoutingAssertion>
            <L7p:ProtectedServiceUrl stringValue="https://backend:8443/api"/>
        </L7p:HttpRoutingAssertion>
    </wsp:All>
</wsp:Policy>
```

**Flow Logic:**
- `<wsp:All>` - AND logic: all child assertions must pass
- `<wsp:OneOrMore>` - OR logic: at least one child must pass
- `<wsp:ExactlyOne>` - XOR logic: exactly one child must pass
- Assertions can be nested in flow elements to arbitrary depth

### 8.2 RESTMAN Bundle Structure

```xml
<l7:Item xmlns:l7="http://ns.l7tech.com/2010/04/gateway-management">
    <l7:Bundle>
        <l7:References>
            <l7:Item>
                <l7:Type>SERVICE</l7:Type>
                <l7:Resource>
                    <l7:Service>
                        <l7:ServiceDetail>
                            <!-- URL pattern, properties, SOAP flag -->
                        </l7:ServiceDetail>
                        <l7:Resources>
                            <l7:ResourceSet>
                                <l7:Resource type="policy">
                                    <!-- Policy XML embedded here -->
                                </l7:Resource>
                            </l7:ResourceSet>
                        </l7:Resources>
                    </l7:Service>
                </l7:Resource>
            </l7:Item>
            <!-- POLICY, ENCAPSULATED_ASSERTION, CLUSTER_PROPERTY, JDBC_CONNECTION, STORED_PASSWORD items -->
        </l7:References>
    </l7:Bundle>
</l7:Item>
```

**Supported Item Types:**

| Item Type | Parsed Entity | IR Target |
|-----------|--------------|-----------|
| `SERVICE` | Published service + embedded policy | `PolicyBundle.services` |
| `POLICY` | Shared/global policy fragment | `PolicyBundle.shared_policies` |
| `ENCAPSULATED_ASSERTION` | Reusable assertion component | `PolicyBundle.encapsulated_assertions` |
| `CLUSTER_PROPERTY` | Gateway-wide property | `PolicyBundle.cluster_properties` |
| `JDBC_CONNECTION` | Database connection config | `PolicyBundle.jdbc_connections` |
| `STORED_PASSWORD` | Encrypted secret reference | `PolicyBundle.stored_passwords` |

### 8.3 Graphman JSON Structure

```json
{
    "policies": [
        {
            "goid": "...",
            "guid": "...",
            "name": "My Policy",
            "policyType": "SERVICE | FRAGMENT | GLOBAL",
            "folderPath": "/path/to/folder",
            "soap": false,
            "policy": {
                "xml": "<wsp:Policy ...>...</wsp:Policy>",
                "code": { "All": [{"SetVariable": {...}}] },
                "json": "{ ... }"
            }
        }
    ],
    "services": [
        {
            "goid": "...",
            "name": "My Service",
            "resolutionPath": "/api/v1/resource",
            "enabled": true,
            "folderPath": "/services",
            "policy": { "xml": "..." },
            "properties": { ... }
        }
    ],
    "clusterProperties": [
        {"name": "env.backend.url", "value": "https://backend:8443"}
    ]
}
```

**Policy Content Representations:**

| Field | Type | Parser Action |
|-------|------|---------------|
| `policy.xml` | XML string | Direct parse with `PolicyParser` |
| `policy.code` | JSON object | Convert to XML via `_code_to_xml()`, then parse |
| `policy.json` | Stringified JSON | `json.loads()` → convert to XML, then parse |

### 8.4 Implemented Assertion Extractors (72 types)

Each extractor converts an `L7p:` XML element into a flat configuration dict.

**Authentication & Authorization:**

| Extractor | Assertion Type | Extracted Fields |
|-----------|---------------|-----------------|
| `_extract_http_basic` | HttpBasic | (none - presence-based) |
| `_extract_authentication` | Authentication | identity_provider_oid |
| `_extract_ssl_assertion` | SslAssertion | require_client_auth, key_alias |
| `_extract_lookup_api_key` | LookupApiKey | key_name, location |
| `_extract_cookie_credential` | CookieCredentialSource | cookie_name |
| `_extract_siteminder_authenticate` | SiteMinderAuthenticate | agent_oid, resource, action |
| `_extract_siteminder_check_protected` | SiteMinderCheckProtected | agent_oid, resource |
| `_extract_validate_nonsaml` | ValidateNonSoapSamlToken | (token config) |
| `_extract_create_saml_token` | CreateSamlToken | issuer, audience, name_format |

**JWT:**

| Extractor | Assertion Type | Extracted Fields |
|-----------|---------------|-----------------|
| `_extract_decode_jwt` | DecodeJsonWebToken | source_variable, target_variable, validate_signature, key_id |
| `_extract_encode_jwt` | EncodeJsonWebToken | algorithm, key_id, source_variable, headers |

**Traffic Control:**

| Extractor | Assertion Type | Extracted Fields |
|-----------|---------------|-----------------|
| `_extract_rate_limit` | RateLimit | max_requests_per_second, counter_name |
| `_extract_throughput_quota` | ThroughputQuota | quota, window_size_seconds, counter_name |
| `_extract_request_size_limit` | RequestSizeLimit | max_size_bytes |
| `_extract_ip_range` | RemoteIpRange | ip_ranges, allow_range |
| `_extract_cache_lookup` | CacheLookup | max_entries, max_age, cache_id |
| `_extract_cache_storage` | CacheStorage | max_entries, max_age |

**Routing:**

| Extractor | Assertion Type | Extracted Fields |
|-----------|---------------|-----------------|
| `_extract_http_routing` | HttpRoutingAssertion | protected_service_url, tls_version, connect_timeout, follow_redirects |
| `_extract_jms_routing` | JmsRoutingAssertion | destination_type, endpoint_oid |
| `_extract_mq_native_routing` | MqNativeRouting | queue_name, queue_manager, reply_type |
| `_extract_aws_lambda` | AwsLambda | function_name, region, qualifier |

**Transformation:**

| Extractor | Assertion Type | Extracted Fields |
|-----------|---------------|-----------------|
| `_extract_set_variable` | SetVariable | variable_name, expression |
| `_extract_add_header` | AddHeader | header_name, header_value, remove_existing |
| `_extract_remove_header` | RemoveHeader | header_name |
| `_extract_hardcoded_response_full` | HardcodedResponse | response_status, response_content_type, response_body, response_headers |
| `_extract_customize_error` | CustomizeErrorResponse | content, content_type |
| `_extract_json_transform` | JsonTransformationAssertion | transformation |
| `_extract_json_transformation` | JsonTransformation | transformation, source, target, action |
| `_extract_xsl_transformation` | XslTransformation | xslt_resource |
| `_extract_encode_decode` | EncodeDecode | source_variable, target_variable, transform_type, charset |

**Logic & Flow:**

| Extractor | Assertion Type | Extracted Fields |
|-----------|---------------|-----------------|
| `_extract_comparison` | ComparisonAssertion | comparisons (list) |
| `_extract_regex` | Regex | regex_pattern, target_variable, case_sensitive |
| `_extract_for_each_loop` | ForEachLoop | loop_variable, body_assertion_count |
| `_extract_evaluate_json_path` | EvaluateJsonPathExpression(V2) | expression, source_variable, target_variable |
| `_extract_request_xpath` | RequestXpathAssertion | xpath_expression, namespaces, target_variable |
| `_extract_response_xpath` | ResponseXpathAssertion | (delegates to request xpath) |
| `_extract_split` | Split | variable, split_pattern |
| `_extract_join` | Join/JoinVariable | variable, join_string |
| `_extract_manipulate_multivalued` | ManipulateMultiValuedVariable | action, source_variable, target_variable |
| `_extract_map_value` | MapValue | source_variable, mappings |

**Security:**

| Extractor | Assertion Type | Extracted Fields |
|-----------|---------------|-----------------|
| `_extract_sql_attack_protection` | SqlAttackProtection | protection_targets |
| `_extract_code_injection_protection` | CodeInjectionProtection | protection_targets |
| `_extract_code_injection_protection_v2` | CodeInjectionProtectionAssertion | protection_targets |
| `_extract_lookup_trusted_cert` | LookupTrustedCertificate | trusted_cert_name, lookup_type |
| `_extract_validate_certificate` | ValidateCertificate | validation_type |

**Scripting & Custom:**

| Extractor | Assertion Type | Extracted Fields |
|-----------|---------------|-----------------|
| `_extract_javascript` | JavaScript | script_name, script_body, execution_timeout |
| `_extract_custom_assertion` | CustomAssertion | class_name, module_file_name |

**Data Access:**

| Extractor | Assertion Type | Extracted Fields |
|-----------|---------------|-----------------|
| `_extract_jdbc_query` | JdbcQuery | connection_name, query_string, max_records, schema |
| `_extract_cassandra_query` | CassandraQuery | connection_name, query_string, consistency |

**Utility:**

| Extractor | Assertion Type | Extracted Fields |
|-----------|---------------|-----------------|
| `_extract_uuid_generator` | UUIDGenerator | variable_name |
| `_extract_raise_error` | RaiseError | (error assertion) |
| `_extract_false_assertion` | FalseAssertion | (always-fail) |
| `_extract_true_assertion` | TrueAssertion | (always-pass) |
| `_extract_comment` | CommentAssertion | comment_text |
| `_extract_export_variables` | ExportVariables | variables |
| `_extract_audit_detail` | AuditDetailAssertion | detail_level |
| `_extract_generic` | (fallback) | All child element attributes |

### 8.5 Supported Layer 7 Versions

| Version | Support Level | Export Format |
|---------|--------------|---------------|
| Layer 7 9.x | Full | RESTMAN XML, Policy Manager XML |
| Layer 7 10.x | Full | RESTMAN XML, GMU directory |
| Layer 7 11.x | Full | RESTMAN XML, Graphman JSON |

---

## 9. Kong Generation Specifications

### 9.1 Output Format

Generated configurations use Kong declarative YAML format 3.0:

```yaml
_format_version: '3.0'
services:
- name: my-service
  url: https://backend.example.com
  connect_timeout: 30000
  read_timeout: 60000
  write_timeout: 60000
  retries: 5
  tags:
  - migrated-from-layer7
  - My Service
  routes:
  - name: my-service-route
    paths:
    - /api/v1
    strip_path: true
    protocols:
    - https
    - http
    tags:
    - migrated-from-layer7
  plugins:
  - name: rate-limiting
    config:
      second: 100
      policy: local
      fault_tolerant: true
      hide_client_headers: false
    tags:
    - migrated-from-layer7
    - RateLimit
consumers:
- username: my-service-test-consumer
  custom_id: migration-my-service-001
  tags:
  - placeholder
  - migrated-from-layer7
  - replace-with-real-credentials
  basicauth_credentials:
  - username: test-user
    password: REPLACE-WITH-REAL-PASSWORD
    tags:
    - placeholder
```

### 9.2 Vault Reference Resolution

When vault references are provided, the generator resolves Layer 7 `${variable}` patterns in backend URLs to Kong vault references:

```yaml
# Before (Layer 7 variable reference):
url: ${env.backend.url}/api/v1

# After (Kong vault reference):
url: '{vault://layer7-migrated/ENV_BACKEND_URL}/api/v1'
```

### 9.3 Migration Tags

| Tag | Purpose |
|-----|---------|
| `migrated-from-layer7` | Identifies all migrated resources |
| `{assertion-type}` | Links to source Layer 7 assertion |
| `ai-generated` | Config produced by Claude AI analysis |
| `placeholder` | Credentials/values needing replacement |
| `replace-with-real-credentials` | Consumer credentials needing update |

### 9.4 Validation Requirements

Generated YAML must:
- Parse as valid YAML
- Deploy successfully to Kong Gateway (DB-less mode)
- Pass behavioral tests in Validation Environment
- Reference only valid Kong plugin names
- Not contain actual secrets (redacted or vault-referenced)

---

## 10. Kong Enterprise Plugin Reference

### 10.1 Overview

**Plugin Hub:** https://docs.konghq.com/hub/
**Kong Repository:** https://github.com/Kong/kong (Apache 2.0)
**PDK Reference:** https://developer.konghq.com/gateway/pdk/reference/

### 10.2 Authentication Plugins

| Plugin | Layer 7 Assertion | Enterprise Feature |
|--------|------------------|--------------------|
| basic-auth | HttpBasic | - |
| key-auth | LookupApiKey | - |
| jwt | DecodeJsonWebToken | - |
| jwt-signer | EncodeJsonWebToken | Enterprise - key management |
| openid-connect | RequireSaml (SAML→OIDC) | Enterprise - full OIDC/OAuth2 |
| mtls-auth | SslAssertion (client cert) | Enterprise - mutual TLS |
| ldap-auth | Authentication (LDAP-backed) | - |
| session | CookieCredentialSource | - |

### 10.3 Traffic Control Plugins

| Plugin | Layer 7 Assertion | Enterprise Feature |
|--------|------------------|--------------------|
| rate-limiting | RateLimit (fixed window) | - |
| **rate-limiting-advanced** | DistributedRateLimit, ThroughputQuota | **Enterprise - sliding window, Redis sync** |
| proxy-cache | CacheLookup, CacheStorage | - |
| request-size-limiting | RequestSizeLimit | - |

### 10.4 Transformation Plugins

| Plugin | Layer 7 Assertion |
|--------|------------------|
| request-transformer | AddHeader (request target) |
| response-transformer | AddHeader (response target), CustomizeErrorResponse |
| request-transformer-advanced | JsonTransformationAssertion, JsonTransformation |
| request-termination | HardcodedResponse, EchoRoutingAssertion, RaiseError |
| cors | CorsAssertion |
| jq | JsonPathAssertion, EvaluateJsonPathExpression |
| ip-restriction | RemoteIpRange |
| request-validator | JsonSchemaAssertion, OpenApiValidation, SwaggerAssertion |

### 10.5 Security Plugins

| Plugin | Layer 7 Assertion | Enterprise Feature |
|--------|------------------|--------------------|
| bot-detection | CodeInjectionProtectionAssertion | - |

### 10.6 Logging Plugins

| Plugin | Layer 7 Assertion |
|--------|------------------|
| http-log | AuditDetailAssertion, AuditAssertion |

### 10.7 Serverless Plugins

| Plugin | Layer 7 Assertion |
|--------|------------------|
| pre-function | JavaScript (Lua conversion), SetVariable, Regex, ComparisonAssertion, ExportVariables, UUIDGenerator |
| post-function | JavaScript (response-phase Lua) |
| aws-lambda | AwsLambda |

### 10.8 PDK Key Modules

| Module | Purpose |
|--------|---------|
| `kong.request` | Access request data (headers, body, params) |
| `kong.response` | Modify response (headers, status, body) |
| `kong.service.request` | Modify upstream request |
| `kong.service.response` | Access upstream response |
| `kong.client` | Client info (IP, consumer, credentials) |
| `kong.log` | Debug, info, error logging |
| `kong.vault` | Runtime secret resolution |

---

## 11. Assertion-to-Plugin Mapping Reference

> **Note:** The tables below show the most common types in each tier. For the complete list of all 273 assertion types, see `knowledge/reference/assertion-type-catalog.yaml`.

### 11.1 DIRECT Assertions (35 types - auto-generate)

| Layer 7 Assertion | Kong Plugin | Notes |
|-------------------|-------------|-------|
| HttpBasic | basic-auth | Credential extraction |
| LookupApiKey | key-auth | API Portal key lookup |
| CorsAssertion | cors | Direct mapping - origins, methods, headers |
| RateLimit | rate-limiting | Per-second rate, local policy |
| DistributedRateLimit | rate-limiting-advanced | Cluster-wide, needs EE |
| RequestSizeLimit | request-size-limiting | Convert bytes to MB |
| RemoteIpRange | ip-restriction | IP allow/deny list |
| HardcodedResponse | request-termination | Static response body/status |
| EchoRoutingAssertion | request-termination | Echo response |
| EchoRouting | request-termination | Echo response (variant) |
| AuditDetailAssertion | http-log | Audit logging |
| AuditAssertion | http-log | Audit logging |
| AddHeader | request-transformer | Header add/replace |
| RemoveHeader | request-transformer | Header removal |
| CommentAssertion | _skip | Policy comment (ignored) |
| TrueAssertion | _skip | Always-true (ignored) |
| FalseAssertion | _skip | Always-false (ignored) |
| UUIDGenerator | pre-function | UUID generation via Lua |
| RaiseError | request-termination | Error response |

### 11.2 CONDITIONAL Assertions (109 types - generate with review)

| Layer 7 Assertion | Kong Plugin | Review Flag | Notes |
|-------------------|-------------|-------------|-------|
| Authentication | basic-auth | IDP_CONFIG_REQUIRED | IdP type determines exact plugin |
| SslAssertion | mtls-auth | SECURITY_REVIEW | Client cert → mtls-auth, else TLS config |
| RequireSaml | openid-connect | IDP_CONFIG_REQUIRED | SAML → OIDC migration |
| DecodeJsonWebToken | jwt | KEY_CONFIG_REQUIRED | Algorithm, key source, claims |
| EncodeJsonWebToken | jwt-signer | KEY_CONFIG_REQUIRED | Algorithm, key reference, payload |
| ThroughputQuota | rate-limiting-advanced | TRANSFORM_REVIEW | Window size, limit, counter strategy |
| CacheLookup | proxy-cache | CACHE_STRATEGY | TTL, scope, invalidation |
| CacheStorage | proxy-cache | CACHE_STRATEGY | Cache write config |
| HttpRoutingAssertion | _upstream | ROUTING_DECISION | Backend URL, TLS, timeouts |
| Http2RoutingAssertion | _upstream | ROUTING_DECISION | HTTP/2 routing |
| JsonSchemaAssertion | request-validator | TRANSFORM_REVIEW | Schema content must be migrated |
| OpenApiValidation | request-validator | TRANSFORM_REVIEW | OpenAPI spec validation |
| SwaggerAssertion | request-validator | TRANSFORM_REVIEW | Swagger spec validation |
| CustomizeErrorResponse | response-transformer | TRANSFORM_REVIEW | Error response formatting |
| Regex | pre-function | LUA_MIGRATION_REQUIRED | Regex logic → Lua |
| SetVariable | pre-function | LUA_MIGRATION_REQUIRED | Variable assignment → Lua |
| ComparisonAssertion | pre-function | LUA_MIGRATION_REQUIRED | Conditional logic → Lua |
| Include | _fragment | MANUAL_REVIEW | Policy fragment must be resolved |
| Encapsulated | _encass | MANUAL_REVIEW | Encapsulated assertion must be inlined |
| AwsLambda | aws-lambda | ROUTING_DECISION | Function name, region, IAM |
| JsonTransformationAssertion | request-transformer-advanced | TRANSFORM_REVIEW | Complex JSON transforms |
| JsonPathAssertion | jq | TRANSFORM_REVIEW | JSONPath operations |
| JsonPathAssertionV2 | jq | TRANSFORM_REVIEW | JSONPath V2 operations |
| EvaluateJsonPathExpression | jq | TRANSFORM_REVIEW | JSONPath evaluation |
| EvaluateJsonPathExpressionV2 | jq | TRANSFORM_REVIEW | JSONPath V2 evaluation |
| CookieCredentialSource | session | IDP_CONFIG_REQUIRED | Cookie-based session |
| ExportVariables | pre-function | LUA_MIGRATION_REQUIRED | Variable export → Lua |
| JsonTransformation | request-transformer-advanced | TRANSFORM_REVIEW | JSON transform (variant) |
| LookupTrustedCertificate | mtls-auth | SECURITY_REVIEW | Certificate trust lookup |
| ValidateCertificate | mtls-auth | SECURITY_REVIEW | Certificate validation |
| CodeInjectionProtectionAssertion | bot-detection | SECURITY_REVIEW | Code injection rules |

### 11.3 CUSTOM Assertions (129 types - AI or manual)

**Scripting:**

| Assertion | Recommended Approach |
|-----------|---------------------|
| JavaScript | Convert to Lua for pre-function/post-function |
| XslTransformation | Custom Lua or Kong plugin |
| CustomAssertion | Complete reimplementation (was Java) |

**WS-Security / SOAP:**

| Assertion | Notes |
|-----------|-------|
| WssBasic | WS-Security - no direct Kong equivalent |
| WssDigest | WS-Security digest auth |
| WssSignature | XML digital signature |
| WssKerberos | Kerberos over WS-Security |
| WsSecurity | Generic WS-Security |
| WssEncryptElement | XML encryption |
| WssSignElement | XML signing |
| NonSoapDecryptElement | Non-SOAP XML decryption |

**Identity Federation:**

| Assertion | Notes |
|-----------|-------|
| SiteMinderAuthenticate | CA SSO → OIDC migration strategy |
| SiteMinderAuthorize | CA SSO authorization |
| SiteMinderCheckProtected | CA SSO resource check |
| RadiusAuthenticate | RADIUS auth - custom implementation |
| ValidateNonSoapSamlToken | SAML token validation |
| CreateSamlToken | SAML token generation |

**Protocol Routing (architectural redesign):**

| Assertion | Notes |
|-----------|-------|
| JmsRoutingAssertion | JMS - consider sidecar or event-driven architecture |
| MqNativeRoutingAssertion | MQ Native - consider message bridge pattern |
| MqNativeRouting | MQ Native (variant) |
| FtpRoutingAssertion | FTP - consider file transfer service |
| SshRoutingAssertion | SSH - consider jump host pattern |
| RawTcpRoutingAssertion | Raw TCP - requires custom handling |
| KafkaRoutingAssertion | Kafka - consider Kong's event gateway |

**Data Access:**

| Assertion | Notes |
|-----------|-------|
| JdbcQuery | Move database queries to backend services |
| CassandraQuery | Move to backend services |
| LDAPQuery | Map to ldap-auth or custom plugin |
| LDAPWrite | LDAP write - move to backend |

**Security Threats:**

| Assertion | Notes |
|-----------|-------|
| SqlAttackProtection | Map to Kong WAF or pre-function validation |
| CodeInjectionProtection | Code injection rules → validation |
| CsrfProtection | CSRF - custom implementation |
| DocumentStructureThreat | XML structure validation |
| JsonDocumentStructureThreat | JSON structure validation |
| GraphqlSchemaValidation | GraphQL schema validation |
| SchemaValidation | Generic schema validation |

**XML Operations:**

| Assertion | Notes |
|-----------|-------|
| RequestXpathAssertion | XPath operations - Lua or custom |
| ResponseXpathAssertion | XPath on response |
| XpathCredential | XPath-based credential extraction |
| AddXmlElement | XML modification |
| RemoveXmlElement | XML modification |

**Data Manipulation:**

| Assertion | Notes |
|-----------|-------|
| EncodeDecode | Encoding/decoding transforms |
| Split | Variable splitting |
| JoinVariable / Join | Variable joining |
| ManipulateMultivalued / ManipulateMultiValuedVariable | Multi-valued variable operations |
| MapValue | Value mapping |
| AccumulateData | Data accumulation |

**Miscellaneous:**

| Assertion | Notes |
|-----------|-------|
| ForEachLoop | Loop - Lua implementation |
| TimeRange | Time-based access control |
| KeyValueStore / KeyValueLookup | Key-value operations |
| HttpFormPost | Form POST handling |
| MimeToHttpForm | MIME conversion |

---

## 12. Intermediate Representation Schema

### 12.1 Pydantic IR Models

```python
# src/layer7_kong_migration/models/ir.py

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

class AssertionConfig(BaseModel):
    name: str
    assertion_type: str
    complexity: Complexity = Complexity.CUSTOM
    configuration: dict[str, Any] = {}
    kong_mapping: dict[str, Any] | None = None
    review_flag: ReviewFlag = ReviewFlag.NONE
    review_reason: str = ""
    raw_xml: str = ""
    resource_content: str = ""
    confidence: float = 0.0
    tags: list[str] = []

class FlowStep(BaseModel):
    assertion_name: str
    condition: str = ""
    enabled: bool = True

class Flow(BaseModel):
    name: str = "main"
    logic: str = "all"      # "all" (AND) | "one_or_more" (OR) | "exactly_one" (XOR)
    steps: list[FlowStep] = []
    sub_flows: list[Flow] = []

class Endpoint(BaseModel):
    name: str
    url: str = ""
    protocol: str = "https"
    tls_version: str = ""
    connection_timeout_ms: int = 30000
    read_timeout_ms: int = 60000

class ServiceDefinition(BaseModel):
    name: str
    service_id: str = ""
    folder_path: str = "/"
    resolution_path: str = ""
    enabled: bool = True
    soap: bool = False
    wsdl_url: str = ""
    endpoints: list[Endpoint] = []
    policy_flow: Flow | None = None
    assertions: list[AssertionConfig] = []
    properties: dict[str, str] = {}

class PolicyBundle(BaseModel):
    """Root IR: complete Layer 7 gateway export."""
    name: str
    source_format: str = "restman"
    source_path: str = ""
    gateway_version: str = ""
    services: list[ServiceDefinition] = []
    shared_policies: list[ServiceDefinition] = []
    encapsulated_assertions: list[ServiceDefinition] = []
    cluster_properties: dict[str, str] = {}
    jdbc_connections: list[dict[str, Any]] = []
    stored_passwords: list[str] = []
    certificates: list[dict[str, str]] = []
```

### 12.2 Kong Configuration Models

```python
# src/layer7_kong_migration/models/kong.py

class KongPlugin(BaseModel):
    name: str
    service_name: str = ""
    route_name: str = ""
    config: dict[str, Any] = {}
    enabled: bool = True
    tags: list[str] = []

class KongRoute(BaseModel):
    name: str
    paths: list[str] = []
    methods: list[str] | None = None
    strip_path: bool = True
    protocols: list[str] = ["https", "http"]
    tags: list[str] = []

class KongService(BaseModel):
    name: str
    url: str = ""
    host: str = ""
    port: int = 443
    protocol: str = "https"
    path: str = ""
    connect_timeout: int = 30000
    read_timeout: int = 60000
    write_timeout: int = 60000
    retries: int = 5
    routes: list[KongRoute] = []
    plugins: list[KongPlugin] = []
    tags: list[str] = []

class KongConsumer(BaseModel):
    username: str
    custom_id: str = ""
    tags: list[str] = []
    credentials: dict[str, list[dict[str, Any]]] = {}

class KongUpstream(BaseModel):
    name: str
    targets: list[dict[str, Any]] = []
    healthchecks: dict[str, Any] = {}
    tags: list[str] = []

class KongVault(BaseModel):
    name: str              # Backend type: env, aws, hcv, gcp
    prefix: str            # Vault prefix for references
    config: dict[str, Any] = {}
    description: str = ""
    tags: list[str] = []

class KongCertificate(BaseModel):
    cert: str = ""
    key: str = ""
    cert_alt: str = ""
    key_alt: str = ""
    snis: list[str] = []
    tags: list[str] = []

class KongCACertificate(BaseModel):
    cert: str = ""
    cert_digest: str = ""
    tags: list[str] = []

class KongKey(BaseModel):
    name: str
    kid: str = ""
    set_name: str = ""
    jwk: str = ""
    pem_private_key: str = ""
    pem_public_key: str = ""
    tags: list[str] = []

class KongKeySet(BaseModel):
    name: str
    tags: list[str] = []

class KongConfig(BaseModel):
    """Complete Kong declarative configuration output."""
    format_version: str = "3.0"
    services: list[KongService] = []
    consumers: list[KongConsumer] = []
    upstreams: list[KongUpstream] = []
    plugins: list[KongPlugin] = []
    vaults: list[KongVault] = []
    certificates: list[KongCertificate] = []
    ca_certificates: list[KongCACertificate] = []
    keys: list[KongKey] = []
    key_sets: list[KongKeySet] = []
```

---

## 13. Vault and Secrets Migration

### 13.1 Overview

Layer 7 stores configuration, secrets, and certificates as gateway-wide entities. Kong provides equivalent constructs through its Vaults, Certificates, and Keys entities.

### 13.2 Mapping Strategy

```
┌─────────────────────────────┐       ┌────────────────────────────────┐
│      LAYER 7 GATEWAY        │       │      KONG GATEWAY              │
│                             │       │                                │
│  Cluster Properties ────────┼──────▶│  Kong Vaults                   │
│  (key=value pairs)          │       │  {vault://layer7-migrated/KEY} │
│                             │       │                                │
│  Stored Passwords ──────────┼──────▶│  Kong Vaults (secrets)         │
│  (encrypted secrets)        │       │  {vault://layer7-migrated/KEY} │
│                             │       │                                │
│  Trusted Certificates ──────┼──────▶│  Kong Certificates / CA Certs  │
│  (TLS/mTLS certs)           │       │  + SNI mapping                 │
│                             │       │                                │
│  JWT Keys (in assertions) ──┼──────▶│  Kong Keys / Key Sets          │
│  (signing/validation keys)  │       │  (JWK format)                  │
│                             │       │                                │
│  JDBC Connections ──────────┼──────▶│  Kong Vaults (credentials)     │
│  (URL, user, password)      │       │  + backend service config      │
│                             │       │                                │
└─────────────────────────────┘       └────────────────────────────────┘
```

### 13.3 Vault Reference Format

```
# Pattern:
{vault://layer7-migrated/<ENV_KEY>}

# Examples:
{vault://layer7-migrated/ENV_BACKEND_URL}
{vault://layer7-migrated/SECRET_DB_PASSWORD}
{vault://layer7-migrated/ORDERSDB_JDBC_URL}
```

### 13.4 Environment Variable Convention

All vault-backed values use the prefix `L7_MIGRATED_` with the key name converted to `UPPER_SNAKE_CASE`:

| Layer 7 Name | Env Variable | Vault Reference |
|-------------|-------------|-----------------|
| `env.backend.url` | `L7_MIGRATED_ENV_BACKEND_URL` | `{vault://layer7-migrated/ENV_BACKEND_URL}` |
| `env.api.secret.key` | `L7_MIGRATED_ENV_API_SECRET_KEY` | `{vault://layer7-migrated/ENV_API_SECRET_KEY}` |
| stored password `db-password` | `L7_MIGRATED_SECRET_DB_PASSWORD` | `{vault://layer7-migrated/SECRET_DB_PASSWORD}` |

### 13.5 Secret Detection

Properties with names matching these patterns are automatically redacted in the env template (value set to `REPLACE-WITH-SECRET`):

- `password`, `secret`, `token`
- `api_key`, `api-key`, `apikey`
- `private_key`, `private-key`
- `credential`, `auth`

### 13.6 CLI Usage

```bash
# Default: env vault backend
uv run migrate vaults /path/to/bundle.json -o vault-output/

# AWS Secrets Manager
uv run migrate vaults /path/to/bundle.json -b aws -o vault-output/

# HashiCorp Vault
uv run migrate vaults /path/to/bundle.json -b hcv -o vault-output/

# GCP Secret Manager
uv run migrate vaults /path/to/bundle.json -b gcp -o vault-output/
```

---

## 14. Knowledge Extension Framework

### 14.1 Pattern Contribution Workflow

1. **Encounter** - Consultant encounters CUSTOM assertion during migration
2. **Implement** - Manually create Kong equivalent
3. **Document** - Create YAML pattern file (see format below)
4. **Validate** - Test in Validation Environment
5. **Submit** - Add to `knowledge/patterns/` via PR or direct commit
6. **Activate** - Pattern available for auto-generation

### 14.2 Pattern Format

```yaml
pattern:
  id: "unique-pattern-id"
  name: "Human-readable name"
  description: "What this pattern handles"

  layer7:
    assertion_type: "AssertionTypeName"
    config_keys:
      - "key1"
      - "key2"
    keywords:
      - "keyword1"
      - "keyword2"

  kong:
    plugin: "plugin-name"
    config:
      key: value
    lua_code: null     # Lua code if pre-function needed
    requires_review: false

  metadata:
    contributor: "consultant-id"
    confidence: 0.85
```

### 14.3 Knowledge Patterns (20 files)

The framework ships with 20 migration pattern files covering the most common Layer 7 patterns:

| Pattern ID | Category | Kong Plugin(s) | Confidence |
|------------|----------|----------------|------------|
| `rate-limit-basic` | Traffic Control | rate-limiting | 0.95 |
| `org-rate-quota` | Traffic Control | rate-limiting-advanced | 0.85 |
| `cors-standard` | Security | cors | 0.95 |
| `basic-auth-ldap` | Authentication | ldap-auth | 0.70 |
| `jwt-decode-validate` | Authentication | jwt | 0.75 |
| `jwt-validation-claims` | Authentication | jwt + pre-function | 0.80 |
| `oauth2-token-validation` | Authentication | openid-connect | 0.80 |
| `backend-routing` | Routing | _upstream | 0.85 |
| `json-schema-validation` | Validation | request-validator | 0.85 |
| `xml-schema-validation` | Validation | request-validator | 0.80 |
| `graphql-depth-limiting` | Validation | graphql-rate-limiting-advanced | 0.80 |
| `mtls-certificate-validation` | Security | mtls-auth | 0.85 |
| `threat-protection-layered` | Security | pre-function + xml-threat-protection | 0.80 |
| `log4shell-security-filter` | Security | pre-function | 0.85 |
| `opa-integration` | Authorization | opa | 0.80 |
| `ai-gateway-proxy` | AI Gateway | ai-proxy + ai-rate-limiting | 0.75 |
| `otk-fapi-compliance` | Compliance | openid-connect + mtls-auth | 0.75 |
| `config-cache-scheduled` | Caching | proxy-cache + pre-function | 0.70 |
| `metrics-offboxing` | Observability | prometheus + opentelemetry | 0.75 |
| `custom-assertions-extended` | Custom | pre-function | 0.65 |

### 14.4 AI-Learned Patterns

When the AI analyzer returns a result with confidence ≥85%, the `PatternLearner` automatically extracts it as a reusable YAML pattern file (`knowledge/patterns/ai-{hash}.yaml`). This creates a self-improving knowledge base that reduces API calls over time.

### 14.5 Assertion-to-Plugin Mapping File

The file `knowledge/mappings/assertion-to-plugin.yaml` provides supplemental mappings with notes for each assertion type. This extends the built-in classification in `analysis/classifier.py` and can be customized per customer engagement.

---

## 15. AI Orchestration Layer

### 15.1 Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    AI ANALYSIS PIPELINE                        │
│                                                                │
│  CUSTOM/CONDITIONAL                                            │
│  Assertion                                                     │
│       │                                                        │
│       ▼                                                        │
│  ┌──────────────┐  hit  ┌──────────────┐                       │
│  │   Pattern    │──────▶│   Return     │                       │
│  │   Matcher    │       │   Match      │                       │
│  └──────┬───────┘       └──────────────┘                       │
│         │ miss                                                 │
│         ▼                                                      │
│  ┌──────────────┐  hit  ┌──────────────┐                       │
│  │   Cache      │──────▶│   Return     │                       │
│  │   Check      │       │   Cached     │                       │
│  └──────┬───────┘       └──────────────┘                       │
│         │ miss                                                 │
│         ▼                                                      │
│  ┌──────────────┐       ┌──────────────┐                       │
│  │   Claude API │──────▶│   Cache      │                       │
│  │   Call       │       │   Store      │                       │
│  └──────┬───────┘       └──────┬───────┘                       │
│         │                       │                              │
│         ▼                       ▼                              │
│  ┌──────────────┐       ┌──────────────┐                       │
│  │   Apply      │       │   Pattern    │                       │
│  │   Confidence │       │   Learning   │                       │
│  │   Flags      │       │   (≥85%)     │                       │
│  └──────────────┘       └──────────────┘                       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 15.2 Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ai_model` | `claude-sonnet-4-20250514` | Claude model for analysis |
| `ai_max_tokens` | 2000 | Maximum response tokens |
| `ai_max_resource_chars` | 4000 | Max chars for resource content in prompts |
| `ai_rate_limit_delay_ms` | 500 | Minimum delay between API calls |
| `ai_max_retries` | 3 | Retry count on API errors |
| `ai_confidence_auto_threshold` | 0.85 | Auto-accept threshold |
| `ai_confidence_review_threshold` | 0.60 | Review-required threshold |
| `pattern_learning_threshold` | 0.85 | Min confidence to learn as pattern |

### 15.3 AI Response Schema

```json
{
    "kong_plugin_name": "the-kong-plugin",
    "kong_plugin_config": {
        "key": "value"
    },
    "lua_code": "-- Lua code if pre-function needed, null otherwise",
    "confidence": 0.0,
    "explanation": "Brief explanation of the mapping",
    "review_notes": ["Items requiring human review"],
    "migration_risks": ["Potential behavioral differences"]
}
```

### 15.4 Type-Specific Hints

The AI prompt system includes per-assertion-type guidance via the `TYPE_HINTS` dictionary:

| Assertion Type | Hint Focus |
|---------------|------------|
| Authentication | Identify IdP type, map to appropriate Kong auth plugin |
| SslAssertion | Check if client cert required → mtls-auth |
| RequireSaml | SAML → OIDC conversion, IdP discovery |
| DecodeJsonWebToken | Algorithm, public key, claims |
| EncodeJsonWebToken | Signing algorithm, key reference, payload |
| ThroughputQuota | Window size, limit, counter strategy |
| CacheLookup | TTL, cache key, storage strategy |
| HttpRoutingAssertion | Backend URL, TLS, timeouts, header forwarding |
| JavaScript | Convert JavaScript → Lua for pre-function |
| SetVariable | Variable usage pattern analysis |
| ComparisonAssertion | Conditional logic → expressions or Lua |
| ForEachLoop | Loop pattern → Lua iteration |
| JdbcQuery | Document query, suggest API-based alternative |
| CustomAssertion | Document interface and behavior for reimplementation |

### 15.5 Cache Strategy

- **Key:** MD5 hash of `{assertion_type}|{configuration_json}|{resource_content}`
- **Storage:** Individual YAML files in `.cache/ai/`
- **Eviction:** Manual via `AICache.clear()`
- **Purpose:** Avoid duplicate API calls across bundles with identical assertion patterns

---

## 16. Implementation Status

### 16.1 Current Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Assertion Types Classified | >100 | **273** (35D + 109C + 129X) |
| Registered Extractors | >50 | **72** |
| Plugin Generators | >10 | **23** |
| Knowledge Patterns | 20 | **20** |
| Unit Tests | >50 | **58 passing** |
| OTK Automation Rate | >80% | **83%** |
| Simple Bundle Rate | >90% | **100%** |
| Complex Bundle Rate | >70% | **75%** |
| Vault Backends | 4 | **4** (env, aws, hcv, gcp) |
| Ingestion Formats | 6 | **6** (RESTMAN item/bundle, export, standalone, Graphman imploded/exploded) |

### 16.2 Planned Phases

#### Phase 10: Multi-Agent Parallel Execution
- Async orchestrator module
- Worker pool with configurable concurrency (default 5 workers)
- Rate limit coordination across workers
- `migrate batch-generate --ai <corpus_path>` CLI command
- Rich progress bar with worker status
- Target: >50 services/hour

#### Phase 11: Behavioral Tests
- Docker-based behavioral tests matching Apigee framework's approach
- Test key-auth, rate-limiting, CORS, basic-auth, JWT plugins
- Pipeline end-to-end tests
- Target: >50 behavioral tests

#### Phase 12: Release Kit
- Package for partner/customer distribution
- Customer-facing deployment guide
- Kong PS engagement runbook
- Demo script for leadership presentations

---

## 17. Appendices

### 17.1 Glossary

| Term | Definition |
|------|------------|
| Assertion | A Layer 7 policy step - equivalent to an Apigee policy or Kong plugin |
| Complexity Classification | DIRECT, CONDITIONAL, or CUSTOM rating for migration difficulty |
| Confidence Score | Percentage indicating pattern match or AI analysis reliability |
| Cluster Property | Gateway-wide key-value configuration in Layer 7 |
| decK | Kong declarative configuration tool (`deck validate`, `deck sync`) |
| Encapsulated Assertion | Reusable assertion component in Layer 7 (like a shared flow) |
| Graphman | Modern JSON management API for Layer 7 11.x |
| Intermediate Representation (IR) | Normalized Pydantic models for cross-module communication |
| Knowledge Reference Library | Central repository of mappings, patterns, and examples |
| Mock API Service | Node.js echo service for validating Kong plugin behavior |
| OTK | OAuth Token Kit - Broadcom's 130-policy OAuth/OIDC customization suite |
| PDK | Plugin Development Kit - Kong's Lua API for plugin development |
| Pattern Matching | Weighted similarity scoring against learned assertion patterns |
| RESTMAN | Layer 7 RESTful Management API for exporting bundles |
| Review Flag | Marker indicating human review required in generated config |
| Validation Environment | Docker-based Kong 3.14 + Node mock API for runtime testing |
| Vault Reference | Kong secret resolution syntax: `{vault://prefix/key}` |

### 17.2 Quick Reference Commands

```bash
# Installation
uv sync

# Core CLI
uv run migrate analyze samples/simple-auth-service/service-bundle.xml
uv run migrate generate samples/simple-auth-service/service-bundle.xml -o kong.yaml
uv run migrate generate samples/complex-routing-service/service-bundle.xml --ai -o kong.yaml
uv run migrate vaults samples/real-policies/otk/otk-customizations-single.json -o vault-output/

# Graphman bundles
uv run migrate analyze samples/real-policies/otk/otk-customizations-single.json
uv run migrate vaults samples/real-policies/otk/otk-customizations-single.json -b aws -o vault-output/

# Reports
uv run migrate report samples/simple-auth-service/service-bundle.xml -o report.html
uv run migrate talking-points samples/simple-auth-service/service-bundle.xml -o points.md

# Pattern commands
uv run migrate pattern list
uv run migrate pattern search "rate limit"

# Testing
uv run pytest tests/ -v                   # 58 unit tests

# Validation environment
bin/validation-up.sh                       # Start Kong 3.14 + Node mock API
bin/validation-reload.sh kong.yaml         # Reload config
bin/validation-down.sh                     # Stop environment
```

### 17.3 Kong Enterprise Resources

| Resource | URL |
|----------|-----|
| Plugin Hub | https://docs.konghq.com/hub/ |
| rate-limiting-advanced | https://docs.konghq.com/hub/kong-inc/rate-limiting-advanced/ |
| jwt-signer | https://docs.konghq.com/hub/kong-inc/jwt-signer/ |
| openid-connect | https://docs.konghq.com/hub/kong-inc/openid-connect/ |
| Kong Vaults | https://docs.konghq.com/gateway/latest/kong-enterprise/secrets-management/ |
| Kong Keys | https://docs.konghq.com/gateway/latest/admin-api/#keys-object |
| PDK Documentation | https://developer.konghq.com/gateway/pdk/reference/ |
| Kong OSS Repository | https://github.com/Kong/kong |

### 17.4 Test Coverage Reference

| Module | Test File | Tests | Coverage |
|--------|-----------|-------|----------|
| XML Parser | `test_parser.py` | 8 | Standalone, RESTMAN, config, raw XML, endpoints |
| Classifier | `test_classifier.py` | 15 | Direct, conditional, custom, skip, parametrized matrix |
| Extractors | `test_extractors.py` | 6 | Rate limit, CORS, HTTP routing, set variable, JS, generic |
| Generator | `test_generator.py` | 6 | YAML output, services, routes, plugins, consumers, tags |
| Graphman | `test_graphman.py` | 11 | Imploded, exploded, code-to-XML, cluster props, policy types |
| Vaults | `test_vaults.py` | 12 | Cluster props, secrets, JDBC, certs, env manifest, backends |

### 17.5 Layer 7 Assertion Type Reference (Complete)

The framework recognizes **273 assertion types** across 3 classification tiers (35 DIRECT, 109 CONDITIONAL, 129 CUSTOM), covering the complete Graphman v11.2.1 schema catalog of 247 types plus 26 XML tag name aliases and extended types derived from Layer 7 reference implementations and custom assertion SDK.

Known assertion types discovered in the OTK bundle not yet explicitly classified (handled as CUSTOM):
- `IdentityAttributes` - Identity context attributes (note: `CertificateAttributes` now classified as CONDITIONAL → mtls-auth)
- `XpathCredentialSource` - XPath-based credential extraction
- `assertionComment` - Policy comment (lowercase variant)

---

*End of Document*
