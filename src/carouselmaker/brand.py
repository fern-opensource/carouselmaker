"""Brand token loading and validation."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class BrandColors(BaseModel):
    bg_light: str
    bg_dark: str
    text_dark: str
    text_light: str
    text_muted: str
    accent: str
    divider: str

    @field_validator("*")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError(f"Invalid hex color: {v!r} (expected #RRGGBB)")
        return v


class BrandTypography(BaseModel):
    font_heading: str
    font_body: str


class BrandLayout(BaseModel):
    slide_w: int = 1080
    slide_h: int = 1080
    padding: int = 88
    corner_radius: int = 16


class BrandFigma(BaseModel):
    icon_library_file_key: str = ""


class BrandConfig(BaseModel):
    name: str
    tagline: str = ""
    colors: BrandColors
    typography: BrandTypography
    layout: BrandLayout = Field(default_factory=BrandLayout)
    figma: BrandFigma = Field(default_factory=BrandFigma)

    def to_flat_dict(self) -> dict:
        """Flatten into the dict format used by instruction builders."""
        return {
            "name": self.name,
            "tagline": self.tagline,
            **self.colors.model_dump(),
            **self.typography.model_dump(),
            **self.layout.model_dump(),
            "icon_library_file_key": self.figma.icon_library_file_key,
        }


def load_brand(brand_file: str = "brand.json") -> dict:
    """Load and validate brand tokens from a JSON file.

    Returns a flat dict of brand tokens for use in instruction builders.
    Raises FileNotFoundError if the file doesn't exist.
    Raises pydantic.ValidationError if the file is malformed.
    """
    path = Path(brand_file)
    if not path.exists():
        raise FileNotFoundError(
            f"Brand file not found: {brand_file}. "
            "Create a brand.json or pass --brand to specify one. "
            "See examples/brand_hotpink.json for the expected format."
        )

    with open(path) as f:
        raw = json.load(f)

    config = BrandConfig(**raw)
    return config.to_flat_dict()
