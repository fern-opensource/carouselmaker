"""Carousel generation pipeline.

LangGraph StateGraph:
  extract → figma → export
"""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from carouselmaker.config import Settings, get_settings
from carouselmaker.graph_carousel.nodes.export import export_node
from carouselmaker.graph_carousel.nodes.extract import extract_node
from carouselmaker.graph_carousel.nodes.figma import figma_node
from carouselmaker.graph_carousel.state import CarouselState

logger = logging.getLogger(__name__)


def build_graph():
    """Build and compile the carousel generation graph."""
    graph = StateGraph(CarouselState)

    graph.add_node("extract", extract_node)
    graph.add_node("figma", figma_node)
    graph.add_node("export", export_node)

    graph.add_edge(START, "extract")
    graph.add_edge("extract", "figma")
    graph.add_edge("figma", "export")
    graph.add_edge("export", END)

    return graph.compile()


app = build_graph()


def run_carousel(
    markdown: str,
    title_hint: str = "",
    series_name: str = "",
    settings: Settings | None = None,
) -> CarouselState:
    """Run the carousel generation pipeline.

    Args:
        markdown: The source content.
        title_hint: Optional title override.
        series_name: Optional series name.
        settings: Optional settings override (for CLI --brand etc).

    Returns:
        Final pipeline state with carousel_spec, instructions, and pdf_path.
    """
    initial_state: CarouselState = {
        "markdown": markdown,
        "title_hint": title_hint,
        "series_name": series_name,
        "carousel_spec": {},
        "figma_frame_ids": [],
        "figma_file_url": "",
        "pdf_path": "",
        "error": "",
    }

    logger.info("Running carousel pipeline (%d chars of markdown)", len(markdown))
    result = app.invoke(initial_state)

    spec = result.get("carousel_spec", {})
    logger.info(
        "Pipeline complete: '%s' — %d slides, output: %s",
        spec.get("title", "untitled"),
        len(spec.get("slides", [])),
        result.get("pdf_path", "none"),
    )
    return result
