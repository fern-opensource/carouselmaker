"""Export node – download rendered frames as PDF from Figma REST API."""

from __future__ import annotations

import io
import logging
from pathlib import Path

import httpx
from pypdf import PdfReader, PdfWriter

from carouselmaker.config import get_settings
from carouselmaker.graph_carousel.state import CarouselState
from carouselmaker.models import CarouselSpec

logger = logging.getLogger(__name__)

FIGMA_API_TIMEOUT = 30
FIGMA_DOWNLOAD_TIMEOUT = 60


def export_node(state: CarouselState) -> dict:
    """Export Figma frames to a multi-page PDF via the Figma REST API.

    Requires figma_frame_ids to be populated (by Claude Code via MCP).
    Falls back to reporting the instructions JSON path if no frame IDs exist.
    """
    settings = get_settings()
    spec = CarouselSpec(**state["carousel_spec"]) if state.get("carousel_spec") else None

    if not state.get("figma_frame_ids"):
        logger.info("No Figma frame IDs — skipping PDF export.")
        output_dir = Path(settings.output_dir)
        if spec:
            instructions_path = output_dir / f"{spec.id}_figma_instructions.json"
            return {
                "pdf_path": str(instructions_path),
                "error": (
                    "No frame IDs. Run in Claude Code with Figma MCP to generate "
                    "frames, or provide frame IDs manually."
                ),
            }
        return {"pdf_path": "", "error": "No frame IDs and no spec"}

    if not settings.figma_access_token:
        return {"pdf_path": "", "error": "FIGMA_ACCESS_TOKEN required for PDF export"}

    if not settings.figma_output_file_key:
        return {"pdf_path": "", "error": "FIGMA_OUTPUT_FILE_KEY required for PDF export"}

    headers = {"X-Figma-Token": settings.figma_access_token}
    frame_ids = state["figma_frame_ids"]
    writer = PdfWriter()
    failed = []

    for fid in frame_ids:
        try:
            resp = httpx.get(
                f"https://api.figma.com/v1/images/{settings.figma_output_file_key}",
                params={"ids": fid, "format": "pdf", "scale": 1},
                headers=headers,
                timeout=FIGMA_API_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()

            images = data.get("images") or {}
            image_url = images.get(fid)
            if not image_url:
                logger.warning("No image URL for frame %s", fid)
                failed.append(fid)
                continue

            pdf_resp = httpx.get(image_url, timeout=FIGMA_DOWNLOAD_TIMEOUT)
            pdf_resp.raise_for_status()

            # Validate it's actually PDF content
            if not pdf_resp.content[:5].startswith(b"%PDF"):
                logger.warning("Frame %s returned non-PDF content", fid)
                failed.append(fid)
                continue

            reader = PdfReader(io.BytesIO(pdf_resp.content))
            for page in reader.pages:
                writer.add_page(page)

            logger.info("Exported frame %s (%d bytes)", fid, len(pdf_resp.content))

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("Figma API rate limited on frame %s", fid)
            else:
                logger.error("Figma API error for frame %s: %s", fid, e)
            failed.append(fid)
        except httpx.HTTPError as e:
            logger.error("HTTP error exporting frame %s: %s", fid, e)
            failed.append(fid)

    if not writer.pages:
        return {"pdf_path": "", "error": f"All frame exports failed: {failed}"}

    output_dir = Path(settings.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_filename = f"{spec.id}_carousel.pdf" if spec else "carousel.pdf"
    pdf_path = output_dir / pdf_filename

    with open(pdf_path, "wb") as f:
        writer.write(f)

    error = ""
    if failed:
        error = f"Partial export: {len(failed)} frames failed ({failed})"

    logger.info(
        "Exported %d-page PDF → %s%s",
        len(writer.pages),
        pdf_path,
        f" ({len(failed)} failed)" if failed else "",
    )
    return {"pdf_path": str(pdf_path), "error": error}
