# Project Planning: Pydantic AI Web-Search MCP Agent

This document describes the architecture, conventions, and roadmap for a Pydantic AI–based web-search agent that can
query Brave Search or SearXNG and will be exposed via a FastMCP server.

## 1. Project Goals

- Provide a Pydantic AI agent that can perform web search as a tool.
- Support two backends:
    - Brave Search (via `BRAVE_API_KEY`).
    - SearXNG (via `SEARXNG_BASE_URL`).
- Configure the underlying LLM and search backend via environment variables:
    - `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_CHOICE`.
    - `BRAVE_API_KEY`, `SEARXNG_BASE_URL`.
- Expose the agent as a Machine Control Protocol (MCP) server using FastMCP so that external clients/tools can call it.
- Maintain a clean, testable architecture aligned with repository conventions:
    - Python, Pydantic AI, pytest, PEP 8, and small, focused modules.

The initial scope is a single agent with simple "web search + summarization" behavior, plus test coverage and basic
documentation.

## 2. High-Level Architecture

### 2.1 Components

- **Configuration Layer**
    - Reads env vars and provides validated configuration objects for:
        - LLM provider setup.
        - Search backend (Brave or SearXNG).
        - General agent/runtime settings.
    - Uses Pydantic models for schema and validation.

- **Search Tooling Layer**
    - Implements Pydantic AI–style tools for web search:
        - `brave_search_tool` – calls the Brave Search API.
        - `searxng_search_tool` – calls the SearXNG instance.
    - Both tools share a common interface and result model (e.g., list of search results with title, URL, snippet).

- **Agent Layer**
    - Defines the Pydantic AI agent configuration and behavior.
    - Registers search tools and chooses which to use based on:
        - A preferred backend setting; or
        - Availability of backend-specific env vars.
    - Handles prompt construction, tool usage, and response shaping for "web search" queries.

- **MCP Server Layer (FastMCP)**
    - Wraps the agent in an MCP-compatible server.
    - Exposes one or more MCP tools, such as:
        - `web_search(query: str, max_results: int = 5)` → returns summarized search results.
    - Handles process lifecycle, configuration loading, and logging.

- **CLI / Entry Points**
    - Command-line interface implemented in a dedicated module (for example, `web_search_agent/cli.py`) using a modern
      Python CLI library (such as `typer`).
    - Provides both single-command and conversational REPL modes for interacting with the agent.
    - Optional `main.py` runner for quick debugging.

### 2.2 Data Flow

1. **Startup**
    - Configuration layer loads and validates env vars.
    - Search tools are initialized with backend-specific config (API keys, base URLs).
    - Pydantic AI agent instance is created and wired with tools and LLM configuration.
    - FastMCP server is started (for MCP mode) using the configured agent, or the CLI is invoked for interactive or
      one-off usage.

2. **Request Handling (Agent Use)**
    - Client calls an MCP tool (e.g., `web_search`) or invokes the CLI.
    - MCP server or CLI forwards the request to the Pydantic AI agent.
    - Agent decides which search tool to call (Brave or SearXNG) based on configuration.
    - Search tool performs an HTTP request to the appropriate backend and returns structured results.
    - Agent synthesizes the results into a concise, user-friendly answer and returns via MCP or prints to the terminal.

3. **Error Handling**
    - Config errors: fail fast with clear messages (missing keys, invalid URLs).
    - Backend errors: convert HTTP/network failures into well-typed error responses for the agent, and gracefully
      degrade (e.g., explanatory error messages).
    - MCP errors: ensure FastMCP returns a structured error payload.
    - CLI errors: return non-zero exit codes and human-friendly error messages.

## 3. Module and Package Layout

The project should follow a small, modular layout consistent with `.github/copilot-instructions.md`.

Suggested structure (top-level under this module):

- `main.py`
    - Optional CLI / quick runner for debugging the agent.
- `web_search_agent/`
    - `__init__.py`.
    - `config.py` – env var loading and Pydantic models.
    - `models.py` – shared domain models such as `SearchResult`, `SearchResults`.
    - `tools.py` – Brave and SearXNG search tool implementations.
    - `agent.py` – Pydantic AI agent definition and tool wiring.
    - `mcp_server.py` – FastMCP server wiring and MCP tool definitions.
    - `cli.py` – CLI entrypoints (single-command mode and conversational REPL) built on a modern CLI library.
- `tests/`
    - `test_config.py`.
    - `test_tools_brave.py`.
    - `test_tools_searxng.py`.
    - `test_agent.py`.
    - `test_mcp_server.py`.
    - `test_cli.py`.

Keep each file well below 500 lines; if any module approaches that size, split into submodules (e.g., `tools/brave.py`
and `tools/searxng.py`).

## 4. Configuration and Environment Handling

### 4.1 Environment Variables

The system is configured exclusively via environment variables (no secrets in code):

- **LLM config**
    - `LLM_PROVIDER`: logical provider name (`openai`, `openrouter`, or `ollama`).
    - `LLM_BASE_URL`: base URL for the LLM API (for self-hosted or compatible endpoints).
    - `LLM_API_KEY`: API key or token for the LLM provider.
    - `LLM_CHOICE`: a logical identifier of the LLM or configuration preset to use (for Pydantic AI agent
      configuration).

- **Search backends**
    - `BRAVE_API_KEY`: API key for Brave Search HTTP API.
    - `SEARXNG_BASE_URL`: base URL of SearXNG instance (e.g., `https://searxng.example.com`).

### 4.2 Config Design

- Use Pydantic models to represent:
    - `LlmConfig`.
    - `BraveConfig`.
    - `SearxngConfig`.
    - `AgentConfig` (high-level settings, including which search backend to prefer).
- Provide a single `load_config()` function in `config.py` that:
    - Reads env vars.
    - Validates them.
    - Returns a top-level `AppConfig` model holding all sub-configs.
- Validation rules:
    - At least one search backend must be fully configured (Brave or SearXNG).
    - LLM config must be valid (non-empty API key, plausible base URL when required).
    - If both Brave and SearXNG are configured, selection is based on a deterministic rule (documented here), such as:
        - Prefer the backend specified in a dedicated variable (e.g., `SEARCH_BACKEND`); or
        - Default to Brave when both are available.

### 4.3 `.env.example`

- Maintain a root-level `.env.example` containing all relevant env vars:
    - Include placeholder values and comments (not secrets).
- This file serves as documentation and a starting point for developers.

## 5. Testing Strategy

Testing uses `pytest` as described in `.github/copilot-instructions.md`.

### 5.1 Unit Tests

- **Config tests (`test_config.py`)**
    - Validate that:
        - Missing required env vars raise clear errors.
        - Partial configurations behave as expected (e.g., SearXNG-only).
        - Backend selection logic works correctly when both are available.

- **Search tools tests**
    - Use mocking for HTTP requests.
    - Verify:
        - Correct request URLs, headers, and query params for Brave and SearXNG.
        - Correct parsing into `SearchResult` / `SearchResults` models.
        - Handling of error responses (4xx/5xx, timeouts).

- **Agent tests**
    - Use Pydantic AI’s test harness or simple function-level tests.
    - Confirm:
        - The agent calls the expected tool given the config.
        - The agent returns a structured answer containing references to search results.

- **MCP server tests**
    - Test that:
        - MCP tools are registered.
        - An example request to `web_search` yields a plausible response.
        - Errors are surfaced correctly.

### 5.2 Edge Cases

- No search backend configured → clear startup error.
- Brave API key invalid → search tool wraps and surfaces an error.
- SearXNG instance unavailable (network error) → error surfaced with any documented fallback behavior.
- Env vars set but malformed (e.g., invalid URL) → Pydantic validation failure.

### 5.3 Test Organization

- Tests live under `tests/` mirroring main modules.
- Each new function or class should have:
    - A happy-path test.
    - An edge-case test.
    - A failure/exception test (where applicable).

## 6. MCP Integration (FastMCP)

### 6.1 Goals

- Provide an MCP server that exposes the web-search agent through a well-defined tool interface.
- Allow MCP-aware clients to call the agent without knowing underlying LLM or search backend details.

### 6.2 Design

- Implement `mcp_server.py` using FastMCP:
    - Initialize config and agent at startup.
    - Define one or more MCP tools, e.g.:
        - `web_search(query: str, max_results: int = 5)`.
    - Bridge between MCP tool invocation and the Pydantic AI agent:
        - Prepare an input message or structured request.
        - Invoke the Pydantic AI agent.
        - Map agent output to MCP response format.

- Provide a simple entry point (function or CLI) to start the server:
    - e.g., `python -m web_search_agent.mcp_server`.

- Make sure MCP tools and agent configuration share a single, consistent config load path (`load_config()`).

### 6.3 Observability

- Log:
    - Which backend is used (Brave vs SearXNG) for each request.
    - Relevant error messages (without leaking secrets).
- Optionally, add structured logging hooks later.

## 7. Future Extensions

- Support additional search backends (e.g., SerpAPI, Google Custom Search, Bing).
- Add richer search parameters (time ranges, language filters, safe search).
- Add a caching layer for repeated queries.
- Add multiple agents for different tasks (e.g., news summarizer, research assistant) sharing the same MCP server.
- Introduce higher-level task management in `.ai/tasks/` following the 3-pass plan once implementation starts.

## 8. CLI Design

### 8.1 Overview

The CLI for the Pydantic AI Web-Search MCP Agent provides a convenient way to interact with the agent from the command
line. It is implemented in `web_search_agent/cli.py` using the `typer` library, supporting both single-command and
REPL (Read-Eval-Print Loop) modes.

### 8.2 Single-Command Mode

In single-command mode, the CLI allows users to perform a web search and get summarized results in a single command. The
basic syntax is:

```bash
python -m web_search_agent.cli search "query" --max-results 5
```

- `search`: The command to perform a web search.
- `"query"`: The search query string (required).
- `--max-results`: Optional; the maximum number of results to return (default is 5).

The command will:

- Validate the input parameters.
- Invoke the appropriate MCP tool (`web_search`) with the query.
- Print the summarized search results to the terminal.

### 8.3 REPL Mode

REPL mode allows for an interactive session with the agent, where users can continuously ask questions and receive
answers without retyping the command. To start REPL mode:

```bash
python -m web_search_agent.cli repl
```

In REPL mode:

- The user is prompted to enter a query.
- The agent processes the query and returns the results.
- The session continues until the user exits (e.g., by typing `exit`).

### 8.4 Error Handling

The CLI should gracefully handle errors, such as:

- Invalid or missing query parameters → print a user-friendly error message and show help.
- Network or backend errors → print an explanatory message and possible next steps.
- Configuration errors (e.g., missing API keys) → print a clear, actionable message.

### 8.5 Future CLI Enhancements

Future enhancements to the CLI could include:

- Additional commands for different agent capabilities (e.g., `summarize`, `analyze`).
- Support for batch processing of queries.
- Integration with configuration management (e.g., `config set/get` commands).
- Enhanced error handling and recovery suggestions.
