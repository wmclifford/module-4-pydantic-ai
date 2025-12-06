# Planned Diffs for TASK-003 – Implement Brave Search tool

## 1. web_search_agent/models.py (modify)

**Marker:** After the module-level docstring at the top of `web_search_agent/models.py`.

**Planned change:**
- Add backend-agnostic Pydantic models:
  - `SearchResult` with fields: `title`, `url`, `snippet`, `source`, `rank`, `raw`.
  - `SearchResults` with fields: `query`, `backend`, `results`, `total`,
    `summarizer_key`, `error`, `raw`.
- Ensure docstrings make clear that these models are shared across Brave and
  SearXNG backends.

**Diff sketch (illustrative):**

```python
"""Placeholder data models for search results and related entities.

This module will define Pydantic models for representing search results,
web pages, and other data structures used by the web search agent.
"""

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Normalized representation of a single search result."""

    title: str = Field(...)
    url: str = Field(...)
    snippet: str = Field(...)
    source: Optional[str] = Field(default=None)
    rank: Optional[int] = Field(default=None)
    raw: Optional[dict[str, Any]] = Field(default=None)


class SearchResults(BaseModel):
    """Container for normalized search results from any backend."""

    query: str = Field(...)
    backend: str = Field(...)
    results: List[SearchResult] = Field(default_factory=list)
    total: Optional[int] = Field(default=None)
    summarizer_key: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)
    raw: Optional[dict[str, Any]] = Field(default=None)
```

---

## 2. web_search_agent/tools.py (modify)

**Marker:** After the module-level docstring in `web_search_agent/tools.py`.

**Planned change:**
- Import httpx, config, and models.
- Define `BraveSearchError` exception.
- Implement `BraveSearchClient` that:
  - Uses `httpx.Client` with base URL `https://api.search.brave.com`.
  - Sends GET requests to `/res/v1/web/search` with headers:
    - `Accept: application/json`
    - `Accept-Encoding: gzip`
    - `X-Subscription-Token: <BRAVE_API_KEY>`
  - Accepts parameters like `query`, `count`, `offset`, optional `country`,
    `language`, `safesearch`, and internal `summary` flag.
  - Raises `BraveSearchError` on HTTP/network/JSON errors.
  - Parses responses into `SearchResults` and `SearchResult` instances,
    extracting `web.results`, `web.total`, and optional `summarizer.key`.
  - When Brave returns valid JSON without `web.results`, logs a warning and
    returns an empty `SearchResults` with `raw` populated, not an exception.
- Implement `create_brave_search_tool(app_config)` that:
  - Validates `app_config.brave.api_key`.
  - Constructs a `BraveSearchClient`.
  - Returns a callable `brave_search(query: str, max_results: int = 5)` that
    calls `client.search(query=query, count=max_results, summary=False)`.

**Diff sketch (illustrative):**

```python
"""Placeholder module for Brave and SearXNG tool implementations.

This module will contain tool functions for interacting with various
search engines like Brave Search API and SearXNG instances.
"""

from typing import Any, Dict, Optional, Callable

import httpx

from .config import AppConfig, BraveSearchConfig
from .models import SearchResult, SearchResults


class BraveSearchError(Exception):
    """Error raised for failures when calling the Brave Search API."""


class BraveSearchClient:
    """HTTP client for Brave Web Search API."""

    def __init__(
        self,
        config: BraveSearchConfig,
        *,
        base_url: str = "https://api.search.brave.com",
        client: Optional[httpx.Client] = None,
        timeout: float = 10.0,
    ) -> None:
        ...

    def search(
        self,
        query: str,
        *,
        count: int = 5,
        offset: int = 0,
        country: Optional[str] = None,
        language: Optional[str] = None,
        safesearch: Optional[str] = None,
        summary: bool = False,
    ) -> SearchResults:
        ...  # Build URL, headers, params; call httpx; parse JSON; handle errors.


def create_brave_search_tool(app_config: AppConfig) -> Callable[[str, int], SearchResults]:
    """Create a callable Brave search tool using the given application configuration."""

    ...
```

---

## 3. tests/test_tools_brave.py (add)

**Marker:** New file under `tests/` named `tests/test_tools_brave.py`.

**Planned change:**
- Add pytest-based unit tests that:
  - Mock httpx to verify correct URL, headers, and query parameters for a
    typical Brave web search request.
  - Confirm that the tool returns `SearchResults` with expected `SearchResult`
    entries on a happy-path response.
  - Verify that `BraveSearchError` is raised on HTTP status errors and JSON
    parsing failures.
  - Verify that when Brave returns valid JSON without `web.results`, the tool
    returns an empty `SearchResults` with `raw` populated and no exception.
  - Exercise internal summary support by calling `BraveSearchClient.search` with
    `summary=True` in tests and asserting that `summary=1` is sent and
    `summarizer_key` is populated when present.

**Diff sketch (illustrative):**

```python
import pytest
from unittest.mock import Mock

from web_search_agent.config import AppConfig, LLMConfig, BraveSearchConfig, SearXNGConfig
from web_search_agent.models import SearchResults
from web_search_agent.tools import (
    BraveSearchClient,
    BraveSearchError,
    create_brave_search_tool,
)


def test_brave_search_tool_happy_path(monkeypatch):
    ...  # Mock httpx, call tool, assert SearchResults contents.


def test_brave_search_client_summary_support(monkeypatch):
    ...  # Call client.search(..., summary=True) and assert summarizer_key.


def test_brave_search_missing_api_key():
    ...  # Ensure ValueError/BraveSearchError is raised when api_key is missing.


def test_brave_search_http_error(monkeypatch):
    ...  # Ensure BraveSearchError on HTTP status errors.


def test_brave_search_empty_results_structure(monkeypatch):
    ...  # Ensure empty SearchResults with raw populated when web.results is missing.
```
