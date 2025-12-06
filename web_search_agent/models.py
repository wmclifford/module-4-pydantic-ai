"""Placeholder data models for search results and related entities.

This module will define Pydantic models for representing search results,
web pages, and other data structures used by the web search agent.
"""

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Normalized representation of a single search result.

    This model is backend-agnostic and can represent results from any
    search backend (Brave, SearXNG, etc.).
    """

    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the search result")
    snippet: str = Field(..., description="Text snippet from the search result")
    source: Optional[str] = Field(
        default=None, description="Source or domain of the result"
    )
    rank: Optional[int] = Field(
        default=None, description="Rank or position of the result"
    )
    raw: Optional[dict[str, Any]] = Field(
        default=None, description="Raw data from the backend"
    )


class SearchResults(BaseModel):
    """Container for normalized search results from any backend.

    This model aggregates search results with metadata and supports
    multiple backends through a single, consistent interface.
    """

    query: str = Field(..., description="Original search query")
    backend: str = Field(
        ..., description="Name of the search backend (e.g., 'brave', 'searxng')"
    )
    results: List[SearchResult] = Field(
        default_factory=list, description="List of search results"
    )
    total: Optional[int] = Field(
        default=None, description="Total number of results available"
    )
    summarizer_key: Optional[str] = Field(
        default=None, description="Optional summarizer key from backend"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if the search failed"
    )
    raw: Optional[dict[str, Any]] = Field(
        default=None, description="Raw response data from the backend"
    )
