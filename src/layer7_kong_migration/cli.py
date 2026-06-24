"""CLI entry point for the Layer 7 → Kong migration tool.

Usage:
    uv run migrate analyze /path/to/bundle.xml
    uv run migrate generate /path/to/bundle.xml -o kong.yaml
    uv run migrate generate /path/to/bundle.xml --ai -o kong.yaml
    uv run migrate report /path/to/bundle.xml --ai -o report.html
    uv run migrate talking-points /path/to/bundle.xml -o points.md
    uv run migrate pattern list
    uv run migrate pattern search "rate limit"
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="migrate", help="Broadcom Layer 7 → Kong Gateway migration tool")
pattern_app = typer.Typer(name="pattern", help="Manage migration patterns")
app.add_typer(pattern_app)
console = Console()


@app.command()
def analyze(
    bundle_path: str = typer.Argument(..., help="Path to Layer 7 bundle (XML, ZIP, or directory)"),
) -> None:
    """Analyze a Layer 7 bundle and classify assertions."""
    from layer7_kong_migration.analysis import AssertionClassifier
    from layer7_kong_migration.ingestion import BundleLoader

    with console.status("Loading bundle..."):
        bundle = BundleLoader(bundle_path).load()

    with console.status("Classifying assertions..."):
        classifier = AssertionClassifier()
        bundle = classifier.classify_bundle(bundle)

    metrics = bundle.metrics
    console.print(f"\n[bold]Bundle: {bundle.name}[/bold]")
    console.print(f"Services: {len(bundle.services)}")
    console.print(f"Total assertions: {metrics['total']}")

    table = Table(title="Classification Summary")
    table.add_column("Complexity", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Rate", justify="right")
    table.add_row("DIRECT", str(metrics["direct"]), f"{metrics.get('direct_rate', 0):.0%}")
    table.add_row("CONDITIONAL", str(metrics["conditional"]), f"{metrics.get('conditional_rate', 0):.0%}")
    table.add_row("CUSTOM", str(metrics["custom"]), f"{metrics.get('custom_rate', 0):.0%}")
    console.print(table)

    console.print(f"\n[green]Automation rate: {metrics.get('automation_rate', 0):.0%}[/green]")

    detail_table = Table(title="Assertion Details")
    detail_table.add_column("Type")
    detail_table.add_column("Complexity")
    detail_table.add_column("Review Flag")
    detail_table.add_column("Reason")

    for a in bundle.all_assertions:
        style = {"direct": "green", "conditional": "yellow", "custom": "red"}.get(a.complexity.value, "")
        detail_table.add_row(
            a.assertion_type,
            f"[{style}]{a.complexity.value}[/{style}]",
            a.review_flag.value if a.review_flag.value != "none" else "-",
            a.review_reason[:60] or "-",
        )
    console.print(detail_table)


@app.command()
def generate(
    bundle_path: str = typer.Argument(..., help="Path to Layer 7 bundle"),
    output: str = typer.Option("kong.yaml", "-o", "--output", help="Output file path"),
    ai: bool = typer.Option(False, "--ai", help="Enable AI analysis for CUSTOM assertions"),
    ai_conditional: bool = typer.Option(False, "--ai-conditional", help="Also AI-analyze CONDITIONAL assertions"),
) -> None:
    """Generate Kong declarative YAML from a Layer 7 bundle."""
    from layer7_kong_migration.analysis import AssertionClassifier
    from layer7_kong_migration.generation import KongGenerator
    from layer7_kong_migration.ingestion import BundleLoader

    with console.status("Loading bundle..."):
        bundle = BundleLoader(bundle_path).load()

    with console.status("Classifying assertions..."):
        classifier = AssertionClassifier()
        bundle = classifier.classify_bundle(bundle)

    if ai:
        with console.status("Running AI analysis..."):
            from layer7_kong_migration.ai import AIAnalyzer
            analyzer = AIAnalyzer()
            bundle = analyzer.analyze_bundle(bundle, include_conditional=ai_conditional)
            console.print(f"AI stats: {analyzer.stats}")

    with console.status("Generating Kong config..."):
        generator = KongGenerator()
        kong_yaml = generator.generate(bundle)

    Path(output).write_text(kong_yaml, encoding="utf-8")
    console.print(f"\n[green]Kong config written to {output}[/green]")
    console.print(f"Automation rate: {bundle.metrics.get('automation_rate', 0):.0%}")


@app.command()
def report(
    bundle_path: str = typer.Argument(..., help="Path to Layer 7 bundle"),
    output: str = typer.Option("report.html", "-o", "--output", help="Output HTML file"),
    ai: bool = typer.Option(False, "--ai", help="Enable AI analysis"),
) -> None:
    """Generate an HTML migration report."""
    from layer7_kong_migration.analysis import AssertionClassifier
    from layer7_kong_migration.generation import KongGenerator
    from layer7_kong_migration.ingestion import BundleLoader
    from layer7_kong_migration.reporting import HTMLReportGenerator

    with console.status("Loading and analyzing..."):
        bundle = BundleLoader(bundle_path).load()
        classifier = AssertionClassifier()
        bundle = classifier.classify_bundle(bundle)

    if ai:
        with console.status("Running AI analysis..."):
            from layer7_kong_migration.ai import AIAnalyzer
            analyzer = AIAnalyzer()
            bundle = analyzer.analyze_bundle(bundle)

    with console.status("Generating..."):
        generator = KongGenerator()
        kong_yaml = generator.generate(bundle)
        report_html = HTMLReportGenerator().generate(bundle, kong_yaml, ai_enabled=ai)

    Path(output).write_text(report_html, encoding="utf-8")
    console.print(f"[green]Report written to {output}[/green]")


@app.command()
def talking_points(
    bundle_path: str = typer.Argument(..., help="Path to Layer 7 bundle"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output markdown file"),
) -> None:
    """Generate customer-facing talking points."""
    from layer7_kong_migration.analysis import AssertionClassifier
    from layer7_kong_migration.ingestion import BundleLoader
    from layer7_kong_migration.reporting import TalkingPointsGenerator

    bundle = BundleLoader(bundle_path).load()
    bundle = AssertionClassifier().classify_bundle(bundle)
    md = TalkingPointsGenerator().generate(bundle)

    if output:
        Path(output).write_text(md, encoding="utf-8")
        console.print(f"[green]Talking points written to {output}[/green]")
    else:
        console.print(md)


@app.command()
def vaults(
    bundle_path: str = typer.Argument(..., help="Path to Layer 7 bundle"),
    output_dir: str = typer.Option("vault-output", "-o", "--output-dir", help="Output directory"),
    backend: str = typer.Option("env", "-b", "--backend", help="Vault backend: env, aws, hcv, gcp"),
) -> None:
    """Map Layer 7 secrets, cluster properties, and certificates to Kong vaults."""
    from layer7_kong_migration.generation.vaults import (
        VaultMapper,
        generate_env_manifest,
        generate_vault_reference_map,
        generate_vault_yaml,
    )
    from layer7_kong_migration.ingestion import BundleLoader

    with console.status("Loading bundle..."):
        bundle = BundleLoader(bundle_path).load()

    with console.status(f"Mapping to Kong vaults (backend={backend})..."):
        mapper = VaultMapper(vault_backend=backend)
        result = mapper.map_bundle(bundle)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    vault_yaml = generate_vault_yaml(result)
    (out / "kong-vaults.yaml").write_text(vault_yaml, encoding="utf-8")

    env_file = generate_env_manifest(result)
    (out / "vault.env.template").write_text(env_file, encoding="utf-8")

    ref_map = generate_vault_reference_map(result)
    (out / "vault-reference-map.txt").write_text(ref_map, encoding="utf-8")

    table = Table(title="Vault Migration Summary")
    table.add_column("Category", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("Vault backends", str(len(result["vaults"])))
    table.add_row("Cluster properties", str(len([r for r in result["vault_references"] if not r.startswith(("stored_password:", "jdbc:"))])))
    table.add_row("Stored passwords", str(len([r for r in result["vault_references"] if r.startswith("stored_password:")])))
    table.add_row("JDBC connections", str(len([r for r in result["vault_references"] if r.startswith("jdbc:")])))
    table.add_row("Certificates", str(len(result["certificates"])))
    table.add_row("CA certificates", str(len(result["ca_certificates"])))
    table.add_row("Key sets", str(len(result["key_sets"])))
    table.add_row("Keys", str(len(result["keys"])))
    console.print(table)

    env_secrets = sum(1 for v in result.get("env_manifest", {}).values() if v == "REPLACE-WITH-SECRET")
    if env_secrets:
        console.print(f"\n[yellow]⚠ {env_secrets} secret(s) need manual replacement in vault.env.template[/yellow]")

    console.print(f"\n[green]Vault config written to {out}/[/green]")
    console.print(f"  kong-vaults.yaml        - Kong declarative vault/cert/key config")
    console.print(f"  vault.env.template      - Environment variables template")
    console.print(f"  vault-reference-map.txt - Layer 7 name → Kong vault reference")


@pattern_app.command("list")
def pattern_list() -> None:
    """List all known migration patterns."""
    from layer7_kong_migration.patterns import PatternLibrary

    library = PatternLibrary()
    table = Table(title=f"Migration Patterns ({library.count()} total)")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Assertion Type")
    table.add_column("Kong Plugin")
    table.add_column("Confidence")

    for p in library.list_all():
        table.add_row(
            p.get("id", ""),
            p.get("name", ""),
            p.get("layer7", {}).get("assertion_type", ""),
            p.get("kong", {}).get("plugin", ""),
            f"{p.get('metadata', {}).get('confidence', 0):.0%}",
        )
    console.print(table)


@pattern_app.command("search")
def pattern_search(query: str = typer.Argument(..., help="Search query")) -> None:
    """Search patterns by keyword."""
    from layer7_kong_migration.patterns import PatternLibrary

    results = PatternLibrary().search(query)
    if not results:
        console.print(f"No patterns found for '{query}'")
        return

    for p in results:
        console.print(f"[bold]{p.get('id')}[/bold]: {p.get('name')} → {p.get('kong', {}).get('plugin')}")


if __name__ == "__main__":
    app()
