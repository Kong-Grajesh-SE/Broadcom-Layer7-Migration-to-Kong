# Layer 7 → Kong Migration Framework

## Project Overview

This is a migration framework that converts Broadcom Layer 7 API Gateway (CA API Gateway) policies to Kong Gateway declarative configurations. It uses a five-stage pipeline: ingestion → classification → AI analysis → generation → reporting.

## Architecture

```
src/layer7_kong_migration/
├── ingestion/     # XML bundle parsing (RESTMAN, GMU, policy export)
├── analysis/      # Three-tier classification (DIRECT/CONDITIONAL/CUSTOM)
├── ai/            # Claude API integration with caching + pattern learning
├── generation/    # Kong declarative YAML output
├── patterns/      # Pattern library matching
├── reporting/     # HTML reports + talking points
├── models/        # Pydantic IR + Kong output models
└── cli.py         # Typer CLI entry point
```

## Key Concepts

- **PolicyBundle**: Root IR containing services, policies, assertions
- **AssertionConfig**: Single Layer 7 assertion with classification and Kong mapping
- **Three-tier classification**: DIRECT (auto-generate), CONDITIONAL (review), CUSTOM (AI/manual)
- **Pattern learning**: High-confidence AI results become reusable YAML patterns

## Commands

```bash
uv run migrate analyze <bundle>            # Classify assertions
uv run migrate generate <bundle> -o out.yaml  # Generate Kong config
uv run migrate generate <bundle> --ai -o out.yaml  # With AI analysis
uv run migrate report <bundle> -o report.html  # HTML report
uv run migrate talking-points <bundle>     # Customer talking points
uv run migrate pattern list                # List patterns
```

## Testing

```bash
uv run pytest tests/                       # All tests
uv run pytest tests/unit/                  # Unit tests only
```

## Validation

```bash
bin/validation-up.sh                       # Start Kong + mock API
bin/validation-reload.sh kong.yaml         # Reload config
bin/validation-down.sh                     # Tear down
```

## Extension Points

| Task | Files to Touch |
|------|----------------|
| New assertion mapping | `analysis/classifier.py`, `generation/plugins.py`, `knowledge/mappings/` |
| New pattern | `knowledge/patterns/<id>.yaml` |
| New plugin generator | `generation/plugins.py` |
| Change AI prompts | `ai/prompts.py` |
| New CLI command | `cli.py` |
| New extractor | `ingestion/extractors.py` |

## Dependencies

- Python 3.12+, managed with `uv`
- lxml + defusedxml for XML parsing
- anthropic SDK for Claude AI
- ruamel.yaml for YAML output
- typer + rich for CLI
