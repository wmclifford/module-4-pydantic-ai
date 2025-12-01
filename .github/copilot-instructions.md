# Copilot Instructions

> Machine-readable summary

```yaml
project:
  name: ai-agent-mastery-course
  primary_language: "python"
  framework: "pydantic-ai"
  code_style: "PEP8"
  formatting_tools: [ "black", "ruff" ]
  testing_framework: "pytest"
  task_management: "yaml-based"
  commit_convention: "conventional-commits"
```

### Project Awareness and Context

- **Always read `docs/PLANNING.md`** at the start of a new conversation to understand the project's architecture, goals,
  style, and constraints.
- **Check `docs/TASKS.md`** before starting a new task. If the task is not listed, add it with a brief description and
  today's date.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `docs/PLANNING.md`.

### Releases & Publishing

- Use `semantic-release` (or similar) for automatic changelog and release tagging where appropriate for templates or
  actions published from this repo.

---

## Code Structure and Modularity

### Organization

- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it
  into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility. For agents this looks like:
    - `agent.py` - Main agent definition and execution logic
    - `tools.py` - Tool functions used by the agent
    - `prompts.py` - System prompts
- **Use clear, consistent imports** (prefer relative imports within packages).

### Testing and Reliability

- **Always create Pytest unit tests for new features** (functions, classes, routes, etc.).
- **After updating any logic**, check whether existing unit tests need to be updated. If so, update them.
- **Tests should live in a `/tests` folder** mirroring the main app structure.
    - Include at least:
        - 1 test for expected use (the "happy path")
        - 1 test for edge cases (invalid inputs, unexpected errors, etc.)
        - 1 test for failure conditions (invalid API responses, etc.)
- Always test the individual functions for agent tools.

Where possible, try to follow the [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)
process. Functional or end-to-end tests should follow
the [Behavior-Driven Development](https://en.wikipedia.org/wiki/Behavior-driven_development)
process, though they are not presently planned.

### Style and Conventions

- **Use Python** as the primary language.
- **Follow PEP8**, use type hints, and use `black` to format code.
- **Use `pydantic` for data validation**.
- Write **docstrings for every function** using the Google style:
    ```python

    def example_function(param1: int, param2: str) -> bool:
        """Short description of the function.

        Args:
            param1 (int): Description of param1.
            param2 (str): Description of param2.

        Returns:
            bool: Description of the return value.
        """
        pass

    ```

### Formatting

- Source of truth: `.editorconfig`
- Enforced via: `black`/`ruff`
- Auto-fixable via: `black --fast --quiet`
- Auto-format via: `prettier --write`
- Agents must run formatting after edits and re-stage only formatted files.

### Documentation and Explainability

- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment non-obvious code** and ensure everything is understandable to a mid-level developer.
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

---

## AI Behavior Rules

- **Never assume missing context. Ask questions if uncertain.**
- **Always confirm file paths and module names** exist before using them.
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from `docs/TASKS.md`.

---

## Branching and Commits

### Branch and Merge Policy

- PR is **required** to merge to `main`.
- **Trunk-based** development:
    - require squash merges to `main`.
    - PR title must be a Conventional Commit.
    - include `Refs: [TASK-ID]` in the PR footer.
- CI **must** pass before merging.
- Code review is required; **at least 1 approving review** — may be manual or assisted by an AI reviewer.
- Consider required reviewers for sensitive changes (templates, workflows, schemas).

### Conventional Commits

Instructions for formatting commit messages can be found [here](git-commit-instructions.md).

### Two-commit Evidence Ritual

1. CODE commit implements the task.
2. EVIDENCE commit updates the task file (`.ai/tasks/<TASK-ID>.yaml`) with `evidence.commit` = 40-char commit hash.

Note: The task file schema supports optional `evidence.timestamp` (ISO-8601) and `evidence.branchName` (the branch used
for the task). Populate these where helpful.

### Additional Rules

- **One task per PR** preferred; avoid mixing concerns.
- **Branch Naming:** `<type>/<TASK-ID>-<slug>`; e.g. `feat/PAD-002-add-new-feature`
- Agents must create/checkout branch after spec approval and before edits; task file status must be
  updated to `in_progress`, and the task file must be committed to the branch before any code changes.
- Merging:
    - Local: linear history per task (rebase or squash locally).
    - Remote: **squash merges** recommended; PR title must follow Conventional Commits format.

### Dependency Management

- During the Spec pass, perform a quick dependency analysis and propose `requiredDependencies` split into `runtime` and `dev` arrays in the spec artifact.
- During the Scaffold pass, install dependencies via `uv` and commit those changes separately using Conventional Commits. Examples:
  - `uv add httpx pydantic-settings`
  - `uv add --dev pytest pytest-cov`
  - Commit: `chore(deps): add httpx and pytest` with `Refs: <TASK-ID>` in the footer.
- Record exact installed versions in `scaffold.yaml` under `resolvedDependencies`.
- In the Stabilize pass, run a pre-flight check: ensure deps are installed/synced (`uv sync`) before running tests.

---

## Task Management

### Task Lifecycle (cheat sheet)

```markdown
`pending` (task file created and exists on `main` branch)
-> `in_progress` (branch created)
-> `in_review` (branch pushed, PR created)
-> `done` (PR merged and evidence commit present)
```

- **`pending`:** task file exists on `main` branch; task is not yet started.
- **`in_progress`:** should be updated as first commit when branch is created, before any code changes.
- **`in_review`:** task file must be updated with `evidence.commit` = <code SHA> and status set to `in_review` as
  last commit on the branch, just before PR is opened.
- **`done`:** task branch has been merged to `main`; the task file must be updated with `status` = `done` and
  the `evidence.commit` must be updated to the squash commit of the PR; commit this directly to `main`.
- The `done` transition is handled by the post-merge ritual described in
  `.github/instructions/3-pass-plan.instructions.md`.

### Task Completion

- **Mark completed tasks in `docs/TASKS.md`** immediately after they are completed.
- Add new subtasks or TODOs discovered during development to `docs/TASKS.md` under a "Discovered During Work" section.

### Evidence & Audit

- Completed tasks must have `evidence.commit` set to the code SHA present in the repository:
    - Before the PR is merged, this will be the SHA of the PR branch commit referenced in the task file.
    - After the PR is merged, this will be the SHA of the squashed commit on the `main` branch.
- `evidence.prUrl` should reference the PR URL for the audit trail.
- `evidence.ciRunUrl` may remain empty for this repo (it does not build artifacts), but templates that include CI should
  prefer linking to the CI run for traceability.
- Keep an audit trail in tasks and record the `evidence.commit` and `evidence.prUrl` for all tasks (documentation,
  examples, and production tasks) per the agreed evidence policy.

---

## Security

- **Never** store secrets in source code, configuration files, or documentation; use repository secrets instead.
- Use short-lived tokens and least privilege for automation. For publishing or automation that requires long-lived
  credentials, store them in an organization-level secrets store and rotate regularly.
- Protect sensitive branches (`main`) with branch protection rules: require PRs, require passing status checks, require
  reviews, and limit who can push directly.
- Audit access to repository secrets and review secret usage periodically.

---

## Deviations

- Any deviation must include a short ADR entry with rationale and consequences, rollback plan, and approval
  signature (owner-driven by default). See `docs/ADR.md` for the ADR format and process.
