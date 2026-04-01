"""Carousel data models."""

from __future__ import annotations

import enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SlideType(str, enum.Enum):
    COVER = "cover"
    CONTENT = "content"
    SUMMARY = "summary"
    CTA = "cta"


class CarouselSlide(BaseModel):
    """A single slide in the carousel."""

    slide_number: int
    slide_type: SlideType
    heading: str
    subheading: str = ""
    body: str = ""
    bullet_points: list[str] = Field(default_factory=list)
    footnote: str = ""
    icon_hint: str = ""


class CarouselSpec(BaseModel):
    """Full carousel specification extracted from markdown content."""

    id: UUID = Field(default_factory=uuid4)
    title: str
    subtitle: str = ""
    series_name: str = ""
    tagline: str = ""
    slides: list[CarouselSlide] = Field(default_factory=list)

    @property
    def slide_count(self) -> int:
        return len(self.slides)
