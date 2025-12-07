# SearXNG HTTP API Research Summary

*Research Date: December 6, 2025*

## Question

What is the SearXNG HTTP API interface, including endpoints, parameters, response formats, JSON structure, pagination,
error handling, and self-hosted instance considerations for building a robust Python HTTP client?

---

## Key Findings

### 1. HTTP Endpoints and Query Parameters

#### Endpoints

- **`GET /` or `GET /search`** — Both endpoints are available and equivalent
- **`POST /` or `POST /search`** — POST method also supported
- **Base URL Format:** `http://localhost:8080/search` (or your instance URL)

#### Query Parameters (GET/POST)

| Parameter            | Type    | Default          | Values/Notes                                                                                                                |
|----------------------|---------|------------------|-----------------------------------------------------------------------------------------------------------------------------|
| `q`                  | string  | **required**     | Search query; supports engine-specific syntax (e.g., `site:github.com`)                                                     |
| `categories`         | string  | —                | Comma-separated list (e.g., `general,web,images`); depends on instance configuration                                        |
| `engines`            | string  | all enabled      | Comma-separated list of search engines to use (e.g., `google,bing,duckduckgo`)                                              |
| `language`           | string  | instance default | Language code (e.g., `en`, `de`, `fr`); check instance preferences for available codes                                      |
| `pageno`             | integer | 1                | Page number for pagination (1-indexed)                                                                                      |
| `time_range`         | string  | —                | Values: `day`, `month`, `year`; only if engine supports time-range filtering                                                |
| `format`             | string  | `html`           | Output format: `json`, `csv`, `rss`, `html`; must be enabled in `settings.yml`                                              |
| `results_on_new_tab` | integer | 0                | `0` or `1`; open results in new tab (UI preference)                                                                         |
| `image_proxy`        | boolean | server default   | `True` or `False`; proxy image results through SearXNG                                                                      |
| `autocomplete`       | string  | instance default | Autocomplete provider: `google`, `dbpedia`, `duckduckgo`, `mwmbl`, `startpage`, `wikipedia`, `stract`, `swisscows`, `qwant` |
| `safesearch`         | integer | instance default | Filter level: `0` (off), `1` (moderate), `2` (strict)                                                                       |
| `theme`              | string  | `simple`         | UI theme (depends on instance configuration)                                                                                |
| `enabled_plugins`    | string  | instance default | Comma-separated list of plugins                                                                                             |
| `disabled_plugins`   | string  | instance default | Comma-separated list of plugins to disable                                                                                  |
| `enabled_engines`    | string  | all              | Explicitly enable engines by name                                                                                           |
| `disabled_engines`   | string  | none             | Explicitly disable engines by name                                                                                          |

**Example Request:**

```
GET /search?q=python+programming&format=json&categories=general&language=en&pageno=1&engines=google,bing&time_range=month&safesearch=1
```

---

### 2. Response Formats

SearXNG supports multiple output formats. To use JSON, the instance administrator must enable it in `settings.yml`:

```yaml
search:
  formats:
    - html
    - json
    # optionally: csv, rss
```

**Supported Formats:**

- `html` — Default; HTML rendered page
- `json` — Machine-readable JSON object (see section 3 for schema)
- `csv` — Comma-separated values
- `rss` — RSS feed format

---

### 3. JSON Response Structure

#### Top-Level Object

```json
{
  "query": "python programming",
  "number_of_results": 0,
  "results": [
    ...
  ],
  "answers": [
    ...
  ],
  "corrections": [
    ...
  ],
  "infoboxes": [
    ...
  ],
  "suggestions": [
    ...
  ],
  "unresponsive_engines": [
    ...
  ]
}
```

**Top-Level Fields:**

| Field                  | Type    | Notes                                                                                                                            |
|------------------------|---------|----------------------------------------------------------------------------------------------------------------------------------|
| `query`                | string  | The search query as submitted                                                                                                    |
| `number_of_results`    | integer | **Known Issue:** Often returns 0 even when results are present (documented as a bug); do not rely on this field for result count |
| `results`              | array   | Main search results; see below for result object schema                                                                          |
| `answers`              | array   | Short answer snippets from answerers (Wikipedia excerpts, weather, translations, etc.)                                           |
| `corrections`          | array   | Spelling corrections or alternative queries suggested by engines                                                                 |
| `infoboxes`            | array   | Rich information boxes (e.g., Wikipedia infobox data, maps)                                                                      |
| `suggestions`          | array   | Alternative search term suggestions                                                                                              |
| `unresponsive_engines` | array   | Engines that timed out or failed during this search                                                                              |

#### Result Object Schema

Each result in the `results` array has the following structure:

```json
{
  "category": "general",
  "content": "Short snippet or description of the page...",
  "engine": "google",
  "engines": [
    "google",
    "bing"
  ],
  "parsed_url": [
    "https",
    "example.com",
    "/path/to/page",
    "",
    "",
    ""
  ],
  "positions": [
    1,
    2
  ],
  "score": 2.5,
  "template": "default.html",
  "title": "Example Page Title",
  "url": "https://example.com/path/to/page",
  "publishedDate": "2024-01-15",
  "thumbnail": "https://example.com/thumb.jpg",
  "iframe_src": null,
  "img_src": null,
  "author": null,
  "metadata": null
}
```

**Result Field Reference:**

| Field           | Type        | Optional | Notes                                                                                                  |
|-----------------|-------------|----------|--------------------------------------------------------------------------------------------------------|
| `title`         | string      | No       | Page title or headline                                                                                 |
| `url`           | string      | No       | Full URL to the result                                                                                 |
| `content`       | string      | No       | Snippet or summary (truncated)                                                                         |
| `category`      | string      | No       | Result category: `general`, `images`, `videos`, `news`, `maps`, `music`, `files`, `social media`, etc. |
| `engine`        | string      | No       | Primary engine providing this result                                                                   |
| `engines`       | array       | No       | List of engines that returned this result                                                              |
| `parsed_url`    | array       | No       | URL parsed into components: `[scheme, domain, path, query, fragment, ...]`                             |
| `positions`     | array       | No       | Ranking positions within each contributing engine (1-indexed)                                          |
| `score`         | float       | No       | Aggregate relevance score (higher = better; exact calculation varies)                                  |
| `template`      | string      | No       | Internal template used to render the result (typically `default.html`)                                 |
| `publishedDate` | string/null | Yes      | ISO-8601 date when the page was published/updated (may be null)                                        |
| `thumbnail`     | string/null | Yes      | URL to thumbnail or image associated with the result                                                   |
| `iframe_src`    | string/null | Yes      | URL for embedded content (rare)                                                                        |
| `img_src`       | string/null | Yes      | Image source URL (for image results)                                                                   |
| `author`        | string/null | Yes      | Author name (if available)                                                                             |
| `metadata`      | string/null | Yes      | Extra metadata (context-dependent)                                                                     |

**Complete Example JSON Response:**

```json
{
  "query": "artificial intelligence",
  "number_of_results": 0,
  "results": [
    {
      "title": "Artificial Intelligence - Wikipedia",
      "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
      "content": "Artificial intelligence (AI) is intelligence demonstrated by machines...",
      "category": "general",
      "engine": "google",
      "engines": [
        "google",
        "duckduckgo"
      ],
      "parsed_url": [
        "https",
        "en.wikipedia.org",
        "/wiki/Artificial_intelligence",
        "",
        "",
        ""
      ],
      "positions": [
        1,
        1
      ],
      "score": 2.0,
      "template": "default.html",
      "publishedDate": "2024-01-10",
      "thumbnail": null
    },
    {
      "title": "What is Artificial Intelligence (AI)? | IBM",
      "url": "https://www.ibm.com/cloud/learn/what-is-artificial-intelligence",
      "content": "Artificial intelligence leverages computers and machines to mimic problem-solving...",
      "category": "general",
      "engine": "bing",
      "engines": [
        "bing"
      ],
      "parsed_url": [
        "https",
        "www.ibm.com",
        "/cloud/learn/what-is-artificial-intelligence",
        "",
        "",
        ""
      ],
      "positions": [
        2
      ],
      "score": 1.8,
      "template": "default.html",
      "publishedDate": "2023-11-15",
      "thumbnail": "https://www.ibm.com/ai/thumb.jpg"
    }
  ],
  "answers": [],
  "corrections": [],
  "infoboxes": [],
  "suggestions": [],
  "unresponsive_engines": []
}
```

---

### 4. Pagination

**Mechanism:** Page-number based (not cursor/offset based)

**Parameters:**

- `pageno` — Page number (integer, 1-indexed; default: 1)
  - Example: `pageno=1`, `pageno=2`, `pageno=3`, etc.

**Behavior:**

- No explicit `page_size` or `limit` parameter in the API
- Results per page is configured by the SearXNG instance administrator (default is typically 10–20 results)
- Invalid page numbers may return an empty result set, or some engines may return the first page as a fallback (
  rate-limiting measure)

**Recommendation for Client:**

```python
# Defensive pagination logic
if not results and pageno > 1:
  # Could be rate limiting or invalid page; try with pageno=1
  pass
```

---

### 5. Error Responses and HTTP Status Codes

#### Common HTTP Status Codes

| Status  | Meaning               | Response Body                   | Reason                                                                    |
|---------|-----------------------|---------------------------------|---------------------------------------------------------------------------|
| **200** | OK                    | Valid JSON/HTML                 | Success                                                                   |
| **400** | Bad Request           | HTML error page                 | Malformed query parameters                                                |
| **403** | Forbidden             | HTML error page (often)         | See details below                                                         |
| **429** | Too Many Requests     | HTML or plain text              | Rate limiting active; see below                                           |
| **500** | Internal Server Error | HTML error page or partial JSON | Engine crash or misconfiguration (e.g., category not supported by engine) |
| **503** | Service Unavailable   | HTML error page                 | SearXNG instance temporarily down                                         |

#### 403 Forbidden — Common Causes

**1. JSON format not enabled:**

- **Cause:** Instance administrator has not added `json` to `search.formats` in `settings.yml`
- **Response:** HTML error page: `403 Forbidden: You don't have permission to access the requested resource`
- **Fix:** Enable JSON in settings or contact administrator

**2. Rate limiting (rate limiter enabled):**

- **Cause:** Public instances often enable request rate limiting to prevent bot abuse
- **Response:** HTML or JSON error indicating too many requests
- **Retry-After header:** May be present; check for retry timing
- **Fix:** Self-host an instance with `server.limiter: false` in `settings.yml`, or add delays between requests

**3. Bot blocker active:**

- **Cause:** Instance may block requests that appear automated (missing or suspicious User-Agent header)
- **Response:** 403 Forbidden
- **Fix:** Include a realistic User-Agent header in requests (see example below)

#### 429 Too Many Requests

- **Cause:** Rate limiter or proxy (nginx/Cloudflare) blocking excessive requests
- **Response:** Plain text or HTML error
- **Rate Limits (typical):**
  - Public instances: 2–5 requests per second per IP
  - Self-hosted: Configurable or none
- **Retry-After header:** May be present; respect it
- **Mitigation:**
  - Add `Retry-After` header handling
  - Implement exponential backoff
  - Space requests by ~1 second on public instances

#### 500 Internal Server Error

**Common causes:**

- Engine configuration error (e.g., querying with an unsupported category for the selected engine)
- External engine timeout or failure (unresponsive search service)
- Incompatible category/engine combination (e.g., `categories=videos&format=json` may fail on older versions)

**Response:** Partial JSON or HTML error page

---

### 6. Self-Hosted Instance Gotchas

#### Configuration-Dependent Behavior

1. **JSON Format Disabled by Default**

- **Issue:** Instances ship with only HTML format enabled
- **Solution:** Add to `settings.yml`:
  ```yaml
  search:
    formats:
      - html
      - json
  ```
- **Restart required:** Yes

2. **Rate Limiting and Bot Blocker**

- **Public instances:** Usually have rate limiting + bot blocker active
- **Self-hosted:** Disabled by default, but configurable:
  ```yaml
  server:
    limiter: false  # Disable rate limiter
  ```
- **Limiter configuration (if enabled):**
  ```yaml
  limiter:
    enabled: true
    # Requests per second per IP
    requests: 2
    # Ban window (seconds)
    ban_time: 60
  ```
- **Bot detection:** Headers matter:
  - Missing `User-Agent` → often flagged as bot
  - Use realistic UA: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36`

3. **CORS Headers (Self-Hosted Behind Proxy)**

- **Issue:** Browsers or cross-origin requests may fail if CORS headers are missing
- **Note:** SearXNG does not set CORS headers by default
- **Solution (nginx reverse proxy example):**
  ```nginx
  location / {
      add_header 'Access-Control-Allow-Origin' '*';
      add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
      add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type';
      proxy_pass http://searxng_backend;
  }
  ```

4. **Instance-Specific Engine Availability**

- **Issue:** Different instances have different engines enabled
- **Risk:** Requesting an engine not available on that instance may fail with 500
- **Solution:**
  - Query `/config` endpoint to discover available engines (see Admin API)
  - Or: Gracefully handle engine errors and retry without that engine
- **Example:**
  ```
  GET /config
  Returns: { "engines": [...], "categories": [...] }
  ```

5. **Empty Results Due to Timeout**

- **Issue:** `number_of_results` returns 0, but results array is non-empty (documented bug)
- **Workaround:** Always check the `results` array length, not the `number_of_results` field
- **Risk:** Some engines timeout; SearXNG returns partial results from responsive engines
- **Mitigation:** No perfect fix; accept partial results or add engine-specific retries

6. **Category/Engine Compatibility**

- **Issue:** Not all categories work with all engines
- **Example:** `format=json&categories=videos` fails on some instances
- **Solution:**
  - Start with `categories=general` for compatibility
  - Use instance preferences page to check engine/category support
  - Catch HTTP 500 and retry with fewer/different engines

7. **Language and Locale Variability**

- **Issue:** Language codes differ across engines; instance may not support all codes
- **Solution:**
  - Use `language=all` to query all engines in their default language
  - Use `language=en` for English-specific results (most instances support)
  - Check instance preferences for supported language codes

---

## Recommendations for Pydantic Model Design

### 1. Core Models

```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


class SearchResult(BaseModel):
  """Single search result."""
  title: str
  url: HttpUrl
  content: str
  category: str
  engine: str
  engines: List[str]
  parsed_url: List[str]
  positions: List[int]
  score: float
  template: str
  published_date: Optional[str] = Field(None, alias="publishedDate")
  thumbnail: Optional[HttpUrl] = None
  iframe_src: Optional[HttpUrl] = Field(None, alias="iframe_src")
  author: Optional[str] = None
  metadata: Optional[str] = None

  class Config:
    populate_by_name = True  # Allow both snake_case and camelCase


class SearXNGResponse(BaseModel):
  """Top-level SearXNG API response."""
  query: str
  number_of_results: int  # Note: Often 0; check results array length instead
  results: List[SearchResult] = Field(default_factory=list)
  answers: List[dict] = Field(default_factory=list)
  corrections: List[dict] = Field(default_factory=list)
  infoboxes: List[dict] = Field(default_factory=list)
  suggestions: List[dict] = Field(default_factory=list)
  unresponsive_engines: List[str] = Field(default_factory=list)

  @property
  def actual_result_count(self) -> int:
    """Returns actual count of results (workaround for number_of_results bug)."""
    return len(self.results)
```

### 2. Request/Configuration Models

```python
from enum import Enum
from typing import Optional, List


class TimeRange(str, Enum):
  DAY = "day"
  MONTH = "month"
  YEAR = "year"


class SafeSearch(int, Enum):
  OFF = 0
  MODERATE = 1
  STRICT = 2


class SearXNGRequest(BaseModel):
  """SearXNG search request parameters."""
  q: str
  categories: Optional[str] = None
  engines: Optional[str] = None
  language: str = "en"
  pageno: int = Field(default=1, ge=1)
  time_range: Optional[TimeRange] = None
  format: str = "json"
  safesearch: SafeSearch = SafeSearch.OFF
  autocomplete: Optional[str] = None
  image_proxy: Optional[bool] = None
  results_on_new_tab: int = Field(default=0, ge=0, le=1)

  class Config:
    use_enum_values = True
```

### 3. Error Handling

```python
class SearXNGError(Exception):
  """Base exception for SearXNG client."""
  pass


class RateLimitError(SearXNGError):
  """Rate limit (429) encountered."""
  retry_after: Optional[int] = None


class JSONNotEnabledError(SearXNGError):
  """JSON format not enabled on instance (403)."""
  pass


class EngineError(SearXNGError):
  """Engine-specific error (500)."""
  engine: Optional[str] = None
```

---

## Variability Between Instances (Defensive Handlin g)| Aspect | Ty          pical Variation | Client Strategy |

|--------|------------------|-----------------|
| ** Rate limits** | 0 (di sabled) to 5 req/sec | Implement adaptive backoff; catch 429 with Retry-After |
| **Enable d engines** | Var ies widely | Query `/config` on startup; gracefully degrade if engine unavailable |
| **JSON format** | Enabled/disable d | Test with `format=json` on first request; fall back to CSV if needed |
| **Supported categories** | Subset of: general, images, vi deos, news, music, maps, etc. | Default to `general`; catch
500 errors from unsupported categories |
| **Supported languag es** | Usually EN + fe w others | Use `language=en` or `language=all`; handle 400 for invalid
codes |
| **Pagination limit** | Typically 10 –50 pages max | Implement page limit checks; gracefully handle empty results |
| **Response latency** | 100ms–5s depending on engines | Set HTTP timeouts to 10–30 seconds; handle partial/timeout
results |

---

## Example HTTP Request & Response

### Request

```bash
curl -s "http://localhost:8080/search" \
  -G \
  --data-urlencode "q=machine learning" \
  -d "format=json" \
  -d "language=en" \
  -d "pageno=1" \
  -d "engines=google,bing" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Accept: application/json"
```

### Response (Truncated)

```json
{
  "query": "machine learning",
  "number_of_results": 0,
  "results": [
    {
      "title": "Machine Learning - Wikipedia",
      "url": "https://en.wikipedia.org/wiki/Machine_learning",
      "content": "Machine learning is a subset of artificial intelligence...",
      "category": "general",
      "engine": "google",
      "engines": [
        "google",
        "bing"
      ],
      "parsed_url": [
        "https",
        "en.wikipedia.org",
        "/wiki/Machine_learning",
        "",
        "",
        ""
      ],
      "positions": [
        1,
        2
      ],
      "score": 2.0,
      "template": "default.html",
      "publishedDate": "2024-02-01",
      "thumbnail": null
    }
  ],
  "answers": [],
  "corrections": [],
  "infoboxes": [],
  "suggestions": [],
  "unresponsive_engines": []
}
```

---

## Summary: Quick Reference for Backend Python Client

### Do's ✅

- **Always include a realistic `User-Agent` header** to avoid bot detection
- **Check the `results` array length**, not `number_of_results` (it's buggy)
- **Implement retry logic with exponential backoff** for rate limiting (429, 403)
- **Query `/config` on first run** to discover available engines and categories
- **Handle partial results gracefully** (some engines may timeout)
- **Default to `format=json&language=en`** for compatibility
- **Self-host for reliability** if building production tools

### Don'ts ❌

- **Do not assume JSON is always enabled** (verify or handle 403)
- **Do not rely on the `number_of_results` field**
- **Do not hammer public instances** (use self-hosted or add delays)
- **Do not ignore `Retry-After` headers** in 429 responses
- **Do not assume engine availability** across instances
- **Do not use unsupported category/engine combinations without fallback**

---

## References

- [SearXNG Official Search API Docs](https://docs.searxng.org/dev/search_api.html)
- [SearXNG Result Types Documentation](https://docs.searxng.org/dev/result_types/index.html)
- [SearXNG Admin/Limiter Configuration](https://docs.searxng.org/admin/searx.limiter.html)
- [Go SearXNG Client (Reference Implementation)](https://pkg.go.dev/github.com/morikuni/go-searxng)
- [LangChain SearXNG Integration](https://python.langchain.com/docs/integrations/providers/searx/)
- [GitHub Issues: SearXNG number_of_results Bug](https://github.com/searxng/searxng/issues/2457)
- [Rate Limiting / 429 Handling](https://github.com/searxng/searxng/discussions/4265)
