"""Self-contained HTML report generator.

Produces a single HTML file with inline CSS - no external dependencies.
Includes executive summary, classification breakdown, assertion details,
Kong config preview, and recommendations.
"""

from typing import Any

from layer7_kong_migration.models.ir import Complexity, PolicyBundle


class HTMLReportGenerator:
    def generate(self, bundle: PolicyBundle, kong_yaml: str = "", ai_enabled: bool = False) -> str:
        metrics = bundle.metrics
        assertions = bundle.all_assertions
        return self._render(bundle.name, metrics, assertions, kong_yaml, ai_enabled)

    def generate_portfolio(self, bundles: list[PolicyBundle]) -> str:
        sections = []
        for b in bundles:
            sections.append(self.generate(b))
        return "\n<hr>\n".join(sections)

    def _render(
        self,
        name: str,
        metrics: dict[str, Any],
        assertions: list,
        kong_yaml: str,
        ai_enabled: bool,
    ) -> str:
        total = metrics.get("total", 0)
        direct = metrics.get("direct", 0)
        conditional = metrics.get("conditional", 0)
        custom = metrics.get("custom", 0)
        auto_rate = metrics.get("automation_rate", 0)

        rows = ""
        for a in assertions:
            badge_class = {
                Complexity.DIRECT: "badge-direct",
                Complexity.CONDITIONAL: "badge-conditional",
                Complexity.CUSTOM: "badge-custom",
            }.get(a.complexity, "badge-custom")

            kong_plugin = ""
            if a.kong_mapping:
                kong_plugin = a.kong_mapping.get("kong_plugin_name", "")
            confidence = f"{a.confidence:.0%}" if a.confidence > 0 else "-"

            rows += f"""<tr>
                <td>{a.assertion_type}</td>
                <td><span class="badge {badge_class}">{a.complexity.value}</span></td>
                <td>{kong_plugin}</td>
                <td>{confidence}</td>
                <td>{a.review_flag.value if a.review_flag.value != 'none' else '-'}</td>
                <td class="review-reason">{a.review_reason or '-'}</td>
            </tr>"""

        kong_preview = f"<pre><code>{_escape(kong_yaml)}</code></pre>" if kong_yaml else "<p>No Kong config generated (run with --generate)</p>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Layer 7 → Kong Migration Report: {_escape(name)}</title>
<style>
:root {{ --primary: #003459; --success: #10B981; --warning: #F59E0B; --danger: #EF4444; --bg: #F8FAFC; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: #1E293B; padding: 2rem; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
h1 {{ color: var(--primary); margin-bottom: 0.5rem; }}
.subtitle {{ color: #64748B; margin-bottom: 2rem; }}
.metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
.metric-card {{ background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
.metric-value {{ font-size: 2.5rem; font-weight: bold; }}
.metric-label {{ color: #64748B; font-size: 0.875rem; margin-top: 0.25rem; }}
.gauge {{ width: 120px; height: 120px; margin: 0 auto 0.5rem; position: relative; }}
.gauge-circle {{ fill: none; stroke-width: 8; stroke-linecap: round; }}
.gauge-bg {{ stroke: #E2E8F0; }}
.gauge-fill {{ stroke: var(--success); transition: stroke-dashoffset 1s; }}
table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem; }}
th {{ background: var(--primary); color: white; padding: 0.75rem 1rem; text-align: left; font-weight: 600; }}
td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #E2E8F0; }}
tr:hover {{ background: #F1F5F9; }}
.badge {{ padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
.badge-direct {{ background: #D1FAE5; color: #065F46; }}
.badge-conditional {{ background: #FEF3C7; color: #92400E; }}
.badge-custom {{ background: #FEE2E2; color: #991B1B; }}
.review-reason {{ font-size: 0.8rem; color: #64748B; max-width: 300px; }}
section {{ margin-bottom: 2rem; }}
section h2 {{ color: var(--primary); margin-bottom: 1rem; }}
pre {{ background: #1E293B; color: #E2E8F0; padding: 1.5rem; border-radius: 8px; overflow-x: auto; font-size: 0.85rem; }}
.ai-badge {{ background: #EDE9FE; color: #5B21B6; padding: 0.125rem 0.5rem; border-radius: 3px; font-size: 0.7rem; }}
</style>
</head>
<body>
<div class="container">
<h1>Layer 7 → Kong Migration Report</h1>
<p class="subtitle">{_escape(name)} {'(AI-enhanced)' if ai_enabled else ''}</p>

<div class="metrics">
    <div class="metric-card">
        <div class="metric-value">{total}</div>
        <div class="metric-label">Total Assertions</div>
    </div>
    <div class="metric-card">
        <div class="metric-value" style="color: var(--success)">{direct}</div>
        <div class="metric-label">Direct (Auto-Generate)</div>
    </div>
    <div class="metric-card">
        <div class="metric-value" style="color: var(--warning)">{conditional}</div>
        <div class="metric-label">Conditional (Review)</div>
    </div>
    <div class="metric-card">
        <div class="metric-value" style="color: var(--danger)">{custom}</div>
        <div class="metric-label">Custom (AI/Manual)</div>
    </div>
    <div class="metric-card">
        <div class="metric-value" style="color: var(--success)">{auto_rate:.0%}</div>
        <div class="metric-label">Automation Rate</div>
    </div>
</div>

<section>
<h2>Assertion Details</h2>
<table>
<thead>
<tr><th>Assertion Type</th><th>Complexity</th><th>Kong Plugin</th><th>Confidence</th><th>Review Flag</th><th>Notes</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</section>

<section>
<h2>Generated Kong Configuration</h2>
{kong_preview}
</section>

<section>
<h2>Recommendations</h2>
<ul>
<li>Review all <strong>CONDITIONAL</strong> mappings - these have correct plugin targets but need configuration validation</li>
<li>{'AI analysis was used for CUSTOM assertions - review AI-generated configurations carefully' if ai_enabled else 'Run with <code>--ai</code> flag to get AI-powered analysis of CUSTOM assertions'}</li>
<li>Replace all <code>placeholder</code> tagged credentials with real values before deployment</li>
<li>Test generated configuration in a staging environment before production deployment</li>
<li>For SOAP services, consider API modernization as part of the migration</li>
</ul>
</section>

</div>
</body>
</html>"""


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
