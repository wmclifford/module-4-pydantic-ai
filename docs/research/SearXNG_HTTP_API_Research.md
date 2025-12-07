# SearXNG HTTP API Research

This document summarizes research into the SearXNG HTTP API, focusing on
implementing a robust backend Python client that normalizes results into
Pydantic models suitable for use by the web_search_agent project.

## 1. Endpoints and HTTP Methods

### 1.1 Primary search endpoints

Most SearXNG instances expose search functionality via:

- `GET /search`  (recommended API-style endpoint)
- `GET /`        (HTML search page, can also respond with JSON when
  `format=json` is provided if configured)

For backend integrations, `GET /search` with `format=json` is the most
predictable choice:

- Example:

  ```http
  GET https://searxng.example.com/search?q=python&format=json
  ```

SearXNG also supports `POST` for search, but `GET` is more common for simple
web-search tools.

### 1.2 JSON format

To receive JSON instead of HTML, the query must include:

- `format=json`

Some instances disable JSON responses by default. In that case:

- The server may return `403 Forbidden` or an HTML response even when
  `format=json` is requested.
- JSON support must be enabled in `settings.yml` on the SearXNG server.

## 2. Common Query Parameters

The following query parameters are commonly supported by SearXNG when
performing a web search:

- `q` (string, required)
  - The search query string.

- `format` (string, required for JSON)
  - Use `format=json` to request a JSON response.

- `pageno` (integer, optional)
  - 1-based page number for pagination.
  - Example: `pageno=1` (default), `pageno=2` for the second page.

- `categories` (string, optional)
  - Comma-separated list of category names.
  - Common categories include `general`, `news`, `images`, `videos`, `it`,
    `science`, etc.
  - Example: `categories=general` or `categories=general,news`.

- `language` (string, optional)
  - Language code used to bias or filter results, e.g. `en`, `de`, `fr`.

- `time_range` (string, optional)
  - Restricts results to a recent time window.
  - Values vary by configuration, but common options include:
    - `day`, `week`, `month`, `year`.

Other, more advanced parameters exist (e.g. `engines`, `safesearch`), but the
above are sufficient for a first-pass backend tool.

## 3. JSON Response Structure

When `format=json` is enabled and requested, the SearXNG response typically
has the following high-level structure:

```json
{
  "query": "python",
  "number_of_results": 1234,
  "results": [
    {
      "title": "Example result title",
      "url": "https://example.com/article",
      "content": "Short summary or snippet of the page...",
      "category": "general",
      "engine": "duckduckgo",
      "engines": [
        "duckduckgo"
      ],
      "source": "example.com",
      "score": 5.73,
      "thumbnail": "https://example.com/thumb.jpg",
      "parsed_url": {
        "scheme": "https",
        "netloc": "example.com",
        "hostname": "example.com",
        "path": "/article",
        "query": "",
        "fragment": ""
      },
      "position": 1,
      "id": "some-id",
      "publishedDate": "2024-01-01T12:00:00Z"
    }
  ],
  "answers": [],
  "corrections": [],
  "infoboxes": [],
  "suggestions": [],
  "unresponsive_engines": []
}
```

### 3.1 Top-level fields

- `query`
  - Often a string or an object containing the original query. Implementations
    should not rely heavily on its exact shape; the client can instead track
    the original query separately.

- `number_of_results`
  - Intended to report the total number of results.
  - **Gotcha:** in practice this field can be inaccurate or always `0` even
    when `results` contains entries. A robust client should not rely solely on
    this value.

- `results`
  - List of individual result objects (see below).

- `answers`, `corrections`, `infoboxes`, `suggestions`,
  `unresponsive_engines`
  - Optional arrays providing richer metadata or hints. For a minimal search
    tool, they can be passed through in the `raw` field of the normalized
    model and ignored at the top level.

### 3.2 Result objects

Common fields in each `results` element include:

- `title` (string)
  - Human-readable title of the result.

- `url` (string)
  - Target URL of the result.

- `content` (string)
  - Short description or snippet of the result.

- `category` (string)
  - Category of the result, e.g. `general`, `news`, `images`.

- `engine` (string)
  - Name of the engine that produced the result (e.g. `duckduckgo`).

- `engines` (array of strings, optional)
  - Some configurations include a list of contributing engines.

- `source` (string, optional)
  - Usually a domain-like string (e.g. `example.com`).

- `score` (number, optional)
  - Relevance score assigned by SearXNG.

- `thumbnail` (string, optional)
  - URL to a thumbnail image, if available.

- `parsed_url` (object, optional)
  - Structured representation of the URL, often including `hostname`.

- `position` (integer, optional)
  - 1-based rank or position in the result list.

- `publishedDate` / `published_date` (string, optional)
  - Publication timestamp, if known.

A robust client should:

- Treat any of these fields as optional.
- Use sensible fallbacks (e.g. fall back to `url` when `title` is missing).
- Avoid strict assumptions about case or presence of optional fields.

## 4. Pagination Semantics

Pagination is controlled via the `pageno` parameter:

- `pageno=1` is the first page (default in most configurations).
- `pageno=2` is the second page, and so on.

There is no explicit `page_size` parameter in the public HTTP API; the number
of results per page is typically configured on the SearXNG instance itself.

A backend client should:

- Always send `pageno >= 1`.
- Expose `page` as an integer parameter at the client level, passing it
  through to `pageno`.
- Optionally apply a client-side `max_results` limit by slicing the
  normalized result list after parsing.

## 5. Error Responses and Gotchas

### 5.1 Common HTTP status codes

- `403 Forbidden`
  - JSON disabled or restricted.
  - Bot detection or rate limiting triggered.

- `429 Too Many Requests`
  - Rate limiter active on public instances.

- `500 Internal Server Error`
  - Engine misconfiguration or timeout on the SearXNG side.

### 5.2 Practical gotchas

- **JSON not enabled:**
  - Some instances are configured without JSON output. The client may receive
    HTML or a `403` even when requesting `format=json`.
  - Mitigation: treat non-JSON responses or unexpected content types as
    errors; surface clear messages to the caller.

- **number_of_results reliability:**
  - This field can be 0 or inaccurate even when results are present.
  - Mitigation: use `len(results)` as a fallback or primary source for
    reporting the total.

- **Engine and category availability:**
  - Not all instances enable the same engines or categories.
  - Some combinations of categories or time ranges may trigger errors or yield
    no results.

- **Rate limiting and bot detection:**
  - Public instances often rate-limit requests and may block clients with
    generic or missing User-Agent headers.
  - Mitigation: send a realistic User-Agent and be prepared to handle 429/403
    with backoff or useful error messages.

## 6. Pydantic Model Design Considerations

For the `web_search_agent` project, a minimal, backend-agnostic model is
preferred. The recommended pattern is:

- Keep top-level `SearchResult` fields minimal:
  - `title`, `url`, `snippet`, `source`, `rank`.
- Store the full backend-specific payload from SearXNG in a `raw` dictionary.
- Avoid introducing SearXNG-specific attributes (e.g. `category`, `score`,
  `engine`) as first-class fields unless there is a strong cross-backend
  need.

This design:

- Keeps the public model stable and simple.
- Allows backends like Brave and SearXNG to share the same normalized model.
- Preserves advanced data in `raw` for debugging or future features.

## 7. Client-side Parsing Strategy

A robust Python client should:

1. Request JSON via `format=json` and handle non-JSON responses as errors.
2. Parse the top-level `results` list; if it is missing or not a list, treat
   the response as "no results" and set a helpful error message.
3. For each result:
  - Use `title` or fall back to `url` when missing.
  - Use `content` as the snippet; fall back to an empty string when missing.
  - Determine `source` from `source` or from
    `parsed_url.hostname` when available.
  - Compute `rank` from `position` if present, otherwise use a 1-based index.
  - Store the full result object in `raw`.
4. Compute `total` from `number_of_results` when it is a positive integer;
   otherwise use `len(results)`.
5. Preserve the full top-level JSON into a `raw` field on the aggregate
   results model.

## 8. Defensive Strategies for Self-hosted Instances

When talking to a self-hosted SearXNG instance, a client should:

- Use a configurable base URL (e.g. `SEARXNG_BASE_URL`).
- Default the endpoint to `/search` and allow overriding in configuration if
  needed.
- Provide configurable defaults for:
  - `timeout` (e.g. 10 seconds).
  - `default_categories` (e.g. `['general']`).
  - `default_language` (optional).
  - `default_time_range` (optional).
- Send a realistic User-Agent header.
- Handle network errors, timeouts, and unexpected responses gracefully, using
  clear exception types and messages.

These patterns map directly into the planned `SearxngSearchClient` and
associated configuration in the `web_search_agent` package.

