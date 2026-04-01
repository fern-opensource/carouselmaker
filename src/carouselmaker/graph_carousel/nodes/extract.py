"""Extract node – parse markdown into structured CarouselSpec."""

from __future__ import annotations

import json
import logging
import re

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from carouselmaker.config import get_settings
from carouselmaker.graph_carousel.state import CarouselState
from carouselmaker.models import CarouselSpec

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """\
You are a content designer creating LinkedIn carousel specifications.

Given markdown content, extract a structured carousel specification.
The carousel will be a multi-page PDF (1080x1080px per slide).

Rules:
- First slide: COVER with title, subtitle, and a numbered list of topics
- Middle slides: CONTENT with heading, subheading, role description, \
  and decision path (when to use it)
- Optionally include a SUMMARY slide for synthesis/conclusion
- Last slide: CTA with closing thought + brand tagline
- Keep text concise — each slide must be readable at mobile size
- Suggest an icon_hint for each content slide (e.g. "shield", "brain", \
  "workflow", "zap", "git-branch", "cpu", "bar-chart", "activity")

Return ONLY valid JSON (no comments, no markdown fences) matching this schema:
{
  "title": "string",
  "subtitle": "string",
  "series_name": "string",
  "tagline": "string",
  "slides": [
    {
      "slide_number": 1,
      "slide_type": "cover|content|summary|cta",
      "heading": "string",
      "subheading": "string",
      "body": "string",
      "bullet_points": ["string"],
      "footnote": "string",
      "icon_hint": "string"
    }
  ]
}"""


def _extract_json(text: str) -> str:
    """Extract JSON from Claude's response, handling common formatting issues."""
    # Strip markdown fences if present
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)

    # Find the outermost JSON object
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")

    # Walk forward to find matching closing brace
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    raise ValueError("Unclosed JSON object in response")


def extract_node(state: CarouselState) -> dict:
    """Parse markdown into a structured CarouselSpec."""
    settings = get_settings()

    if not settings.anthropic_api_key:
        return {"error": "ANTHROPIC_API_KEY not set", "carousel_spec": {}}

    model = ChatAnthropic(
        model=settings.extraction_model,
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
        temperature=0,
    )

    user_content = state["markdown"]
    if state.get("title_hint"):
        user_content = f"Suggested title: {state['title_hint']}\n\n{user_content}"
    if state.get("series_name"):
        user_content = f"Series: {state['series_name']}\n\n{user_content}"

    messages = [
        SystemMessage(content=EXTRACT_PROMPT),
        HumanMessage(content=user_content),
    ]

    logger.info("Extracting carousel spec from markdown (%d chars)", len(state["markdown"]))
    response = model.invoke(messages)
    raw = response.content

    # Parse JSON from response
    try:
        json_str = _extract_json(raw)
        spec_data = json.loads(json_str)
    except (ValueError, json.JSONDecodeError) as e:
        logger.error("Failed to parse JSON from Claude response: %s", e)
        logger.debug("Raw response: %s", raw[:500])
        return {"error": f"JSON parsing failed: {e}", "carousel_spec": {}}

    # Validate against Pydantic model
    try:
        spec = CarouselSpec(**spec_data)
    except ValidationError as e:
        logger.error("Carousel spec validation failed: %s", e)
        return {"error": f"Validation failed: {e}", "carousel_spec": {}}

    logger.info("Extracted carousel: '%s' with %d slides", spec.title, spec.slide_count)
    return {"carousel_spec": spec.model_dump(mode="json"), "error": ""}
