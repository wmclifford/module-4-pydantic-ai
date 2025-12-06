"""Placeholder module for Brave and SearXNG tool implementations.

This module will contain tool functions for interacting with various
search engines like Brave Search API and SearXNG instances.
"""

import logging
from typing import Any, Callable, Optional

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
