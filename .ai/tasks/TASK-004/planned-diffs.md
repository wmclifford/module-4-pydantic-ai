# Planned Diffs for TASK-004 – Implement SearXNG Search tool

## Overview

Implement a SearXNG-based web-search tool that mirrors the existing Brave tool,
using configuration from SearXNGConfig, issuing HTTP requests to the
SEARXNG_BASE_URL instance, and returning normalized SearchResult/SearchResults
models while preserving backend details in the raw field.

Each planned diff below will map to a dedicated commit in the Scaffold pass.

## 1. Extend SearXNG configuration

- **File:** `web_search_agent/config.py`
- **Operation:** modify
- **Goal:** Extend `SearXNGConfig` with sensible defaults and env-driven
  parameters.
- **Details:**
  - Add fields: `timeout`, `default_categories`, `default_language`,
    `default_time_range`.
  - Map them from env vars when present: `SEARXNG_TIMEOUT`,
    `SEARXNG_DEFAULT_CATEGORIES`, `SEARXNG_DEFAULT_LANGUAGE`,
    `SEARXNG_DEFAULT_TIME_RANGE`.
  - Document defaults with *why* (e.g., timeout balances responsiveness vs.
    slower meta-search engines; `['general']` reduces surprising
    cross-category results).
- **Markers:**
  - Inside `class SearXNGConfig` definition.
  - Where `SearXNGConfig` is constructed in `load_config()` or equivalent.

### Content Sketch

```python
# ...existing imports...
from pydantic import BaseModel, Field
from typing import Optional, List


class SearXNGConfig(BaseModel):
  """Configuration for SearXNG backend.

  Reason: Centralizes SearXNG-specific behavior and defaults so the
  SearxngSearchClient can be configured consistently via env vars without
  per-call parameter sprawl.
  """

  base_url: Optional[str] = Field(
    default=None,
    description="Base URL of the SearXNG instance, e.g. https://searxng.example.com",
  )
  timeout: float = Field(
    default=10.0,
    description=(
      "Timeout in seconds for SearXNG HTTP requests. Default 10.0 provides "
      "a balance between responsiveness and allowing slower meta-search "
      "engines to respond."
    ),
  )
  default_categories: List[str] = Field(
    default_factory=lambda: ["general"],
    description=(
      "Default SearXNG categories to query when none are specified. "
      "Using ['general'] keeps responses focused on typical web search "
      "and avoids surprising image/video-heavy results."
    ),
  )
  default_language: Optional[str] = Field(
    default=None,
    description=(
      "Optional default language code (e.g. 'en'). If None, the SearXNG "
      "instance's own language defaults are used."
    ),
  )
  default_time_range: Optional[str] = Field(
    default=None,
    description=(
      "Optional default time_range filter (e.g. 'day', 'week', 'month'). "
      "If None, no time filter is applied and the instance default is used."
    ),
  )

  class Config:
    extra = "forbid"


def load_config() -> AppConfig:
  """Load and validate application configuration from environment variables."""
  # ...existing code...
  searxng = SearXNGConfig(
    base_url=os.getenv("SEARXNG_BASE_URL"),
    timeout=float(os.getenv("SEARXNG_TIMEOUT", "10.0")),
    default_categories=[c for c in os.getenv("SEARXNG_DEFAULT_CATEGORIES", "general").split(",") if c],
    default_language=os.getenv("SEARXNG_DEFAULT_LANGUAGE"),
    default_time_range=os.getenv("SEARXNG_DEFAULT_TIME_RANGE"),
  )
  # ...existing code wiring SearXNGConfig into AppConfig...
```

---

## 2. Clarify models as minimal and backend-agnostic

- **File:** `web_search_agent/models.py`
- **Operation:** modify
- **Goal:** Make it explicit that SearchResult/SearchResults are intentionally
  minimal and backend-agnostic.
- **Details:**
  - Update docstrings for `SearchResult` and `SearchResults` to state that
    backend-specific fields (e.g., SearXNG `category`, `score`, `engine`,
    `thumbnail`) remain in `raw` and are not promoted to first-class
    attributes.
  - No new fields are added; existing structure remains unchanged.
- **Markers:**
  - Inside `SearchResult` class docstring.
  - Inside `SearchResults` class docstring.

### Content Sketch

```python
"""Placeholder data models for search results and related entities.

This module defines Pydantic models for representing normalized search
results used by the web search agent.

The models are intentionally minimal and backend-agnostic: backend-specific
fields from Brave or SearXNG (e.g., category, score, engine, thumbnail,
infoboxes) are preserved only in the ``raw`` field and are not promoted to
first-class attributes.
"""


# ...existing imports...


class SearchResult(BaseModel):
  """Normalized representation of a single search result.

  The fields here are common across all supported backends. Any
  backend-specific metadata from Brave or SearXNG is kept in ``raw``.
  """

  # ...existing fields: title, url, snippet, source, rank, raw...


class SearchResults(BaseModel):
  """Container for normalized search results from any backend.

  ``backend`` identifies the source (e.g., "brave" or "searxng"). The
  backend's full response payload is stored in ``raw`` so callers can
  inspect engine-specific fields when needed without changing this model's
  public surface.
  """

  # ...existing fields: query, backend, results, total, summarizer_key, error, raw...
```

---

## 3. Add SearXNG HTTP client and error type

- **File:** `web_search_agent/tools/searxng.py`
- **Operation:** add
- **Goal:** Implement a dedicated SearXNG HTTP client mirroring the Brave
  client design.
- **Details:**
  - Add `SearxngSearchError` for SearXNG-specific failures.
  - Add `SearxngSearchClient` with:
    - Constructor accepting `base_url`, optional `httpx.Client`, `timeout`,
      `default_categories`, `default_language`, `default_time_range`.
    - `search(query, max_results=5, page=1, categories=None, language=None,
      time_range=None)` method that:
      - Calls `{base_url}/search` with `format=json`, `pageno`, and optional
        `categories`, `language`, `time_range` based on config/overrides.
      - Sets a realistic `User-Agent` header to avoid bot blocking.
      - Handles HTTPStatusError, TimeoutException, and RequestError by raising
        `SearxngSearchError` with clear messages.
      - Parses JSON into `SearchResults` using minimal `SearchResult` fields
        and preserves the full response in `raw`.
      - Treats missing or non-list `results` as "no results" and sets a
        helpful error message while returning an empty list.
      - Computes `total` from `number_of_results` when reliable, otherwise
        falls back to `len(results)`.
- **Markers:**
  - New module defining `SearxngSearchClient` and `SearxngSearchError`.

### Content Sketch

```python
"""SearXNG HTTP client and error types.

Reason: Encapsulate SearXNG-specific request/response handling in a focused
client that mirrors BraveSearchClient while normalizing into shared
SearchResult/SearchResults models.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

import httpx

from web_search_agent.models import SearchResult, SearchResults

logger = logging.getLogger(__name__)


class SearxngSearchError(Exception):
  """Exception raised for failures when calling a SearXNG instance."""


class SearxngSearchClient:
  """HTTP client for SearXNG search API."""

  def __init__(
          self,
          base_url: str,
          *,
          client: Optional[httpx.Client] = None,
          timeout: float = 10.0,
          default_categories: Optional[List[str]] = None,
          default_language: Optional[str] = None,
          default_time_range: Optional[str] = None,
  ) -> None:
    if not base_url or not isinstance(base_url, str):
      raise ValueError("base_url must be a non-empty string")

    self.base_url = base_url.rstrip("/")
    self.timeout = timeout
    self.default_categories = default_categories or ["general"]
    self.default_language = default_language
    self.default_time_range = default_time_range

    self._client = client or httpx.Client(timeout=timeout)
    self._owns_client = client is None

  def search(
          self,
          query: str,
          *,
          max_results: int = 5,
          page: int = 1,
          categories: Optional[List[str]] = None,
          language: Optional[str] = None,
          time_range: Optional[str] = None,
  ) -> SearchResults:
    """Execute a SearXNG search and normalize results.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return (client-side slice).
        page: 1-based page number (mapped to pageno).
        categories: Optional override categories for this call.
        language: Optional override language for this call.
        time_range: Optional override time range for this call.
    """
    url = f"{self.base_url}/search"
    params: dict[str, Any] = {
      "q": query,
      "format": "json",
      "pageno": max(page, 1),
    }

    cats = categories if categories is not None else self.default_categories
    if cats:
      params["categories"] = ",".join(cats)

    lang = language if language is not None else self.default_language
    if lang:
      params["language"] = lang

    tr = time_range if time_range is not None else self.default_time_range
    if tr:
      params["time_range"] = tr

    headers = {
      "Accept": "application/json",
      # Reason: avoid being treated as a bot by SearXNG instances.
      "User-Agent": "web-search-agent/1.0 (+https://example.com)",
    }

    try:
      response = self._client.get(url, headers=headers, params=params)
      response.raise_for_status()
    except httpx.HTTPStatusError as e:
      status = e.response.status_code
      text = e.response.text
      raise SearxngSearchError(
        f"SearXNG returned status {status}: {text}"
      ) from e
    except httpx.TimeoutException as e:
      raise SearxngSearchError(f"SearXNG request timed out: {e}") from e
    except httpx.RequestError as e:
      raise SearxngSearchError(f"Request to SearXNG failed: {e}") from e

    try:
      data = response.json()
    except ValueError as e:
      raise SearxngSearchError(
        f"Failed to parse SearXNG response as JSON: {e}"
      ) from e

    return self._parse_response(query=query, data=data, max_results=max_results)

  def _parse_response(
          self,
          query: str,
          data: dict[str, Any],
          *,
          max_results: int,
  ) -> SearchResults:
    raw_results = data.get("results")
    error: Optional[str] = None

    if not isinstance(raw_results, list):
      logger.warning("SearXNG response missing 'results' list")
      raw_results = []
      error = "No results found in SearXNG response"

    results: list[SearchResult] = []
    for idx, item in enumerate(raw_results):
      title = item.get("title") or item.get("url") or ""
      url = item.get("url", "")
      snippet = item.get("content", "") or ""
      parsed_url = item.get("parsed_url") or {}
      source = (
              item.get("source")
              or parsed_url.get("hostname")
              or None
      )

      position = item.get("position")
      rank = position if isinstance(position, int) else idx + 1

      results.append(
        SearchResult(
          title=title,
          url=url,
          snippet=snippet,
          source=source,
          rank=rank,
          raw=item,
        )
      )

    if max_results > 0:
      results = results[:max_results]

    total = data.get("number_of_results")
    if not isinstance(total, int) or total <= 0:
      total = len(results)

    if not results and error is None:
      error = "No results found in SearXNG response"

    return SearchResults(
      query=query,
      backend="searxng",
      results=results,
      total=total,
      summarizer_key=None,
      error=error,
      raw=data,
    )

  def __del__(self) -> None:
    if getattr(self, "_owns_client", False):
      try:
        self._client.close()
      except Exception:
        pass
```

---

## 4. Expose SearXNG tool factory

- **File:** `web_search_agent/tools.py`
- **Operation:** modify
- **Goal:** Provide a `create_searxng_search_tool` factory similar to the Brave
  factory.
- **Details:**
  - Import `SearxngSearchClient` and `SearxngSearchError` from the new module.
  - Implement `create_searxng_search_tool(app_config)` that:
    - Validates `app_config.searxng.base_url` is configured, otherwise raises
      `ValueError` with a clear message.
    - Instantiates `SearxngSearchClient` using `SearXNGConfig` fields
      (base_url, timeout, default_categories, default_language,
      default_time_range).
    - Returns a `searxng_search(query: str, max_results: int = 5)` callable
      that simply delegates to `client.search(query=query,
      max_results=max_results)`.
- **Markers:**
  - Imports section near Brave-related imports.
  - Adjacent to `create_brave_search_tool` definition.

### Content Sketch

```python
"""Placeholder module for Brave and SearXNG tool implementations."""

# ...existing imports...
from web_search_agent.config import AppConfig
from web_search_agent.models import SearchResults
from web_search_agent.tools.searxng import (
  SearxngSearchClient,
  SearxngSearchError,
)


def create_searxng_search_tool(app_config: AppConfig) -> callable:
  """Create a SearXNG search tool for use with Pydantic AI.

  Reason: Mirror the Brave search tool factory so the agent can swap
  backends without special handling.
  """
  if not app_config.searxng or not app_config.searxng.base_url:
    raise ValueError(
      "SearXNG base URL not configured. Set SEARXNG_BASE_URL environment variable."
    )

  cfg = app_config.searxng
  client = SearxngSearchClient(
    base_url=cfg.base_url,
    timeout=cfg.timeout,
    default_categories=cfg.default_categories,
    default_language=cfg.default_language,
    default_time_range=cfg.default_time_range,
  )

  def searxng_search(query: str, max_results: int = 5) -> SearchResults:
    """Execute a SearXNG web search using the configured instance."""

    return client.search(query=query, max_results=max_results)

  return searxng_search
```

---

## 5. Add tests for SearXNG client and tool

- **File:** `tests/test_tools_searxng.py`
- **Operation:** add
- **Goal:** Verify SearXNG client and tool behavior mirrors Brave tests.
- **Details:**
  - Add `TestSearxngSearchClient`:
    - Tests for valid/invalid initialization.
    - Happy-path search with realistic SearXNG JSON, verifying URL, params,
      and normalized `SearchResults`.
    - Tests for optional parameters (categories, language, time_range, page).
    - Error tests: HTTPStatusError, TimeoutException, RequestError, JSON
      parse errors, and missing/empty `results` structures.
    - Test that `raw` preserves the full backend response.
  - Add `TestSearxngSearchTool`:
    - Valid config returns a callable tool.
    - Missing `SEARXNG_BASE_URL` produces `ValueError`.
    - Tool callable delegates correctly to `SearxngSearchClient.search` with
      `query` and `max_results`.
- **Markers:**
  - New pytest module alongside `test_tools_brave.py`.

### Content Sketch

```python
"""Unit tests for the SearXNG search client and tool."""

from unittest.mock import Mock, patch

import httpx
import pytest

from web_search_agent.config import (
  AppConfig,
  LLMConfig,
  BraveSearchConfig,
  SearXNGConfig,
)
from web_search_agent.models import SearchResult, SearchResults
from web_search_agent.tools.searxng import (
  SearxngSearchClient,
  SearxngSearchError,
)
from web_search_agent.tools import create_searxng_search_tool


class TestSearxngSearchClient:
  def test_init_with_valid_base_url(self) -> None:
    client = SearxngSearchClient(base_url="https://searxng.example.com")
    assert client.base_url == "https://searxng.example.com"

  def test_init_with_empty_base_url_raises(self) -> None:
    with pytest.raises(ValueError):
      SearxngSearchClient(base_url="")

  @patch("web_search_agent.tools.searxng.httpx.Client.get")
  def test_search_happy_path(self, mock_get: Mock) -> None:
    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = {
      "number_of_results": 2,
      "results": [
        {
          "title": "Example 1",
          "url": "https://example1.com",
          "content": "Snippet 1",
          "source": "example1.com",
          "position": 1,
        },
        {
          "title": "Example 2",
          "url": "https://example2.com",
          "content": "Snippet 2",
          "source": "example2.com",
          "position": 2,
        },
      ],
    }
    mock_get.return_value = mock_response

    client = SearxngSearchClient(base_url="https://searxng.example.com")
    results = client.search("test query", max_results=5)

    mock_get.assert_called_once()
    called_url = mock_get.call_args.args[0]
    params = mock_get.call_args.kwargs["params"]
    assert called_url == "https://searxng.example.com/search"
    assert params["q"] == "test query"
    assert params["format"] == "json"
    assert isinstance(results, SearchResults)
    assert len(results.results) == 2

  # Additional tests for optional params, errors, and raw preservation...


class TestSearxngSearchTool:
  def test_create_searxng_search_tool_valid_config(self) -> None:
    app_config = AppConfig(
      llm=LLMConfig(provider="openai", api_key="key", choice="gpt-4"),
      brave=BraveSearchConfig(api_key=None),
      searxng=SearXNGConfig(base_url="https://searxng.example.com"),
    )
    tool = create_searxng_search_tool(app_config)
    assert callable(tool)

  def test_create_searxng_search_tool_missing_base_url(self) -> None:
    app_config = AppConfig(
      llm=LLMConfig(provider="openai", api_key="key", choice="gpt-4"),
      brave=BraveSearchConfig(api_key=None),
      searxng=SearXNGConfig(base_url=None),
    )
    with pytest.raises(ValueError):
      create_searxng_search_tool(app_config)

  @patch("web_search_agent.tools.searxng.SearxngSearchClient.search")
  def test_searxng_search_tool_calls_client(self, mock_search: Mock) -> None:
    mock_search.return_value = SearchResults(
      query="test",
      backend="searxng",
      results=[],
    )
    app_config = AppConfig(
      llm=LLMConfig(provider="openai", api_key="key", choice="gpt-4"),
      brave=BraveSearchConfig(api_key=None),
      searxng=SearXNGConfig(base_url="https://searxng.example.com"),
    )
    tool = create_searxng_search_tool(app_config)
    result = tool("test query", max_results=3)
    mock_search.assert_called_once()
    assert isinstance(result, SearchResults)
```

---

## 6. Document future work for advanced SearXNG parameters

- **File:** `docs/TASKS.md`
- **Operation:** modify
- **Goal:** Record a generic TODO under "Discovered During Work" about
  exposing advanced SearXNG parameters.
- **Details:**
  - Under the "Discovered During Work" heading, add a bullet describing
    potential follow-up work to expose categories, language, and time_range as
    first-class options in the agent/CLI/MCP interfaces while maintaining
    parity with Brave and avoiding confusing defaults.
- **Markers:**
  - Under the "Discovered During Work" section near the end of the file.

### Content Sketch

```markdown
## 5. Discovered During Work

- Expose advanced SearXNG parameters in public interfaces (future task)
  - Background: TASK-004 keeps the SearXNG tool's public signature minimal
    (query, max_results) and drives categories, language, and time_range from
    configuration only.
  - Future work:
    - Decide how and where to surface categories/language/time_range as
      user-facing options (agent prompts, CLI flags, MCP tool parameters).
    - Ensure any additional knobs remain consistent with Brave's interface
      and do not surprise users with backend-specific behavior.
```

---

These planned diffs will be implemented in the Scaffold pass as separate
commits following the Conventional Commits style, with this spec and the task
file forming the first commit once the branch is created.
