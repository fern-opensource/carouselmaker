from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    figma_access_token: str = ""
    figma_output_file_key: str = ""

    brand_file: str = "brand.json"
    extraction_model: str = "claude-sonnet-4-5-20250929"
    output_dir: str = "output"


@lru_cache
def get_settings(**overrides: str) -> Settings:
    return Settings(**overrides)


def get_settings_with_overrides(**overrides: str) -> Settings:
    """Create settings with explicit overrides (bypasses cache)."""
    return Settings(**overrides)
