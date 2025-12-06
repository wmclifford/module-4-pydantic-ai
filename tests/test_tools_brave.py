"""Unit tests for the Brave search tool and BraveSearchClient.

Tests verify:
- Correct request construction (URL, headers, query parameters)
- Response parsing into SearchResult/SearchResults models
- Error handling for HTTP failures and malformed responses
- Behavior when Brave returns valid JSON without web.results
- Summary support and summarizer_key extraction
"""

from unittest.mock import Mock, patch

import httpx
import pytest

from web_search_agent.config import AppConfig, LLMConfig, BraveSearchConfig, SearXNGConfig
from web_search_agent.models import SearchResult, SearchResults
from web_search_agent.tools import (
    BraveSearchClient,
    BraveSearchError,
    create_brave_search_tool,
)


class TestBraveSearchClient:
    """Tests for BraveSearchClient HTTP client."""

    def test_init_with_valid_api_key(self):
        """Test client initialization with a valid API key."""
        client = BraveSearchClient(api_key="test-api-key")
        assert client.api_key == "test-api-key"
        assert client.base_url == "https://api.search.brave.com"
        assert client.timeout == 10.0

    def test_init_with_empty_api_key(self):
        """Test that client initialization fails with an empty API key."""
        with pytest.raises(ValueError, match="api_key must be a non-empty string"):
            BraveSearchClient(api_key="")

    def test_init_with_none_api_key(self):
        """Test that client initialization fails with None API key."""
        with pytest.raises(ValueError, match="api_key must be a non-empty string"):
            BraveSearchClient(api_key=None)  # type: ignore

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_happy_path(self, mock_get):
        """Test successful web search with valid Brave response."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Example 1",
                        "url": "https://example1.com",
                        "description": "This is example 1",
                        "domain": "example1.com",
                        "rank": 1,
                    },
                    {
                        "title": "Example 2",
                        "url": "https://example2.com",
                        "description": "This is example 2",
                        "domain": "example2.com",
                        "rank": 2,
                    },
                ],
                "count": 100,
            }
        }
        mock_get.return_value = mock_response

        client = BraveSearchClient(api_key="test-key")
        result = client.search(query="test query", count=5)

        # Verify request construction
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args.args[0] == "https://api.search.brave.com/res/v1/web/search"
        assert call_args.kwargs["headers"]["X-Subscription-Token"] == "test-key"
        assert call_args.kwargs["params"]["q"] == "test query"
        assert call_args.kwargs["params"]["count"] == 5

        # Verify result parsing
        assert isinstance(result, SearchResults)
        assert result.query == "test query"
        assert result.backend == "brave"
        assert len(result.results) == 2
        assert result.results[0].title == "Example 1"
        assert result.results[0].url == "https://example1.com"
        assert result.results[0].snippet == "This is example 1"
        assert result.results[0].source == "example1.com"
        assert result.total == 100

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_with_optional_parameters(self, mock_get):
        """Test search with optional country, language, and safesearch parameters."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {"web": {"results": [], "count": 0}}
        mock_get.return_value = mock_response

        client = BraveSearchClient(api_key="test-key")
        client.search(
            query="test",
            count=10,
            country="US",
            language="en",
            safesearch="strict",
        )

        call_args = mock_get.call_args
        params = call_args.kwargs["params"]
        assert params["country"] == "US"
        assert params["language"] == "en"
        assert params["safesearch"] == "strict"

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_with_summary_support(self, mock_get):
        """Test search with summary=True sends correct parameters."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {
            "web": {"results": [], "count": 0},
            "summarizer": {"key": "summary-key-123"},
        }
        mock_get.return_value = mock_response

        client = BraveSearchClient(api_key="test-key")
        result = client.search(query="test", summary=True)

        call_args = mock_get.call_args
        params = call_args.kwargs["params"]
        assert params["summary"] == 1

        # Verify summarizer_key extraction
        assert result.summarizer_key == "summary-key-123"

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_http_error(self, mock_get):
        """Test that HTTP errors raise BraveSearchError."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=Mock(), response=mock_response
        )
        mock_get.return_value = mock_response

        client = BraveSearchClient(api_key="bad-key")
        with pytest.raises(BraveSearchError, match="Brave API returned status 401"):
            client.search(query="test")

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_timeout_error(self, mock_get):
        """Test that timeout errors raise BraveSearchError."""
        mock_get.side_effect = httpx.TimeoutException("Request timed out")

        client = BraveSearchClient(api_key="test-key")
        with pytest.raises(BraveSearchError, match="request timed out"):
            client.search(query="test")

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_request_error(self, mock_get):
        """Test that network errors raise BraveSearchError."""
        mock_get.side_effect = httpx.RequestError("Network error")

        client = BraveSearchClient(api_key="test-key")
        with pytest.raises(BraveSearchError, match="Request to Brave API failed"):
            client.search(query="test")

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_json_parse_error(self, mock_get):
        """Test that JSON parsing errors raise BraveSearchError."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        client = BraveSearchClient(api_key="test-key")
        with pytest.raises(BraveSearchError, match="Failed to parse.*JSON"):
            client.search(query="test")

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_empty_results_structure(self, mock_get):
        """Test handling of valid JSON without web.results."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {"other": "data"}
        mock_get.return_value = mock_response

        client = BraveSearchClient(api_key="test-key")
        result = client.search(query="test")

        # Should return empty SearchResults with error set
        assert result.query == "test"
        assert result.backend == "brave"
        assert len(result.results) == 0
        assert result.error == "No results found in Brave response"
        assert result.raw == {"other": "data"}

    @patch("web_search_agent.tools.httpx.Client.get")
    def test_search_with_raw_data_preserved(self, mock_get):
        """Test that raw response data is preserved in SearchResults."""
        raw_response = {
            "web": {
                "results": [{"title": "Test", "url": "https://test.com"}],
                "count": 1,
            },
            "query": {"original": "test"},
        }
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = raw_response
        mock_get.return_value = mock_response

        client = BraveSearchClient(api_key="test-key")
        result = client.search(query="test")

        assert result.raw == raw_response


class TestBraveSearchTool:
    """Tests for the Brave search tool factory and integration."""

    def test_create_brave_search_tool_valid_config(self):
        """Test creating a Brave search tool with valid configuration."""
        app_config = AppConfig(
            llm=LLMConfig(provider="openai", api_key="test-key", choice="gpt-4"),
            brave=BraveSearchConfig(api_key="brave-key"),
            searxng=SearXNGConfig(base_url=None),
        )

        tool = create_brave_search_tool(app_config)

        # Verify tool is callable
        assert callable(tool)

    def test_create_brave_search_tool_missing_api_key(self):
        """Test that creating tool fails without Brave API key."""
        app_config = AppConfig(
            llm=LLMConfig(provider="openai", api_key="test-key", choice="gpt-4"),
            brave=BraveSearchConfig(api_key=None),
            searxng=SearXNGConfig(base_url="https://example.com"),
        )

        with pytest.raises(ValueError, match="Brave API key not configured"):
            create_brave_search_tool(app_config)

    def test_create_brave_search_tool_empty_api_key(self):
        """Test that creating tool fails with empty Brave API key."""
        with pytest.raises(ValueError, match="Brave Search API key cannot be an empty string"):
            BraveSearchConfig(api_key="")

    @patch("web_search_agent.tools.BraveSearchClient.search")
    def test_brave_search_tool_callable(self, mock_search):
        """Test calling the created Brave search tool."""
        mock_search.return_value = SearchResults(
            query="test",
            backend="brave",
            results=[],
            total=0,
        )

        app_config = AppConfig(
            llm=LLMConfig(provider="openai", api_key="test-key", choice="gpt-4"),
            brave=BraveSearchConfig(api_key="brave-key"),
            searxng=SearXNGConfig(base_url=None),
        )

        tool = create_brave_search_tool(app_config)
        result = tool("test query", max_results=5)

        # Verify tool calls client.search with correct parameters
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args.kwargs["query"] == "test query"
        assert call_args.kwargs["count"] == 5
        assert call_args.kwargs["summary"] is False

        # Verify result is SearchResults
        assert isinstance(result, SearchResults)
        assert result.query == "test"


class TestSearchResults:
    """Tests for SearchResults and SearchResult models."""

    def test_search_result_model_valid(self):
        """Test creating a valid SearchResult model."""
        result = SearchResult(
            title="Test",
            url="https://test.com",
            snippet="This is a test",
            source="test.com",
            rank=1,
        )

        assert result.title == "Test"
        assert result.url == "https://test.com"
        assert result.snippet == "This is a test"
        assert result.source == "test.com"
        assert result.rank == 1

    def test_search_result_model_minimal(self):
        """Test creating SearchResult with only required fields."""
        result = SearchResult(
            title="Test",
            url="https://test.com",
            snippet="This is a test",
        )

        assert result.title == "Test"
        assert result.source is None
        assert result.rank is None
        assert result.raw is None

    def test_search_results_model_valid(self):
        """Test creating a valid SearchResults model."""
        results = SearchResults(
            query="test",
            backend="brave",
            results=[
                SearchResult(title="T1", url="https://t1.com", snippet="S1"),
                SearchResult(title="T2", url="https://t2.com", snippet="S2"),
            ],
            total=100,
            summarizer_key="key-123",
        )

        assert results.query == "test"
        assert results.backend == "brave"
        assert len(results.results) == 2
        assert results.total == 100
        assert results.summarizer_key == "key-123"

    def test_search_results_model_empty(self):
        """Test creating SearchResults with no results."""
        results = SearchResults(
            query="test",
            backend="brave",
            error="No results",
        )

        assert results.query == "test"
        assert len(results.results) == 0
        assert results.error == "No results"
