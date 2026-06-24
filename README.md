# Broadcom Layer 7 to Kong Gateway Migration Framework

> Automated migration toolkit for converting Broadcom Layer 7 API Gateway (CA API Gateway) configurations to Kong Gateway Enterprise declarative YAML — powered by Claude AI.

**Status:** Active Development | **Version:** 0.1.0 | **Python:** 3.12+

---

## What This Delivers

Point this toolkit at a customer's Layer 7 gateway export and get a **migration plan + working Kong configuration in minutes instead of weeks**.

The framework takes Layer 7 exports (RESTMAN XML, Graphman JSON, GMU directories, standalone policies, ZIP archives) and produces:

- **Production-ready Kong Gateway 3.14 declarative YAML** — services, routes, plugins, consumers, upstreams — auto-generated from Layer 7 policies
- **Vault-mapped secrets** — cluster properties, stored passwords, JDBC credentials, and certificates mapped to Kong vault references (env, AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager)
- **Structured gap analysis** — every assertion that can't auto-migrate gets a specific review flag explaining what's needed (IdP migration, Lua conversion, architectural redesign, or custom plugin)
- **HTML migration report + customer-facing talking points** — ready for internal review or customer delivery
- **20 migration pattern files** — ready-made knowledge for auth, OPA, AI Gateway, FAPI, threat protection, rate limiting, mTLS, GraphQL, and more
- **47 Graphman entity type mappings** — services, policies, IdPs, secrets, scheduled tasks, etc. mapped to their Kong equivalents

### Automation Coverage

| Scenario | Automation Rate |
|----------|----------------|
| Simple services (auth + routing + rate limit) | **100%** — fully auto-generated Kong YAML |
| OTK OAuth/OIDC bundles (130 policies, 1596 assertions) | **83%** — most assertions auto-classified |
| Complex services (transforms, WS-Security, multi-protocol) | **50-70%** — DIRECT + CONDITIONAL auto-generated, CUSTOM flagged with guidance |

### How the Three Tiers Work

| Tier | Count | What Happens | Example |
|------|-------|-------------|---------|
| **DIRECT** | 35 | Auto-generates Kong plugin config. Zero review needed. | `RateLimit` → `rate-limiting` plugin YAML |
| **CONDITIONAL** | 109 | Generates config with review flags. Human verifies settings. | `SiteMinderAuthenticate` → `openid-connect` + "IdP migration required" |
| **CUSTOM** | 129 | Flagged for AI analysis or manual work. Specific guidance provided. | `JavaScript` → "Lua conversion needed" with pre-function scaffold |

A Kong SE runs the tool, reviews the flagged items, and delivers a complete migration package.

---

## Why This Exists

Enterprises running Broadcom Layer 7 (CA API Gateway) face a complex migration path to Kong. Policies are deeply nested XML with 273 assertion types spanning authentication, traffic control, transformation, routing, and protocol bridging. Manual migration is slow, error-prone, and expensive.

This framework automates 75-85% of that work by parsing Layer 7 exports, classifying every assertion by migration complexity, and generating production-ready Kong Gateway 3.14 declarative YAML — leveraging Enterprise plugins like `xml-threat-protection`, `kafka-upstream`, `opa`, and `exit-transformer` for broader coverage, with AI-assisted analysis for the hard cases.

## Key Results

| Metric | Value |
|--------|-------|
| Assertion types recognized | **273** (35 auto-generate, 109 with review, 129 AI/manual) |
| Assertion-specific extractors | **72** |
| OTK bundle automation rate | **83%** (130 real OAuth/OIDC policies, 1596 assertions) |
| Simple service automation | **100%** |
| Unit tests | **58 passing** |
| Vault backends supported | **4** (env, AWS, HashiCorp, GCP) |

## How It Works

```
                          ┌─────────────┐
                          │  Layer 7    │
                          │  Export     │
                          │  (XML/JSON) │
                          └──────┬──────┘
                                 │
                    ┌────────────▼────────────┐
                    │      INGESTION          │
                    │  RESTMAN · Graphman     │
                    │  GMU · Standalone XML   │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────▼──────────────────┐
              │          CLASSIFICATION              │
              │                                      │
              │  DIRECT (35)      → auto-generate     │
              │  CONDITIONAL (109) → generate + review │
              │  CUSTOM (129)     → AI analysis       │
              └──────────┬───────────────┬───────────┘
                         │               │
              ┌──────────▼───┐   ┌───────▼──────────┐
              │   Pattern    │   │   Claude AI       │
              │   Matcher    │   │   Analyzer        │
              │              │   │   (cache+learn)   │
              └──────────┬───┘   └───────┬───────────┘
                         │               │
                    ┌────▼───────────────▼────┐
                    │      GENERATION         │
                    │  Kong YAML 3.0          │
                    │  Vault configs          │
                    │  Certificates & Keys    │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────▼──────────────────┐
              │           REPORTING                  │
              │  HTML Report · Talking Points        │
              │  Vault Reference Map · Env Template  │
              └─────────────────────────────────────┘
```

### Three-Tier Classification

Every Layer 7 assertion is classified into one of three tiers:

- **DIRECT** — 1:1 Kong plugin mapping. Auto-generated with full confidence. Examples: `HttpBasic` → `basic-auth`, `RateLimit` → `rate-limiting`, `CorsAssertion` → `cors`.
- **CONDITIONAL** — Known Kong plugin target, but configuration requires review. Includes Kong 3.14 Enterprise plugins: `DocumentStructureThreat` → `xml-threat-protection`, `KafkaRoutingAssertion` → `kafka-upstream`, `SiteMinderAuthenticate` → `openid-connect`, `SiteMinderAuthorize` → `opa`.
- **CUSTOM** — No direct Kong equivalent. Analyzed by Claude AI or flagged for manual implementation. Examples: `JavaScript` (→ Lua conversion), `JmsRoutingAssertion` (→ architectural redesign), `WssSignature` (→ custom plugin).

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- (Optional) Anthropic API key for AI-assisted analysis

### Install

```bash
git clone git@github.com:Kong-Grajesh-SE/Broadcom-Layer7-Migration-to-Kong.git
cd Broadcom-Layer7-Migration-to-Kong
uv sync
```

### Configure AI (optional)

```bash
cp config/.secrets.toml.example config/.secrets.toml
# Edit config/.secrets.toml and add your ANTHROPIC_API_KEY
```

### Run

```bash
# Analyze a Layer 7 bundle — see classification breakdown
uv run migrate analyze samples/simple-auth-service/service-bundle.xml

# Generate Kong declarative YAML
uv run migrate generate samples/simple-auth-service/service-bundle.xml -o kong.yaml

# Generate with AI analysis for CUSTOM assertions
uv run migrate generate samples/complex-routing-service/service-bundle.xml --ai -o kong.yaml

# Map secrets, cluster properties, and certs to Kong vaults
uv run migrate vaults samples/real-policies/otk/otk-customizations-single.json -b env -o vault-output/

# Generate HTML migration report
uv run migrate report samples/simple-auth-service/service-bundle.xml -o report.html

# Generate customer-facing talking points
uv run migrate talking-points samples/simple-auth-service/service-bundle.xml -o points.md

# List available migration patterns
uv run migrate pattern list
```

## Supported Input Formats

| Format | File Type | Layer 7 Version |
|--------|-----------|-----------------|
| RESTMAN Item/Bundle | `.xml` | 9.x, 10.x, 11.x |
| Policy Manager Export | `.xml` | 9.x, 10.x |
| GMU Directory Export | directory | 10.x |
| Graphman JSON (imploded) | `.json` | 11.x |
| Graphman JSON (exploded) | directory of `.policy.json` | 11.x |
| ZIP Archive | `.zip` | Any |

## Project Structure

```
├── src/layer7_kong_migration/
│   ├── cli.py                  # 7 CLI commands (analyze, generate, report, vaults, ...)
│   ├── ingestion/              # XML/JSON parsing, 72 assertion extractors
│   ├── analysis/               # Three-tier classification (273 assertion types)
│   ├── generation/             # Kong YAML generator, 23 plugin generators, vault mapper
│   ├── ai/                     # Claude API integration, caching, pattern learning
│   ├── patterns/               # Weighted similarity matcher + YAML pattern library
│   ├── reporting/              # HTML report + Markdown talking points
│   └── models/                 # Pydantic IR (PolicyBundle) + Kong output models
├── knowledge/
│   ├── mappings/               # Assertion-to-plugin YAML mappings
│   ├── patterns/               # 20 migration pattern files (auth, routing, security, AI gateway...)
│   └── reference/              # Full assertion catalog (273 types) + Graphman entity types (47)
├── samples/                    # Test bundles (synthetic + real OTK policies)
├── tests/                      # 58 unit tests
├── validation/                 # Docker-based Kong 3.14 validation environment
├── config/                     # Settings + secrets (gitignored)
└── doc/                        # Specification document
```

## Vault and Secrets Migration

Layer 7 gateway-wide entities map to Kong native constructs:

| Layer 7 Entity | Kong Entity |
|----------------|-------------|
| Cluster Properties | Kong Vaults (`{vault://layer7-migrated/KEY}`) |
| Stored Passwords | Kong Vault secrets |
| Certificates | Kong Certificates / CA Certificates |
| JWT Keys | Kong Keys / Key Sets |
| JDBC Connection credentials | Kong Vault secrets |

Supports four vault backends: `env` (default), `aws` (AWS Secrets Manager), `hcv` (HashiCorp Vault), `gcp` (GCP Secret Manager).

```bash
uv run migrate vaults bundle.json -b aws -o vault-output/
# Produces: kong-vaults.yaml, vault.env.template, vault-reference-map.txt
```

## Validation Environment

Spin up a local Kong 3.14 instance to test generated configs:

```bash
bin/validation-up.sh                   # Start Kong + mock API
bin/validation-reload.sh kong.yaml     # Load generated config
bin/validation-down.sh                 # Tear down
```

## Testing

```bash
uv run pytest tests/ -v                # All 58 unit tests
```

| Test Suite | Tests | Coverage |
|------------|-------|----------|
| XML Parser | 8 | RESTMAN, standalone, config extraction |
| Classifier | 15 | All three tiers, parametrized matrix |
| Extractors | 6 | Rate limit, CORS, routing, JS, generic |
| Generator | 6 | Services, routes, plugins, consumers |
| Graphman | 11 | Imploded, exploded, code-to-XML |
| Vaults | 12 | Cluster props, secrets, JDBC, certs |

## Extension Points

| Task | Where to Change |
|------|-----------------|
| Add assertion mapping | `analysis/classifier.py` + `generation/plugins.py` |
| Add new extractor | `ingestion/extractors.py` |
| Add migration pattern | `knowledge/patterns/<id>.yaml` |
| Add plugin generator | `generation/plugins.py` |
| Tune AI prompts | `ai/prompts.py` |
| Add vault backend | `generation/vaults.py` |
| Add CLI command | `cli.py` |

## Documentation

- [Technical Specification (v1.0)](doc/Layer7_Kong_Migration_Framework_Specification_v1.0.md) — comprehensive architecture, parsing specs, mapping tables, and implementation status
- [CLAUDE.md](CLAUDE.md) — Claude Code context file for AI-assisted development

## License

MIT — See [LICENSE](LICENSE).
