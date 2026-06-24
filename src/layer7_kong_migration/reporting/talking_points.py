"""Customer-facing talking points generator."""

from layer7_kong_migration.models.ir import Complexity, PolicyBundle


class TalkingPointsGenerator:
    def generate(self, bundle: PolicyBundle) -> str:
        metrics = bundle.metrics
        total = metrics["total"]
        if total == 0:
            return "# Migration Assessment\n\nNo assertions found in the bundle.\n"

        direct = metrics["direct"]
        conditional = metrics["conditional"]
        custom = metrics["custom"]
        auto_rate = metrics["automation_rate"]

        direct_types = set()
        conditional_types = set()
        custom_types = set()
        for a in bundle.all_assertions:
            if a.complexity == Complexity.DIRECT:
                direct_types.add(a.assertion_type)
            elif a.complexity == Complexity.CONDITIONAL:
                conditional_types.add(a.assertion_type)
            else:
                custom_types.add(a.assertion_type)

        soap_count = sum(1 for s in bundle.services if s.soap)

        return f"""# Layer 7 → Kong Migration Assessment: {bundle.name}

## Executive Summary

- **{total} policy assertions** analyzed across {len(bundle.services)} services
- **{auto_rate:.0%} automation rate** - {direct + conditional} of {total} assertions have direct or guided Kong mappings
- **{direct} assertions** can be auto-migrated with high confidence (DIRECT)
- **{conditional} assertions** have known mappings but need configuration review (CONDITIONAL)
- **{custom} assertions** require AI analysis or custom implementation (CUSTOM)

## Quick Wins (DIRECT - Auto-Generate)

These {direct} assertions map directly to Kong plugins with no manual intervention:

{chr(10).join(f'- {t}' for t in sorted(direct_types)) or '- (none)'}

## Needs Review (CONDITIONAL)

These {conditional} assertions have correct plugin targets but need config validation:

{chr(10).join(f'- {t}' for t in sorted(conditional_types)) or '- (none)'}

## Requires Analysis (CUSTOM)

These {custom} assertions need AI-powered analysis or custom plugin development:

{chr(10).join(f'- {t}' for t in sorted(custom_types)) or '- (none)'}

{"## SOAP Services" + chr(10) + chr(10) + f"**{soap_count} SOAP services** detected. Consider API modernization (SOAP→REST) as part of the migration." if soap_count > 0 else ""}

## Timeline Estimate

| Phase | Duration | Description |
|-------|----------|-------------|
| Assessment | 1-2 days | Validate auto-generated config, review CONDITIONAL mappings |
| DIRECT migration | 1-2 days | Deploy auto-generated Kong config, test with placeholder creds |
| CONDITIONAL tuning | 3-5 days | Configure IdP, caching, routing decisions |
| CUSTOM development | 1-3 weeks | AI-assisted Lua development, custom plugins |
| Validation | 1 week | End-to-end testing, performance benchmarking |

## Key Talking Points

1. **High automation rate**: {auto_rate:.0%} of policies have direct or guided Kong equivalents
2. **Kong's plugin ecosystem** covers the majority of Layer 7's built-in assertion capabilities
3. **AI-powered migration** accelerates CUSTOM assertion conversion with pattern learning
4. **Progressive migration**: start with DIRECT mappings, iterate on CONDITIONAL/CUSTOM
5. **Modern architecture**: move from XML-policy-driven gateway to declarative Kong configuration
"""
