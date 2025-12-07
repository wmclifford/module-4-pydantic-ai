"""Configuration management for the web-search agent.

This module provides Pydantic-based configuration models for loading and validating
environment variables related to LLM settings and search backends.
"""

from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


class LLMConfig(BaseModel):
    """Configuration for the Language Model provider.

    Attributes:
        provider (str): The LLM provider name (e.g., 'openai', 'anthropic', 'ollama').
        base_url (Optional[str]): The base URL for the LLM API (optional, for custom endpoints).
        api_key (str): The API key for authentication with the LLM provider.
        choice (str): The specific model choice (e.g., 'gpt-4', 'claude-3-opus').
    """

    provider: str = Field(..., description="LLM provider name")
    base_url: Optional[str] = Field(None, description="Base URL for LLM API")
    api_key: str = Field(..., description="API key for LLM provider")
    choice: str = Field(..., description="Model choice (e.g., gpt-4, claude-3-opus)")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate that provider is not empty."""
        if not v or not v.strip():
            raise ValueError("LLM provider cannot be empty")
        return v.strip()

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate that API key is not empty."""
        if not v or not v.strip():
            raise ValueError("LLM API key cannot be empty")
        return v.strip()

    @field_validator("choice")
    @classmethod
    def validate_choice(cls, v: str) -> str:
        """Validate that model choice is not empty."""
        if not v or not v.strip():
            raise ValueError("LLM choice cannot be empty")
        return v.strip()


class BraveSearchConfig(BaseModel):
    """Configuration for Brave Search backend.

    Attributes:
        api_key (Optional[str]): The API key for Brave Search. If None, Brave Search is disabled.
    """

    api_key: Optional[str] = Field(None, description="Brave Search API key")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate that API key is not an empty string (None is allowed)."""
        if v is not None and not v.strip():
            raise ValueError("Brave Search API key cannot be an empty string")
        return v.strip() if v else None


class SearXNGConfig(BaseModel):
    """Configuration for SearXNG backend.

    Attributes:
        base_url (Optional[str]): The base URL for the SearXNG instance. If None, SearXNG is disabled.
        timeout (float): HTTP timeout for SearXNG requests.
        default_categories (List[str]): Categories applied when none are supplied.
        default_language (Optional[str]): Default language code for requests.
        default_time_range (Optional[str]): Default SearXNG time_range filter.
    """

    base_url: Optional[str] = Field(None, description="SearXNG base URL")
    timeout: float = Field(
        default=10.0,
        description="Timeout in seconds for SearXNG requests; balances responsiveness with slower meta-search engines.",
    )
    default_categories: List[str] = Field(
        default_factory=lambda: ["general"],
        description="Default categories to query when none are provided, keeping results focused on general web content.",
    )
    default_language: Optional[str] = Field(
        default=None,
        description="Optional default language code (e.g., 'en'); None defers to the SearXNG server defaults.",
    )
    default_time_range: Optional[str] = Field(
        default=None,
        description="Optional time_range filter (e.g., 'day', 'week', 'month'); None applies no extra filtering.",
    )

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate that base URL is not an empty string (None is allowed)."""
        if v is not None and not v.strip():
            raise ValueError("SearXNG base URL cannot be an empty string")
        return v.strip() if v else None

    @field_validator("default_categories")
    @classmethod
    def normalize_categories(cls, v: List[str]) -> List[str]:
        """Ensure default categories are trimmed and fall back to ['general']."""
        cleaned = [cat.strip() for cat in v if cat and cat.strip()]
        return cleaned or ["general"]

    class Config:
        extra = "forbid"


class AppConfig(BaseModel):
    """Top-level application configuration.

    Enforces that at least one search backend is configured.

    Attributes:
        llm (LLMConfig): LLM configuration.
        brave (BraveSearchConfig): Brave Search configuration.
        searxng (SearXNGConfig): SearXNG configuration.
    """

    llm: LLMConfig
    brave: BraveSearchConfig
    searxng: SearXNGConfig

    @field_validator("searxng", mode="after")
    @classmethod
    def validate_at_least_one_backend(cls, v: SearXNGConfig, info) -> SearXNGConfig:
        """Ensure at least one search backend is configured."""
        brave_config = info.data.get("brave")
        if brave_config and brave_config.api_key:
            return v
        if v.base_url:
            return v
        raise ValueError(
            "At least one search backend must be configured: "
            "either BRAVE_API_KEY or SEARXNG_BASE_URL must be set"
        )


def load_config() -> AppConfig:
    """Load and validate configuration from environment variables.

    Reads the following environment variables:
    - LLM_PROVIDER: The LLM provider name (required)
    - LLM_BASE_URL: The base URL for the LLM API (optional)
    - LLM_API_KEY: The API key for the LLM provider (required)
    - LLM_CHOICE: The specific model choice (required)
    - BRAVE_API_KEY: The API key for Brave Search (optional)
    - SEARXNG_BASE_URL: The base URL for SearXNG (optional)

    Returns:
        AppConfig: A validated configuration object.

    Raises:
        ValueError: If required environment variables are missing or malformed.
        ValidationError: If configuration validation fails.
    """
    import os

    from pydantic import ValidationError

    # Load LLM configuration
    llm_provider = os.getenv("LLM_PROVIDER")
    llm_base_url = os.getenv("LLM_BASE_URL")
    llm_api_key = os.getenv("LLM_API_KEY")
    llm_choice = os.getenv("LLM_CHOICE")

    # Load search backend configuration
    brave_api_key = os.getenv("BRAVE_API_KEY")
    searxng_base_url = os.getenv("SEARXNG_BASE_URL")

    # Validate required LLM variables
    if not llm_provider:
        raise ValueError("Missing required environment variable: LLM_PROVIDER")
    if not llm_api_key:
        raise ValueError("Missing required environment variable: LLM_API_KEY")
    if not llm_choice:
        raise ValueError("Missing required environment variable: LLM_CHOICE")

    try:
        config = AppConfig(
            llm=LLMConfig(
                provider=llm_provider,
                base_url=llm_base_url,
                api_key=llm_api_key,
                choice=llm_choice,
            ),
            brave=BraveSearchConfig(api_key=brave_api_key),
            searxng=SearXNGConfig(
                base_url=searxng_base_url,
                timeout=float(os.getenv("SEARXNG_TIMEOUT", "10.0")),
                default_categories=[
                    cat
                    for cat in os.getenv("SEARXNG_DEFAULT_CATEGORIES", "general").split(",")
                    if cat and cat.strip()
                ],
                default_language=os.getenv("SEARXNG_DEFAULT_LANGUAGE"),
                default_time_range=os.getenv("SEARXNG_DEFAULT_TIME_RANGE"),
            ),
        )
        return config
    except ValidationError as e:
        # Re-raise with more context
        raise ValueError(f"Configuration validation failed: {e}") from e
