"""Placeholder module for Brave and SearXNG tool implementations.

This module will contain tool functions for interacting with various
search engines like Brave Search API and SearXNG instances.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Iterable, List, Optional

import httpx

from .config import AppConfig
from .models import SearchResult, SearchResults

logger = logging.getLogger(__name__)


class BraveSearchError(Exception):
    """Exception raised for failures when calling the Brave Search API."""

    pass


class BraveSearchClient:
    """HTTP client for calling the Brave Web Search API.

    This client handles request construction, parameter validation, API calls,
    response parsing, and error handling for the Brave Search API.
    """

    def __init__(
            self,
            api_key: str,
            *,
            base_url: str = "https://api.search.brave.com",
            client: Optional[httpx.Client] = None,
            timeout: float = 10.0,
    ) -> None:
        """Initialize the Brave Search client.

        Args:
            api_key (str): Brave Search API key.
            base_url (str): Base URL for the Brave Search API.
            client (Optional[httpx.Client]): Optional existing httpx client to reuse.
            timeout (float): Request timeout in seconds.

        Raises:
            ValueError: If api_key is empty or None.
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("api_key must be a non-empty string")

        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None  # Track if we created the client

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
        """Perform a web search using the Brave Search API.

        Args:
            query (str): Search query.
            count (int): Maximum number of results to return (default 5).
            offset (int): Offset for pagination (default 0).
            country (Optional[str]): Country code for results (e.g., 'US').
            language (Optional[str]): Language code for results (e.g., 'en').
            safesearch (Optional[str]): Safe search level ('off', 'moderate', 'strict').
            summary (bool): Whether to include summarizer data (default False).

        Returns:
            SearchResults: Normalized search results.

        Raises:
            BraveSearchError: On HTTP errors or JSON parsing failures.
        """
        url = f"{self.base_url}/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }

        params = {
            "q": query,
            "count": count,
            "offset": offset,
        }

        if country:
            params["country"] = country
        if language:
            params["language"] = language
        if safesearch:
            params["safesearch"] = safesearch
        if summary:
            params["summary"] = 1

        try:
            response = self._client.get(url, headers=headers, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise BraveSearchError(
                f"Brave API returned status {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.TimeoutException as e:
            raise BraveSearchError(f"Brave API request timed out: {e}") from e
        except httpx.RequestError as e:
            raise BraveSearchError(f"Request to Brave API failed: {e}") from e

        try:
            data = response.json()
        except ValueError as e:
            raise BraveSearchError(
                f"Failed to parse Brave API response as JSON: {e}"
            ) from e

        return self._parse_response(query, data)

    def _parse_response(self, query: str, data: dict[str, Any]) -> SearchResults:
        """Parse a Brave Search API response into a SearchResults model.

        Args:
            query (str): Original search query.
            data (dict): Raw JSON response data from Brave.

        Returns:
            SearchResults: Parsed and normalized search results.
        """
        results = []
        total = None
        summarizer_key = None
        error = None

        # Extract web search results
        if "web" in data and "results" in data["web"]:
            for item in data["web"]["results"]:
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source=item.get("domain", None),
                    rank=item.get("rank", None),
                    raw=item,
                )
                results.append(result)

            total = data["web"].get("count", None)
        else:
            # Valid JSON but missing web.results
            logger.warning(
                f"Brave Search API returned valid JSON but no web.results for query: {query}"
            )
            error = "No results found in Brave response"

        # Extract summarizer key if present
        if "summarizer" in data and data["summarizer"].get("key"):
            summarizer_key = data["summarizer"]["key"]

        return SearchResults(
            query=query,
            backend="brave",
            results=results,
            total=total,
            summarizer_key=summarizer_key,
            error=error,
            raw=data,
        )

    def __del__(self) -> None:
        """Clean up resources."""
        if getattr(self, "_owns_client", False):
            try:
                self._client.close()
            except Exception:
                pass


class SearxngSearchError(Exception):
    """Raised when a SearXNG request fails."""


class SearxngSearchClient:
    """HTTP client encapsulating SearXNG search requests."""

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
        if not base_url or not base_url.strip():
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
        """Execute a SearXNG search and normalize the response."""
        params: dict[str, Any] = {
            "q": query,
            "format": "json",
            "pageno": max(page, 1),
        }

        cats = categories or self.default_categories
        if cats:
            params["categories"] = ",".join(cats)

        lang = language or self.default_language
        if lang:
            params["language"] = lang

        tr = time_range or self.default_time_range
        if tr:
            params["time_range"] = tr

        headers = {
            "Accept": "application/json",
            "User-Agent": "web-search-agent/1.0 (https://github.com/wmclifford/ai-agent-mastery-course)",
        }

        url = f"{self.base_url}/search"

        try:
            response = self._client.get(url, params=params, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            response = exc.response
            status = getattr(response, "status_code", "unknown")
            text = getattr(response, "text", str(exc))
            raise SearxngSearchError(
                f"SearXNG returned status {status}: {text}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise SearxngSearchError(f"SearXNG request timed out: {exc}") from exc
        except httpx.RequestError as exc:
            raise SearxngSearchError(f"Request to SearXNG failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise SearxngSearchError(
                f"Failed to parse SearXNG JSON response: {exc}"
            ) from exc

        return self._parse_response(query=query, data=data, max_results=max_results)

    def _parse_response(
            self,
            *,
            query: str,
            data: dict[str, Any],
            max_results: int,
    ) -> SearchResults:
        raw_results = data.get("results")
        error: Optional[str] = None

        if not isinstance(raw_results, Iterable):
            logger.warning("SearXNG response missing 'results' iterable")
            raw_results = []
            error = "No results found in SearXNG response"
        else:
            raw_results = list(raw_results)

        results: list[SearchResult] = []

        for idx, item in enumerate(raw_results):
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("url") or ""
            url = item.get("url", "")
            snippet = item.get("content") or ""
            parsed_url = item.get("parsed_url") or {}
            source = item.get("source") or parsed_url.get("hostname")
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


def create_brave_search_tool(
        app_config: AppConfig,
) -> Callable[[str, int], SearchResults]:
    """Create a Brave search tool function for use with Pydantic AI.

    Args:
        app_config (AppConfig): Application configuration with Brave API key.

    Returns:
        Callable: A function that takes query and max_results and returns SearchResults.

    Raises:
        ValueError: If Brave API key is not configured.
    """
    if not app_config.brave or not app_config.brave.api_key:
        raise ValueError(
            "Brave API key not configured. Set BRAVE_API_KEY environment variable."
        )

    client = BraveSearchClient(api_key=app_config.brave.api_key)

    def brave_search(query: str, max_results: int = 5) -> SearchResults:
        """Execute a Brave web search.

        Args:
            query (str): Search query.
            max_results (int): Maximum number of results (default 5).

        Returns:
            SearchResults: Search results from Brave.
        """
        return client.search(query=query, count=max_results, summary=False)

    return brave_search


def create_searxng_search_tool(
        app_config: AppConfig,
) -> Callable[[str, int], SearchResults]:
    """Create a SearXNG search tool function for Pydantic AI."""
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
        """Execute a SearXNG search request."""
        return client.search(query=query, max_results=max_results)

    return searxng_search
