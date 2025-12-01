# Tasks: Pydantic AI Web-Search MCP Agent

This document tracks planned work for the web-search agent project. Tasks here should correspond to
`.ai/tasks/{{TASK-ID}}.yaml` entries when the 3-pass workflow is used.

Status values: `pending`, `in_progress`, `in_review`, `done`.

## 1. Core Agent, Tooling, and Scaffolding

### TASK-001 – Design and scaffold agent package layout

- **Status:** pending
- **Summary:** Create the base Python package (e.g., `web_search_agent`) with `config.py`, `models.py`, `tools.py`,
  `agent.py`, `mcp_server.py`, and a basic CLI entry point wired into `main.py` (or a console script) following
  `docs/PLANNING.md` architecture.
- **Acceptance Criteria:**
    - Package exists and can be imported.
    - Each module contains minimal, documented placeholders.
    - A CLI stub exists that can be invoked from the command line (even if it only prints a help message or version).
    - No runtime business logic required yet; focus on structure, docstrings, and clear layering.

### TASK-002 – Implement configuration, env management, and initial CI workflow

- **Status:** pending
- **Summary:** Implement `config.py` to load and validate env vars: `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_API_KEY`,
  `LLM_CHOICE`, `BRAVE_API_KEY`, `SEARXNG_BASE_URL`. Add `.env.example` and set up a minimal GitHub Actions workflow
  to run formatting and tests on pushes/PRs.
- **Acceptance Criteria:**
    - Pydantic models for LLM, Brave, SearXNG, and app/agent config.
    - `load_config()` reads env vars and enforces validation rules.
    - `.env.example` lists all relevant vars with comments and no secrets.
    - A GitHub Actions workflow (e.g., `.github/workflows/ci.yml`) runs at least `ruff` (or equivalent) and `pytest`.
    - Unit tests cover happy path and failure modes for missing/malformed env vars.

### TASK-003 – Implement Brave Search tool

- **Status:** pending
- **Summary:** Implement a Brave Search web-search tool in `tools.py` (or `tools/brave.py`) compatible with Pydantic AI
  tools.
- **Acceptance Criteria:**
    - Tool function accepts a search query and optional parameters (e.g., max results).
    - Uses `BRAVE_API_KEY` from config; performs HTTP requests to Brave Search API.
    - Returns structured `SearchResult` / `SearchResults` models.
    - Handles HTTP and API errors gracefully.
    - Unit tests (with mocked HTTP) verify request construction, parsing, and error handling.

### TASK-004 – Implement SearXNG Search tool

- **Status:** pending
- **Summary:** Implement a SearXNG web-search tool in `tools.py` (or `tools/searxng.py`) compatible with Pydantic AI
  tools.
- **Acceptance Criteria:**
    - Tool function accepts a search query and optional parameters.
    - Uses `SEARXNG_BASE_URL` from config; performs HTTP requests to SearXNG instance.
    - Returns structured `SearchResult` / `SearchResults` models consistent with Brave tool.
    - Handles HTTP and API errors gracefully.
    - Unit tests (with mocked HTTP) verify request construction, parsing, and error handling.

### TASK-005 – Implement Pydantic AI web-search agent

- **Status:** pending
- **Summary:** Define a Pydantic AI agent in `agent.py` that uses the Brave and SearXNG tools and picks a backend based
  on configuration.
- **Acceptance Criteria:**
    - Agent is constructed from configuration (`load_config()`).
    - Agent can decide between Brave and SearXNG:
        - Chooses a configured backend deterministically when both are available.
    - Agent exposes a simple method or callable entry to answer “web search” questions (query → summarized answer).
    - Unit tests verify:
        - Backend selection logic at the agent level.
        - Behavior when only one backend is available.
        - Behavior when no backend is configured (clear error).

### TASK-006 – Implement a modern CLI interface for the agent

- **Status:** pending
- **Summary:** Implement a clean, modern command-line interface that allows running the agent from the terminal with
  sensible arguments and modes. Provide both a single-command mode (one-off query) and a conversational REPL where the
  user can interact with the agent across multiple turns. Use a standard Python CLI library (such as `typer`)
  consistent with project conventions, implemented in a dedicated module (for example, `web_search_agent/cli.py`).
- **Acceptance Criteria:**
    - CLI can be invoked via `python -m web_search_agent` or a console script defined in `pyproject.toml`.
    - CLI exposes at least two subcommands (names may vary but should be clearly documented), for example:
        - A single-command mode (e.g., `single`) that runs one query and exits.
        - An interactive REPL mode (e.g., `repl`) that maintains a conversation with the agent.
    - Single-command mode supports at least:
        - Passing a search query as a positional argument or option.
        - Optional flags for max results and basic verbosity.
        - An optional `--backend` override when both Brave and SearXNG are available, defaulting to configuration
          rules when omitted.
        - Clear `--help` output describing options and environment variable usage.
    - REPL mode supports at least:
        - A persistent session where the user can enter multiple prompts and receive responses without restarting the
          process.
        - Simple slash-style commands for invoking meta-actions (for example `/help`, `/exit`, and optionally `/backend`
          to switch backend preference for the remainder of the session).
        - A clear banner on startup indicating the active backend, how to exit, and how to list available commands.
    - CLI delegates requests into the same agent logic used by the MCP server (no duplicated business logic; the CLI
      should be a thin layer over shared helper functions).
    - Basic tests cover:
        - CLI argument parsing and subcommand dispatch.
        - A happy-path invocation for single-command mode (e.g., using `pytest` with a CLI testing helper).
        - A minimal REPL interaction (for example, starting the REPL, sending one prompt, and exiting), using mocks to
          avoid network calls.

## 2. MCP Integration

### TASK-007 – Wire FastMCP server around the agent

- **Status:** pending
- **Summary:** Create a FastMCP-based MCP server in `mcp_server.py` that exposes the web-search agent as MCP tools.
- **Acceptance Criteria:**
    - FastMCP server can be started via a simple entry point (e.g., `python -m web_search_agent.mcp_server` or
      `main.py`).
    - At least one MCP tool `web_search(query: str, max_results: int = 5)` is available.
    - Tool calls are delegated to the Pydantic AI agent and return summarized results.
    - Errors are surfaced as structured MCP errors.
    - Basic tests confirm tool registration and a happy-path request.

## 3. Testing & Quality

### TASK-008 – Add and organize pytest test suite

- **Status:** pending
- **Summary:** Set up and/or extend `pytest` tests for config, tools, agent, CLI, and MCP server as described in
  `docs/PLANNING.md`.
- **Acceptance Criteria:**
    - `tests/` package contains tests for `config`, `tools` (Brave and SearXNG), `agent`, `cli`, and `mcp_server`.
    - Each new module has at least:
        - 1 happy-path test.
        - 1 edge-case test.
        - 1 failure-mode test (where applicable).
    - Tests run via `pytest` and pass locally and in CI.

### TASK-009 – Extend CI workflows for formatting and quality checks

- **Status:** pending
- **Summary:** Ensure commands for formatting and tests (black, ruff, pytest) are fully documented and enforced in CI,
  extending the initial workflow created in TASK-002.
- **Acceptance Criteria:**
    - `pyproject.toml` (or equivalent) includes relevant tool configs if not present.
    - Documented commands for:
        - Formatting: `black` / `ruff`.
        - Testing: `pytest`.
    - GitHub Actions workflow runs formatting and tests on pushes and PRs, failing the build on errors.

## 4. Documentation

### TASK-010 – Update README for web-search agent, CLI, and MCP usage

- **Status:** pending
- **Summary:** Extend the root `README.md` (and/or `RAG_Pipeline/README.md` as needed) to explain how to configure and
  run the web-search agent via CLI and MCP server.
- **Acceptance Criteria:**
    - README covers:
        - Project overview and goals.
        - Required env vars (with reference to `.env.example`).
        - How to run tests.
        - How to start the MCP server and example usage.
        - How to invoke the CLI, including example commands and options.
    - References `docs/PLANNING.md` and `docs/TASKS.md` for deeper details.

### TASK-011 – Align documentation with 3-pass plan workflow

- **Status:** pending
- **Summary:** Ensure `docs/TASKS.md` and the `.ai/tasks` workflow can be used for future work according to
  `.github/instructions/3-pass-plan.instructions.md`.
- **Acceptance Criteria:**
    - `docs/TASKS.md` reflects active tasks and statuses accurately.
    - Each new task eventually gets a corresponding `.ai/tasks/{{TASK-ID}}.yaml` when implementation begins.
    - Notes added for how to use Spec/Scaffold/Stabilize passes for this project.

## 5. Discovered During Work

Use this section to append new tasks discovered while implementing or stabilizing existing tasks. Each new item should
be promoted to a numbered `TASK-XXX` section when ready.

- _None yet._
