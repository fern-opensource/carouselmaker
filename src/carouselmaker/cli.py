"""CarouselMaker CLI – markdown to branded LinkedIn carousel PDFs."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import click

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """CarouselMaker – markdown to branded LinkedIn carousel PDFs."""


@cli.command()
def health():
    """Test connections to Anthropic and optionally Figma."""
    import anthropic

    from carouselmaker.config import get_settings

    settings = get_settings()
    errors = []

    # Test Anthropic
    if not settings.anthropic_api_key:
        click.echo("Anthropic: SKIPPED (no ANTHROPIC_API_KEY)")
    else:
        try:
            ac = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            response = ac.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            click.echo(f"Anthropic: OK ({response.model})")
        except Exception as e:
            click.echo(f"Anthropic: FAILED – {e}")
            errors.append("anthropic")

    # Test Figma token
    if settings.figma_access_token:
        import httpx

        try:
            resp = httpx.get(
                "https://api.figma.com/v1/me",
                headers={"X-Figma-Token": settings.figma_access_token},
                timeout=10,
            )
            resp.raise_for_status()
            user = resp.json()
            click.echo(f"Figma: OK ({user.get('email', 'connected')})")
        except Exception as e:
            click.echo(f"Figma: FAILED – {e}")
            errors.append("figma")
    else:
        click.echo("Figma: SKIPPED (no FIGMA_ACCESS_TOKEN)")

    # Test brand file
    try:
        from carouselmaker.brand import load_brand

        brand = load_brand(settings.brand_file)
        click.echo(f"Brand: OK ({brand['name']} — {brand['font_heading']}/{brand['font_body']})")
    except Exception as e:
        click.echo(f"Brand: FAILED – {e}")
        errors.append("brand")

    if errors:
        raise SystemExit(1)


@cli.command()
@click.argument("markdown_file", type=click.Path(exists=True))
@click.option("--title", default="", help="Override the carousel title")
@click.option("--series", default="", help="Series name (e.g. 'Agentic Taxonomy')")
@click.option("--brand", "brand_file", default="", help="Path to brand JSON (default: brand.json)")
@click.option("--output-dir", default="", help="Output directory (default: output)")
def generate(markdown_file: str, title: str, series: str, brand_file: str, output_dir: str):
    """Generate a carousel from a markdown file."""
    from carouselmaker.config import get_settings_with_overrides
    from carouselmaker.graph_carousel.graph import run_carousel

    overrides = {}
    if brand_file:
        overrides["brand_file"] = brand_file
    if output_dir:
        overrides["output_dir"] = output_dir

    settings = get_settings_with_overrides(**overrides)

    markdown = Path(markdown_file).read_text()
    click.echo(f"Reading {markdown_file} ({len(markdown)} chars)")
    click.echo(f"Brand: {settings.brand_file}")

    result = run_carousel(
        markdown,
        title_hint=title,
        series_name=series,
        settings=settings,
    )

    spec = result.get("carousel_spec", {})
    if spec:
        click.echo(f"\nCarousel: {spec.get('title', 'untitled')}")
        click.echo(f"Slides: {len(spec.get('slides', []))}")
        for slide in spec.get("slides", []):
            click.echo(f"  [{slide['slide_number']}] {slide['slide_type']}: {slide['heading']}")

    if result.get("pdf_path"):
        click.echo(f"\nOutput: {result['pdf_path']}")

    if result.get("error"):
        click.echo(f"\nNote: {result['error']}")


@cli.command()
@click.argument("markdown_file", type=click.Path(exists=True))
@click.option("--title", default="", help="Override the carousel title")
@click.option("--series", default="", help="Series name")
def extract_only(markdown_file: str, title: str, series: str):
    """Extract carousel spec from markdown without generating Figma frames."""
    from carouselmaker.graph_carousel.nodes.extract import extract_node

    markdown = Path(markdown_file).read_text()
    click.echo(f"Extracting from {markdown_file} ({len(markdown)} chars)")

    result = extract_node({
        "markdown": markdown,
        "title_hint": title,
        "series_name": series,
    })

    if result.get("error"):
        click.echo(f"Error: {result['error']}")
        raise SystemExit(1)

    spec = result["carousel_spec"]
    click.echo(json.dumps(spec, indent=2))


if __name__ == "__main__":
    cli()
