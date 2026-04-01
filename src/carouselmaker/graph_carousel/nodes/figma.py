"""Figma node – generate carousel frame instructions.

Produces a structured instruction set describing each slide's layout,
typography, and content. When run inside Claude Code with Figma MCP,
Claude uses these instructions to build frames on the canvas.

In standalone mode, writes the instructions to a JSON file.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from carouselmaker.brand import load_brand
from carouselmaker.config import get_settings
from carouselmaker.graph_carousel.state import CarouselState
from carouselmaker.models import CarouselSlide, CarouselSpec, SlideType

logger = logging.getLogger(__name__)


def _build_cover_instruction(spec: CarouselSpec, brand: dict) -> dict:
    """Build instruction for the cover slide."""
    cover = next((s for s in spec.slides if s.slide_type == SlideType.COVER), None)
    if not cover:
        return {}

    pad = brand["padding"]
    w = brand["slide_w"]
    h = brand["slide_h"]

    return {
        "slide_type": "cover",
        "slide_number": 1,
        "frame": {
            "width": w,
            "height": h,
            "fill": brand["bg_light"],
            "corner_radius": 0,
        },
        "elements": [
            {
                "type": "text",
                "content": cover.heading,
                "font": brand["font_heading"],
                "size": 72,
                "weight": "Bold",
                "color": brand["text_dark"],
                "x": pad,
                "y": 100,
                "max_width": w - 2 * pad,
            },
            {
                "type": "text",
                "content": cover.subheading,
                "font": brand["font_heading"],
                "size": 56,
                "weight": "Regular",
                "style": "italic",
                "color": brand["text_dark"],
                "x": pad,
                "y": 240,
                "max_width": w - 2 * pad,
            },
            {
                "type": "numbered_list",
                "items": cover.bullet_points,
                "font": brand["font_body"],
                "size": 28,
                "color": brand["text_dark"],
                "badge_color": brand["bg_dark"],
                "x": pad,
                "y": 380,
                "spacing": 64,
            },
            {
                "type": "text",
                "content": spec.tagline or brand["tagline"],
                "font": brand["font_body"],
                "size": 22,
                "color": brand["text_dark"],
                "x": pad,
                "y": h - 140,
            },
            {
                "type": "text",
                "content": brand["name"],
                "font": brand["font_heading"],
                "size": 28,
                "weight": "Bold",
                "color": brand["text_dark"],
                "x": pad,
                "y": h - 100,
            },
        ],
    }


def _build_content_instruction(slide: CarouselSlide, spec: CarouselSpec, brand: dict) -> dict:
    """Build instruction for a content slide."""
    pad = brand["padding"]
    w = brand["slide_w"]
    h = brand["slide_h"]

    return {
        "slide_type": "content",
        "slide_number": slide.slide_number,
        "frame": {
            "width": w,
            "height": h,
            "fill": brand["bg_dark"],
            "corner_radius": brand["corner_radius"],
        },
        "elements": [
            {
                "type": "icon",
                "hint": slide.icon_hint,
                "color": brand["text_light"],
                "x": pad,
                "y": 60,
                "size": 64,
            },
            {
                "type": "badge",
                "content": f"{slide.slide_number:02d}",
                "font": brand["font_heading"],
                "size": 48,
                "color": brand["text_muted"],
                "x": w - pad - 60,
                "y": 60,
                "bg_color": brand["accent"],
            },
            {
                "type": "text",
                "content": slide.heading,
                "font": brand["font_body"],
                "size": 48,
                "weight": "Bold",
                "color": brand["text_light"],
                "x": pad,
                "y": 180,
                "max_width": w - 2 * pad,
            },
            {
                "type": "text",
                "content": slide.subheading,
                "font": brand["font_body"],
                "size": 24,
                "color": brand["text_light"],
                "x": pad,
                "y": 260,
            },
            {
                "type": "section_label",
                "content": "ROLE",
                "font": brand["font_body"],
                "size": 16,
                "weight": "SemiBold",
                "color": brand["text_muted"],
                "x": pad,
                "y": 340,
            },
            {
                "type": "text",
                "content": slide.body,
                "font": brand["font_body"],
                "size": 22,
                "color": brand["text_light"],
                "x": pad,
                "y": 370,
                "max_width": w - 2 * pad,
                "line_height": 1.5,
            },
            {
                "type": "section_label",
                "content": "DECISION PATH",
                "font": brand["font_body"],
                "size": 16,
                "weight": "SemiBold",
                "color": brand["text_muted"],
                "x": pad,
                "y": 520,
            },
            {
                "type": "text",
                "content": "\n".join(slide.bullet_points) if slide.bullet_points else "",
                "font": brand["font_body"],
                "size": 22,
                "color": brand["text_light"],
                "x": pad,
                "y": 550,
                "max_width": w - 2 * pad,
                "line_height": 1.5,
            },
            {
                "type": "text",
                "content": spec.series_name,
                "font": brand["font_heading"],
                "size": 18,
                "style": "italic",
                "color": brand["text_light"],
                "x": pad,
                "y": h - 110,
            },
            {
                "type": "text",
                "content": brand["name"],
                "font": brand["font_heading"],
                "size": 22,
                "weight": "Bold",
                "color": brand["text_light"],
                "x": w - pad - 180,
                "y": h - 80,
            },
        ],
    }


def _build_summary_instruction(slide: CarouselSlide, spec: CarouselSpec, brand: dict) -> dict:
    """Build instruction for a summary slide."""
    pad = brand["padding"]
    w = brand["slide_w"]
    h = brand["slide_h"]

    return {
        "slide_type": "summary",
        "slide_number": slide.slide_number,
        "frame": {
            "width": w,
            "height": h,
            "fill": brand["bg_dark"],
            "corner_radius": brand["corner_radius"],
        },
        "elements": [
            {
                "type": "text",
                "content": slide.heading,
                "font": brand["font_heading"],
                "size": 56,
                "weight": "Bold",
                "color": brand["text_light"],
                "x": pad,
                "y": 80,
                "max_width": w - 2 * pad,
            },
            {
                "type": "text",
                "content": slide.subheading,
                "font": brand["font_body"],
                "size": 24,
                "color": brand["text_light"],
                "x": pad,
                "y": 220,
            },
            {
                "type": "card_list",
                "items": slide.bullet_points,
                "font": brand["font_body"],
                "size": 20,
                "color": brand["text_light"],
                "card_bg": brand["accent"],
                "x": pad,
                "y": 300,
                "card_padding": 24,
                "spacing": 20,
                "max_width": w - 2 * pad,
            },
            {
                "type": "text",
                "content": slide.footnote,
                "font": brand["font_body"],
                "size": 16,
                "style": "italic",
                "color": brand["text_muted"],
                "x": pad,
                "y": h - 160,
                "max_width": w - 2 * pad,
            },
            {
                "type": "text",
                "content": spec.series_name,
                "font": brand["font_heading"],
                "size": 18,
                "style": "italic",
                "color": brand["text_light"],
                "x": pad,
                "y": h - 80,
            },
        ],
    }


def build_figma_instructions(spec: CarouselSpec, brand: dict) -> list[dict]:
    """Build the full set of frame instructions for a carousel."""
    instructions = []

    for slide in spec.slides:
        if slide.slide_type == SlideType.COVER:
            inst = _build_cover_instruction(spec, brand)
        elif slide.slide_type == SlideType.CONTENT:
            inst = _build_content_instruction(slide, spec, brand)
        elif slide.slide_type == SlideType.SUMMARY:
            inst = _build_summary_instruction(slide, spec, brand)
        elif slide.slide_type == SlideType.CTA:
            inst = _build_cover_instruction(spec, brand)
            inst["slide_type"] = "cta"
            inst["slide_number"] = slide.slide_number
        else:
            continue

        if inst:
            instructions.append(inst)

    return instructions


def figma_node(state: CarouselState) -> dict:
    """Generate frame instructions and write to output.

    The instructions JSON describes each slide's layout, content, and styling.
    In Claude Code with Figma MCP, Claude uses these to build canvas frames.
    In standalone mode, the JSON can be applied manually or via a Figma plugin.

    Note: This node does NOT create Figma frames directly. Frame creation
    requires the Figma Plugin API, which is only accessible via MCP.
    """
    if not state.get("carousel_spec"):
        return {"error": "No carousel spec to render"}

    settings = get_settings()
    spec = CarouselSpec(**state["carousel_spec"])
    brand = load_brand(settings.brand_file)
    instructions = build_figma_instructions(spec, brand)

    output_dir = Path(settings.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    instructions_path = output_dir / f"{spec.id}_figma_instructions.json"
    with open(instructions_path, "w") as f:
        json.dump(
            {
                "carousel_id": str(spec.id),
                "title": spec.title,
                "brand": brand,
                "slides": instructions,
            },
            f,
            indent=2,
        )

    logger.info(
        "Generated %d frame instructions → %s",
        len(instructions),
        instructions_path,
    )

    return {
        "figma_frame_ids": [],  # Populated by Claude Code via MCP, not by this node
        "figma_file_url": "",
        "error": "",
    }
