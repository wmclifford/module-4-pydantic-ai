"""Unit tests for the SearXNG search client and tool factory."""

from unittest.mock import Mock, patch

import httpx
import pytest

from web_search_agent.config import (
    AppConfig,
    BraveSearchConfig,
    LLMConfig,
    SearXNGConfig,
)
from web_search_agent.models import SearchResult, SearchResults
from web_search_agent.tools import (
    SearxngSearchClient,
    SearxngSearchError,
    create_searxng_search_tool,
)


def make_app_config(base_url: str | None = "https://example.com") -> AppConfig:
    """Helper that returns a valid AppConfig with optional SearXNG base URL."""
    return AppConfig(
        llm=LLMConfig(provider="openai", api_key="llm-key", choice="gpt-4"),
        brave=BraveSearchConfig(api_key="brave-key"),
        searxng=SearXNGConfig(base_url=base_url),
    )


class TestSearxngSearchClient:
    """Tests covering the HTTP client that talks to SearXNG."""

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_happy_path(self, mock_get):
        """It builds the expected request and parses the JSON into SearchResults."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "results": [
                {"title": "A", "url": "https://a", "content": "A content"},
                {"title": "B", "url": "https://b", "content": "B content"},
            ],
            "number_of_results": 10,
        }
        mock_get.return_value = mock_response

        client = SearxngSearchClient(base_url="https://searxng.example.com")
        result = client.search(
            "query",
            max_results=1,
            page=2,
            categories=["general", "news"],
            language="en",
            time_range="week",
        )

        call_args = mock_get.call_args.kwargs
        assert call_args["params"]["q"] == "query"
        assert call_args["params"]["pageno"] == 2
        assert "general,news" in call_args["params"]["categories"]
        assert call_args["params"]["language"] == "en"
        assert call_args["params"]["time_range"] == "week"

        assert result.backend == "searxng"
        assert result.total == 10
        assert len(result.results) == 1  # max_results trims the list
        assert result.results[0].title == "A"

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_http_error(self, mock_get):
        """HTTP status errors from httpx are wrapped in our error type."""
        response = Mock(spec=httpx.Response)
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=Mock(), response=response
        )
        mock_get.return_value = response

        client = SearxngSearchClient(base_url="https://example.com")
        with pytest.raises(SearxngSearchError, match="SearXNG returned status"):
            client.search("query")

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_timeout(self, mock_get):
        """Timeout exceptions are surfaced through SearxngSearchError."""
        mock_get.side_effect = httpx.TimeoutException("timed out")

        client = SearxngSearchClient(base_url="https://example.com")
        with pytest.raises(SearxngSearchError, match="timed out"):
            client.search("query")

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_parse_failure(self, mock_get):
        """JSON parse failures are wrapped in SearxngSearchError."""
        response = Mock(spec=httpx.Response)
        response.raise_for_status = Mock()
        response.json.side_effect = ValueError("bad json")
        mock_get.return_value = response

        client = SearxngSearchClient(base_url="https://example.com")
        with pytest.raises(SearxngSearchError, match="Failed to parse"):
            client.search("query")

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_reports_missing_results(self, mock_get):
        """When the response omits results, the SearchResults.error message is populated."""
        response = Mock(spec=httpx.Response)
        response.raise_for_status = Mock()
        response.json.return_value = {}
        mock_get.return_value = response

        client = SearxngSearchClient(base_url="https://example.com")
        result = client.search("query")

        assert result.error == "No results found in SearXNG response"
        assert result.backend == "searxng"


class TestSearxngSearchToolFactory:
    """Ensure the SearXNG tool factory wires the client correctly."""

    @patch("web_search_agent.tools.SearxngSearchClient.search")
    def test_tool_calls_client(self, mock_search):
        mock_search.return_value = SearchResults(
            query="test",
            backend="searxng",
            results=[SearchResult(title="x", url="https://x", snippet="snip")],
        )

        tool = create_searxng_search_tool(make_app_config())
        result = tool("query", max_results=3)

        mock_search.assert_called_once_with(query="query", max_results=3)
        assert result.backend == "searxng"

    def test_tool_requires_base_url(self):
        invalid_config = make_app_config(base_url=None)
        with pytest.raises(ValueError, match="SearXNG base URL not configured"):
            create_searxng_search_tool(invalid_config)
