# Planned Diffs for TASK-002: Configuration and CI Setup

## Overview

This document describes the planned changes to implement configuration management via Pydantic models and set up initial
GitHub Actions CI workflow.

---

## Diff 1: Create `web_search_agent/config.py`

**File:** `web_search_agent/config.py`  
**Change Type:** Add  
**Location:** New file in the web_search_agent package root

### Description

Define Pydantic-based configuration models that validate environment variables for LLM provider settings and search
backends. Provide a `load_config()` function as the single entrypoint for loading and validating configuration.

### Content Sketch

```python
from pydantic import BaseModel, Field, validator, ValidationError
from typing import Optional
import os
import sys


class LLMConfig(BaseModel):
    """Configuration for the LLM provider."""
    provider: str = Field(..., description="LLM provider: one of 'openai', 'openrouter', or 'ollama'")
    base_url: Optional[str] = Field(None, description="Optional custom base URL for LLM provider")
    api_key: str = Field(..., description="API key for the LLM provider")
    model_choice: str = Field(..., description="Model name/choice (e.g., 'gpt-4o' for OpenAI)")

    class Config:
        extra = "forbid"


class BraveSearchConfig(BaseModel):
    """Configuration for Brave Search backend."""
    api_key: Optional[str] = Field(None, description="Brave Search API key")

    class Config:
        extra = "forbid"


class SearXNGConfig(BaseModel):
    """Configuration for SearXNG backend."""
    base_url: Optional[str] = Field(None, description="SearXNG instance base URL")

    class Config:
        extra = "forbid"


class SearchConfig(BaseModel):
    """Search backend configuration with validation that at least one is configured."""
    brave: BraveSearchConfig = Field(default_factory=BraveSearchConfig)
    searxng: SearXNGConfig = Field(default_factory=SearXNGConfig)

    @validator("searxng", pre=True, always=True)
    def validate_at_least_one_backend(cls, v, values):
        brave_has_key = values.get("brave", {}).get("api_key") if isinstance(values.get("brave"), dict) else (
            values.get("brave").api_key if hasattr(values.get("brave"), "api_key") else None)
        if not brave_has_key and not v.base_url:
            raise ValueError("At least one search backend (Brave or SearXNG) must be configured")
        return v

    class Config:
        extra = "forbid"


class AppConfig(BaseModel):
    """Top-level application configuration."""
    llm: LLMConfig
    search: SearchConfig

    class Config:
        extra = "forbid"


def load_config() -> AppConfig:
    """
    Load and validate application configuration from environment variables.
    
    Environment Variables:
        LLM_PROVIDER: str (required)
        LLM_BASE_URL: str (optional)
        LLM_API_KEY: str (required)
        LLM_CHOICE: str (required)
        BRAVE_API_KEY: str (optional)
        SEARXNG_BASE_URL: str (optional)
    
    Returns:
        AppConfig: Validated application configuration
        
    Raises:
        ValidationError: If required variables are missing or invalid
    """
    try:
        config = AppConfig(
            llm=LLMConfig(
                provider=os.getenv("LLM_PROVIDER"),
                base_url=os.getenv("LLM_BASE_URL"),
                api_key=os.getenv("LLM_API_KEY"),
                model_choice=os.getenv("LLM_CHOICE"),
            ),
            search=SearchConfig(
                brave=BraveSearchConfig(
                    api_key=os.getenv("BRAVE_API_KEY"),
                ),
                searxng=SearXNGConfig(
                    base_url=os.getenv("SEARXNG_BASE_URL"),
                ),
            ),
        )
        return config
    except ValidationError as e:
        print(f"Configuration validation failed:\n{e}", file=sys.stderr)
        raise
```

### Justification

- Centralizes all configuration logic in a single module
- Uses Pydantic for robust validation and type-safety
- Enforces business rules (at least one search backend)
- Provides clear error messages for misconfiguration
- Serves as single source of truth for all consumers (agent, tools, CLI, MCP)

---

## Diff 2: Create `.env.example`

**File:** `.env.example`  
**Change Type:** Add  
**Location:** Project root

### Description

Document all environment variables needed by the agent, with brief comments explaining each one. No secrets included.

### Content Sketch

```
# LLM Configuration
# The LLM provider to use: one of "openai", "openrouter", or "ollama"
LLM_PROVIDER=openai

# Optional: Custom base URL for the LLM provider (leave empty for defaults)
LLM_BASE_URL=

# API key for the LLM provider (required for authentication)
LLM_API_KEY=your-api-key-here

# The specific model/version to use with the LLM provider (e.g., "gpt-4o" for OpenAI)
LLM_CHOICE=gpt-4o

# Search Backend Configuration
# At least one of BRAVE_API_KEY or SEARXNG_BASE_URL must be configured

# Optional: Brave Search API key (get one at https://api.search.brave.com)
BRAVE_API_KEY=

# Optional: SearXNG instance base URL (e.g., https://searxng.example.com)
SEARXNG_BASE_URL=
```

### Justification

- Provides developer reference for environment setup
- Includes helpful comments and URLs
- Contains no actual secrets
- Follows project conventions (simple, well-documented)

---

## Diff 3: Create `.github/workflows/ci.yml`

**File:** `.github/workflows/ci.yml`  
**Change Type:** Add  
**Location:** `.github/workflows/` directory

### Description

GitHub Actions workflow that runs on pushes and pull requests, executing code formatting checks (ruff) and pytest test
suite.

### Content Sketch

```yaml
name: CI

on:
  push:
    branches:
      - main
      - "feat/**"
  pull_request:
    branches:
      - main

jobs:
  lint-and-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v2
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.14"

      - name: Sync dependencies
        run: uv sync

      - name: Run ruff linter
        run: uv run ruff check .

      - name: Run ruff formatter check
        run: uv run ruff format --check .

      - name: Run pytest
        run: uv run pytest tests/ -v
```

### Justification

- Automates code quality checks on every push and PR
- Ensures linting and tests pass before merge
- Uses uv for consistent dependency management
- Supports Python 3.14 as specified in pyproject.toml
- Simple, minimal workflow suitable for project stage

---

## Diff 4: Create `tests/test_config.py`

**File:** `tests/test_config.py`  
**Change Type:** Add  
**Location:** New file in tests directory

### Description

Unit tests covering configuration loading, validation, and error scenarios.

### Content Sketch

```python
import pytest
import os
from pydantic import ValidationError
from web_search_agent.config import (
    load_config,
    AppConfig,
    LLMConfig,
    SearchConfig,
    BraveSearchConfig,
    SearXNGConfig,
)


class TestLLMConfig:
    """Tests for LLMConfig validation."""

    def test_valid_llm_config(self):
        """Test successful LLM configuration creation."""
        config = LLMConfig(
            provider="openai",
            base_url=None,
            api_key="sk-test",
            model_choice="gpt-4o",
        )
        assert config.provider == "openai"
        assert config.api_key == "sk-test"

    def test_missing_required_llm_field(self):
        """Test that missing required LLM fields raise ValidationError."""
        with pytest.raises(ValidationError):
            LLMConfig(
                provider="anthropic",
                api_key="sk-test",
                # model_choice missing
            )


class TestSearchConfig:
    """Tests for search backend configuration."""

    def test_brave_backend_configured(self):
        """Test valid configuration with only Brave backend."""
        config = SearchConfig(
            brave=BraveSearchConfig(api_key="test-brave-key"),
            searxng=SearXNGConfig(base_url=None),
        )
        assert config.brave.api_key == "test-brave-key"

    def test_searxng_backend_configured(self):
        """Test valid configuration with only SearXNG backend."""
        config = SearchConfig(
            brave=BraveSearchConfig(api_key=None),
            searxng=SearXNGConfig(base_url="https://searxng.example.com"),
        )
        assert config.searxng.base_url == "https://searxng.example.com"

    def test_both_backends_configured(self):
        """Test valid configuration with both backends."""
        config = SearchConfig(
            brave=BraveSearchConfig(api_key="brave-key"),
            searxng=SearXNGConfig(base_url="https://searxng.example.com"),
        )
        assert config.brave.api_key == "brave-key"
        assert config.searxng.base_url == "https://searxng.example.com"

    def test_no_backend_configured_raises_error(self):
        """Test that at least one backend must be configured."""
        with pytest.raises(ValidationError) as exc_info:
            SearchConfig(
                brave=BraveSearchConfig(api_key=None),
                searxng=SearXNGConfig(base_url=None),
            )
        assert "at least one search backend" in str(exc_info.value).lower()


class TestLoadConfig:
    """Tests for load_config() function with environment variables."""

    def test_load_config_happy_path(self, monkeypatch):
        """Test successful config loading with valid env vars."""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_CHOICE", "gpt-4o")
        monkeypatch.setenv("BRAVE_API_KEY", "brave-key")

        config = load_config()
        assert config.llm.provider == "openai"
        assert config.llm.api_key == "test-key"
        assert config.search.brave.api_key == "brave-key"

    def test_load_config_missing_llm_provider(self, monkeypatch):
        """Test that missing LLM_PROVIDER raises ValidationError."""
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_CHOICE", "gpt-4o")
        monkeypatch.setenv("BRAVE_API_KEY", "brave-key")

        with pytest.raises(ValidationError):
            load_config()

    def test_load_config_missing_api_key(self, monkeypatch):
        """Test that missing LLM_API_KEY raises ValidationError."""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.setenv("LLM_CHOICE", "gpt-4o")
        monkeypatch.setenv("BRAVE_API_KEY", "brave-key")

        with pytest.raises(ValidationError):
            load_config()

    def test_load_config_no_backend_configured(self, monkeypatch):
        """Test that at least one search backend must be configured."""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_CHOICE", "gpt-4o")
        monkeypatch.delenv("BRAVE_API_KEY", raising=False)
        monkeypatch.delenv("SEARXNG_BASE_URL", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            load_config()
        assert "at least one search backend" in str(exc_info.value).lower()

    def test_load_config_with_searxng_only(self, monkeypatch):
        """Test successful config with only SearXNG configured."""
        monkeypatch.setenv("LLM_PROVIDER", "ollama")
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_CHOICE", "llama2")
        monkeypatch.delenv("BRAVE_API_KEY", raising=False)
        monkeypatch.setenv("SEARXNG_BASE_URL", "https://searxng.example.com")

        config = load_config()
        assert config.search.searxng.base_url == "https://searxng.example.com"

    def test_load_config_with_llm_base_url(self, monkeypatch):
        """Test config loading with optional LLM_BASE_URL."""
        monkeypatch.setenv("LLM_PROVIDER", "openrouter")
        monkeypatch.setenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_CHOICE", "mistralai/mistral-7b")
        monkeypatch.setenv("BRAVE_API_KEY", "brave-key")

        config = load_config()
        assert config.llm.base_url == "https://openrouter.ai/api/v1"
```

### Justification

- Covers happy path with all required variables present
- Tests missing required variables (LLM_PROVIDER, LLM_API_KEY, LLM_CHOICE)
- Validates backend configuration enforcement (at least one required)
- Tests optional fields (LLM_BASE_URL, SEARXNG_BASE_URL, BRAVE_API_KEY)
- Uses pytest fixtures (monkeypatch) for environment variable isolation
- Follows project test conventions

---

## Summary of Changes

| File                         | Type | Purpose                                                   |
|------------------------------|------|-----------------------------------------------------------|
| `web_search_agent/config.py` | Add  | Pydantic-based config models and load_config() entrypoint |
| `.env.example`               | Add  | Environment variable documentation                        |
| `.github/workflows/ci.yml`   | Add  | GitHub Actions CI workflow (lint + test)                  |
| `tests/test_config.py`       | Add  | Unit tests for configuration validation                   |

All changes follow project conventions (PEP8, Pydantic, pytest) and are minimal/focused on the specific task
requirements. No existing files are modified.

