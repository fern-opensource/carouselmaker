"""Carousel generation pipeline state."""

from __future__ import annotations

from typing import TypedDict


class CarouselState(TypedDict):
    # Input
    markdown: str  # Raw markdown content from user
    title_hint: str  # Optional title override
    series_name: str  # e.g. "Agentic Taxonomy"

    # Extract output
    carousel_spec: dict  # Serialized CarouselSpec

    # Figma output
    figma_frame_ids: list[str]  # Node IDs of generated frames
    figma_file_url: str  # URL to the Figma file

    # Export output
    pdf_path: str  # Local path to exported PDF

    # Control
    error: str
