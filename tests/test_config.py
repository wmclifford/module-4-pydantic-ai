"""Unit tests for web_search_agent.config module.

Tests cover:
- Successful configuration loading with valid environment variables
- Missing required environment variables
- Malformed input values
- Search backend configuration validation
"""

import os
from unittest.mock import patch

import pytest

from web_search_agent.config import (
    AppConfig,
    BraveSearchConfig,
    LLMConfig,
    SearXNGConfig,
    load_config,
)


class TestLLMConfig:
    """Tests for LLMConfig model."""

    def test_valid_llm_config(self):
        """Test creating a valid LLMConfig."""
        config = LLMConfig(
            provider="openai",
            base_url="https://api.openai.com/v1",
            api_key="sk-test-key",
            choice="gpt-4",
        )
        assert config.provider == "openai"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.api_key == "sk-test-key"
        assert config.choice == "gpt-4"

    def test_llm_config_without_base_url(self):
        """Test creating LLMConfig without optional base_url."""
        config = LLMConfig(
            provider="openai",
            api_key="sk-test-key",
            choice="gpt-4",
        )
        assert config.provider == "openai"
        assert config.base_url is None
        assert config.api_key == "sk-test-key"
        assert config.choice == "gpt-4"

    def test_llm_config_empty_provider(self):
        """Test that empty provider raises ValueError."""
        with pytest.raises(ValueError, match="provider cannot be empty"):
            LLMConfig(
                provider="",
                api_key="sk-test-key",
                choice="gpt-4",
            )

    def test_llm_config_empty_api_key(self):
        """Test that empty API key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            LLMConfig(
                provider="openai",
                api_key="",
                choice="gpt-4",
            )

    def test_llm_config_empty_choice(self):
        """Test that empty choice raises ValueError."""
        with pytest.raises(ValueError, match="choice cannot be empty"):
            LLMConfig(
                provider="openai",
                api_key="sk-test-key",
                choice="",
            )

    def test_llm_config_whitespace_trimming(self):
        """Test that whitespace is trimmed from fields."""
        config = LLMConfig(
            provider="  openai  ",
            api_key="  sk-test-key  ",
            choice="  gpt-4  ",
        )
        assert config.provider == "openai"
        assert config.api_key == "sk-test-key"
        assert config.choice == "gpt-4"


class TestBraveSearchConfig:
    """Tests for BraveSearchConfig model."""

    def test_brave_config_with_api_key(self):
        """Test creating BraveSearchConfig with API key."""
        config = BraveSearchConfig(api_key="brave-key-123")
        assert config.api_key == "brave-key-123"

    def test_brave_config_without_api_key(self):
        """Test creating BraveSearchConfig without API key (None)."""
        config = BraveSearchConfig()
        assert config.api_key is None

    def test_brave_config_empty_api_key_raises_error(self):
        """Test that empty string API key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be an empty string"):
            BraveSearchConfig(api_key="")

    def test_brave_config_whitespace_api_key_raises_error(self):
        """Test that whitespace-only API key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be an empty string"):
            BraveSearchConfig(api_key="   ")

    def test_brave_config_api_key_trimming(self):
        """Test that API key whitespace is trimmed."""
        config = BraveSearchConfig(api_key="  brave-key-123  ")
        assert config.api_key == "brave-key-123"


class TestSearXNGConfig:
    """Tests for SearXNGConfig model."""

    def test_searxng_config_with_base_url(self):
        """Test creating SearXNGConfig with base URL."""
        config = SearXNGConfig(base_url="https://searxng.example.com")
        assert config.base_url == "https://searxng.example.com"

    def test_searxng_config_without_base_url(self):
        """Test creating SearXNGConfig without base URL (None)."""
        config = SearXNGConfig()
        assert config.base_url is None

    def test_searxng_config_empty_base_url_raises_error(self):
        """Test that empty string base URL raises ValueError."""
        with pytest.raises(ValueError, match="base URL cannot be an empty string"):
            SearXNGConfig(base_url="")

    def test_searxng_config_whitespace_base_url_raises_error(self):
        """Test that whitespace-only base URL raises ValueError."""
        with pytest.raises(ValueError, match="base URL cannot be an empty string"):
            SearXNGConfig(base_url="   ")

    def test_searxng_config_base_url_trimming(self):
        """Test that base URL whitespace is trimmed."""
        config = SearXNGConfig(base_url="  https://searxng.example.com  ")
        assert config.base_url == "https://searxng.example.com"


class TestAppConfig:
    """Tests for AppConfig model."""

    def test_app_config_with_brave_backend(self):
        """Test creating AppConfig with Brave Search backend."""
        config = AppConfig(
            llm=LLMConfig(
                provider="openai",
                api_key="sk-test-key",
                choice="gpt-4",
            ),
            brave=BraveSearchConfig(api_key="brave-key-123"),
            searxng=SearXNGConfig(),
        )
        assert config.llm.provider == "openai"
        assert config.brave.api_key == "brave-key-123"
        assert config.searxng.base_url is None

    def test_app_config_with_searxng_backend(self):
        """Test creating AppConfig with SearXNG backend."""
        config = AppConfig(
            llm=LLMConfig(
                provider="openai",
                api_key="sk-test-key",
                choice="gpt-4",
            ),
            brave=BraveSearchConfig(),
            searxng=SearXNGConfig(base_url="https://searxng.example.com"),
        )
        assert config.llm.provider == "openai"
        assert config.brave.api_key is None
        assert config.searxng.base_url == "https://searxng.example.com"

    def test_app_config_with_both_backends(self):
        """Test creating AppConfig with both backends configured."""
        config = AppConfig(
            llm=LLMConfig(
                provider="openai",
                api_key="sk-test-key",
                choice="gpt-4",
            ),
            brave=BraveSearchConfig(api_key="brave-key-123"),
            searxng=SearXNGConfig(base_url="https://searxng.example.com"),
        )
        assert config.brave.api_key == "brave-key-123"
        assert config.searxng.base_url == "https://searxng.example.com"

    def test_app_config_no_backends_raises_error(self):
        """Test that AppConfig raises error when no backends are configured."""
        with pytest.raises(
                ValueError,
                match="At least one search backend must be configured",
        ):
            AppConfig(
                llm=LLMConfig(
                    provider="openai",
                    api_key="sk-test-key",
                    choice="gpt-4",
                ),
                brave=BraveSearchConfig(),
                searxng=SearXNGConfig(),
            )


class TestLoadConfig:
    """Tests for load_config() function."""

    def test_load_config_success_with_brave(self):
        """Test successful config loading with Brave backend."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "sk-test-key",
            "LLM_CHOICE": "gpt-4",
            "BRAVE_API_KEY": "brave-key-123",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            assert config.llm.provider == "openai"
            assert config.llm.api_key == "sk-test-key"
            assert config.llm.choice == "gpt-4"
            assert config.brave.api_key == "brave-key-123"
            assert config.searxng.base_url is None

    def test_load_config_success_with_searxng(self):
        """Test successful config loading with SearXNG backend."""
        env_vars = {
            "LLM_PROVIDER": "anthropic",
            "LLM_API_KEY": "claude-key",
            "LLM_CHOICE": "claude-3-opus",
            "SEARXNG_BASE_URL": "https://searxng.example.com",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            assert config.llm.provider == "anthropic"
            assert config.llm.api_key == "claude-key"
            assert config.llm.choice == "claude-3-opus"
            assert config.searxng.base_url == "https://searxng.example.com"
            assert config.brave.api_key is None

    def test_load_config_success_with_both_backends(self):
        """Test successful config loading with both backends."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "LLM_BASE_URL": "https://api.openai.com/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_CHOICE": "gpt-4",
            "BRAVE_API_KEY": "brave-key-123",
            "SEARXNG_BASE_URL": "https://searxng.example.com",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            assert config.llm.provider == "openai"
            assert config.llm.base_url == "https://api.openai.com/v1"
            assert config.brave.api_key == "brave-key-123"
            assert config.searxng.base_url == "https://searxng.example.com"

    def test_load_config_missing_llm_provider(self):
        """Test that missing LLM_PROVIDER raises ValueError."""
        env_vars = {
            "LLM_API_KEY": "sk-test-key",
            "LLM_CHOICE": "gpt-4",
            "BRAVE_API_KEY": "brave-key-123",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="LLM_PROVIDER"):
                load_config()

    def test_load_config_missing_llm_api_key(self):
        """Test that missing LLM_API_KEY raises ValueError."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "LLM_CHOICE": "gpt-4",
            "BRAVE_API_KEY": "brave-key-123",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="LLM_API_KEY"):
                load_config()

    def test_load_config_missing_llm_choice(self):
        """Test that missing LLM_CHOICE raises ValueError."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "sk-test-key",
            "BRAVE_API_KEY": "brave-key-123",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="LLM_CHOICE"):
                load_config()

    def test_load_config_no_backends(self):
        """Test that missing both backends raises ValueError."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "sk-test-key",
            "LLM_CHOICE": "gpt-4",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(
                    ValueError,
                    match="At least one search backend must be configured",
            ):
                load_config()

    def test_load_config_empty_llm_provider(self):
        """Test that empty LLM_PROVIDER raises ValueError."""
        env_vars = {
            "LLM_PROVIDER": "",
            "LLM_API_KEY": "sk-test-key",
            "LLM_CHOICE": "gpt-4",
            "BRAVE_API_KEY": "brave-key-123",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                load_config()

    def test_load_config_empty_brave_api_key(self):
        """Test that empty BRAVE_API_KEY is treated as not configured."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "sk-test-key",
            "LLM_CHOICE": "gpt-4",
            "BRAVE_API_KEY": "",
            "SEARXNG_BASE_URL": "https://searxng.example.com",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                load_config()

    def test_load_config_whitespace_llm_provider(self):
        """Test that whitespace-only LLM_PROVIDER is trimmed and validated."""
        env_vars = {
            "LLM_PROVIDER": "   ",
            "LLM_API_KEY": "sk-test-key",
            "LLM_CHOICE": "gpt-4",
            "BRAVE_API_KEY": "brave-key-123",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                load_config()
