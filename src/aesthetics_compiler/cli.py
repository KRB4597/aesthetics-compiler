from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from aesthetics_compiler import __version__
from aesthetics_compiler.tiers import ALL_PROJECTIONS, InputMode

app = typer.Typer(help="aesthetics-compiler — aesthetic IR with pluggable projection analysers")
console = Console()


@app.command()
def compile(
    source: str = typer.Argument(..., help="Input file (text, image, HTML, video) or inline text"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Write IR JSON to this path"),
    projection: Optional[str] = typer.Option(
        None, "--projection", "-p",
        help=f"Comma-separated projection IDs (default: all). Valid: {','.join(ALL_PROJECTIONS)}",
    ),
    input_mode: Optional[str] = typer.Option(
        None, "--input-mode", "-m",
        help="Force input mode: text, image, html, multimedia (default: auto-detect)",
    ),
    extractor: str = typer.Option(
        "rule", "--extractor", "-e",
        help="Text extractor tier: rule (default) or nlp (spaCy; needs the [nlp] extra)",
    ),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Override document title"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
) -> None:
    """Compile an aesthetic source into an AestheticIR."""
    from aesthetics_compiler.pipeline.orchestrator import compile_document

    projection_list = [p.strip() for p in projection.split(",")] if projection else None
    mode = InputMode(input_mode) if input_mode else None

    try:
        ir = compile_document(
            source,
            input_mode=mode,
            projections=projection_list,
            title=title,
            quiet=quiet,
            extractor=extractor,
        )
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if out:
        out.write_text(ir.model_dump_json(indent=2), encoding="utf-8")
        if not quiet:
            console.print(f"[green]IR written to {out}[/green]")

    if not quiet:
        _print_summary(ir)


@app.command()
def report(
    ir_file: Path = typer.Argument(..., help="Path to .ir.json file"),
) -> None:
    """Print a human-readable report from a saved IR file."""
    if not ir_file.exists():
        console.print(f"[red]File not found: {ir_file}[/red]")
        raise typer.Exit(1)
    from aesthetics_compiler.ir.schemas import AestheticIR
    ir = AestheticIR.model_validate_json(ir_file.read_text(encoding="utf-8"))
    _print_summary(ir)


@app.command()
def validate(
    ir_file: Path = typer.Argument(..., help="Path to .ir.json file to validate"),
) -> None:
    """Validate an IR file against the schema."""
    try:
        from aesthetics_compiler.ir.schemas import AestheticIR
        ir = AestheticIR.model_validate_json(ir_file.read_text(encoding="utf-8"))
        console.print(f"[green]Valid[/green] — schema_version={ir.schema_version}, "
                      f"graph_hash={ir.audit.graph_hash or 'none'}")
    except Exception as e:
        console.print(f"[red]Invalid:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="export-schema-org")
def export_schema_org_cmd(
    ir_file: Path = typer.Argument(..., help="Path to .ir.json"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Output .jsonld file"),
) -> None:
    """Export IR as Schema.org/VisualArtwork JSON-LD."""
    from aesthetics_compiler.ir.schemas import AestheticIR
    from aesthetics_compiler.export.schema_org import export_schema_org
    ir = AestheticIR.model_validate_json(ir_file.read_text(encoding="utf-8"))
    jsonld = export_schema_org(ir, out)
    if not out:
        console.print(jsonld)
    else:
        console.print(f"[green]JSON-LD written to {out}[/green]")


@app.command()
def version() -> None:
    """Print compiler version."""
    console.print(f"aesthetics-compiler v{__version__}")


def _print_summary(ir) -> None:
    console.rule(f"[bold]{ir.document.title}[/bold]")
    console.print(
        f"  input_mode=[cyan]{ir.document.input_mode}[/cyan]  "
        f"medium=[cyan]{ir.document.medium or 'unknown'}[/cyan]  "
        f"artist=[cyan]{ir.document.artist or 'unknown'}[/cyan]  "
        f"period=[cyan]{ir.document.style_period or 'unknown'}[/cyan]"
    )

    vec = ir.aggregate_aesthetic_vector
    t = Table(title="Aesthetic Vector", show_header=True, header_style="bold magenta")
    t.add_column("Dimension", style="cyan")
    t.add_column("Value", justify="right")
    t.add_column("Direction")
    t.add_column("Explanation")
    from aesthetics_compiler.ir.schemas import AESTHETIC_DIMENSIONS
    for dim in AESTHETIC_DIMENSIONS:
        ds = getattr(vec, dim)
        color = "green" if ds.direction == "dominant" else "yellow" if ds.direction == "present" else "white"
        t.add_row(
            dim,
            f"{ds.value:.3f}",
            f"[{color}]{ds.direction}[/{color}]",
            (ds.explanation or "")[:60],
        )
    console.print(t)

    if ir.projections:
        pt = Table(title="Projection Results", show_header=True, header_style="bold blue")
        pt.add_column("Projection", style="cyan")
        pt.add_column("Verdict")
        pt.add_column("Polarity")
        pt.add_column("Score", justify="right")
        for pid, pr in ir.projections.items():
            pol_color = "green" if pr.polarity == "harmonious" else "red" if pr.polarity == "discordant" else "yellow"
            pt.add_row(pid, pr.verdict, f"[{pol_color}]{pr.polarity}[/{pol_color}]", f"{pr.score:.3f}")
        console.print(pt)

    verdict = ir.aesthetic_verdict
    v_color = "green" if "harmonious" in verdict.verdict else "red" if "discordant" in verdict.verdict else "yellow"
    console.print(
        f"\n  Verdict: [{v_color}]{verdict.verdict}[/{v_color}] "
        f"(confidence={verdict.confidence:.2f}, dominant={verdict.dominant_projection or 'n/a'})"
    )
    if ir.cross_projection_disagreement:
        console.print("[yellow]  ⚠ Cross-projection disagreement detected — see ir.cross_projection_disagreement[/yellow]")
    console.print(f"\n  graph_hash={ir.audit.graph_hash or 'none'}")
    console.print(f"  schema_version={ir.schema_version}")


if __name__ == "__main__":
    app()
