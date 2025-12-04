# Copilot CLI Workflow

This document describes how to use the custom Copilot CLI agents in this repository to run the 3-pass workflow:

- **Spec (Plan)** – handled by the `architect` agent.
- **Scaffold + Stabilize (Implement + Validate)** – handled end-to-end by the `senior-developer` agent.

The goal is to provide a repeatable, auditable flow per task (`.ai/tasks/{{ task_id }}.yaml`).

> All commands below assume you run them from the repository root:
>
> ```bash
> cd /home/william/AiCodeProjects/ai-agent-mastery-course/module-4-pydantic-ai
> ```

---

## 1. Prerequisites

- `gh` (GitHub CLI) with Copilot enabled.
- `uv` installed and working in this repo.
- Task file exists under `.ai/tasks/{{ task_id }}.yaml` with `status: pending`.

Custom agents are defined under:

- `architect` – `.github/agents/architect.agent.md`
- `senior-developer` – `.github/agents/senior-developer.agent.md`
- `research-engineer` – `.github/agents/research-engineer.agent.md` (optional helper for external research)

The 3-pass governance and schemas are defined in:

- `.github/instructions/3-pass-plan.instructions.md`
- `.github/instructions/spec-pass.instructions.md`
- `.github/instructions/scaffold-pass.instructions.md`
- `.github/instructions/stabilize-pass.instructions.md`
- `.ai/schemas/*.schema.v0.1.json`

---

## 2. Spec Pass with `architect` (on `main`)

You start the Spec pass on the `main` branch. The `architect` agent will:

1. Read governance docs and instructions.
2. Read the task file.
3. Propose and refine `planned_diffs` and `requiredDependencies`.
4. (When approved) write and validate:
    - `.ai/tasks/{{ task_id }}/spec.yaml`
    - `.ai/tasks/{{ task_id }}/planned-diffs.md`
5. Create the task branch and first commit with:
    - Updated task file (`status: in_progress`).
    - Spec artifacts.

### 2.1. Run Spec planning (draft only)

From `main`:

```bash
git checkout main

gh copilot chat \
  --agent architect \
  --prompt .github/prompts/spec-pass.prompt.md \
  --title "Spec pass for TASK-003" \
  --message "Run the Spec pass for .ai/tasks/TASK-003.yaml with write_spec_artifact: false. Load governance docs and instructions, summarize the task and acceptance criteria, and propose a DRAFT spec (planned_diffs + dependency analysis). Do not write spec artifacts or touch git yet."
``

In this conversation:

- Review `Task Summary`, `Planned Diffs`, `Dependency Analysis`, and `QUESTIONS`.
- Iterate until the plan looks correct.

### 2.2. Approve and write spec artifacts (no commits yet)

Once you are happy with the plan, send a follow-up message **in the same chat**:

```text
Treat the current spec as READY FOR ARTIFACTS and set write_spec_artifact: true. Please:

1. Read .ai/schemas/spec-artifact.schema.v0.1.json again to confirm the required fields.
2. Write .ai/tasks/TASK-003/spec.yaml with schemaVersion "0.1.0" and the correct structure.
3. Write .ai/tasks/TASK-003/planned-diffs.md to summarize the planned changes.
4. Validate the spec artifact using:
   uv run .ai/tools/validate_yaml.py .ai/tasks/TASK-003/spec.yaml .ai/schemas/spec-artifact.schema.v0.1.json
5. If validation fails, fix spec.yaml and re-run validation until it passes, explaining what changed.

Do not create a branch or commit yet.
```

You can optionally verify the artifacts manually:

```bash
ls .ai/tasks/TASK-003
cat .ai/tasks/TASK-003/spec.yaml
cat .ai/tasks/TASK-003/planned-diffs.md
```

### 2.3. Let `architect` create the task branch and first commit

After you confirm the artifacts look correct, tell `architect` to perform the Spec-pass branch ritual:

```text
The spec artifacts for TASK-003 look good and validated. Please now:

1. Ensure there are no unrelated staged changes.
2. Create a branch named feat/TASK-003-<short-slug> (you may propose a slug based on the task title).
3. On the new branch, update .ai/tasks/TASK-003.yaml to set status: in_progress and record branchName and timestamp.
4. Stage and commit together:
   - .ai/tasks/TASK-003.yaml
   - .ai/tasks/TASK-003/spec.yaml
   - .ai/tasks/TASK-003/planned-diffs.md
5. Use this Conventional Commit message:
   chore(artifacts): start task branch and add spec artifacts

   Refs: TASK-003

Report the branch name and first commit SHA when done.
```

When `architect` finishes, you should have a branch like:

- `feat/TASK-003-add-config` (example)
- First commit containing the task file and spec artifacts.

Verify locally:

```bash
git status
git branch --show-current
git log -1
```

---

## 3. Scaffold + Stabilize with `senior-developer` (on the task branch)

Once the Spec pass is complete and the task branch exists, you can hand over to the `senior-developer` agent. This
agent:

- Runs the **Scaffold** pass:
    - Validates `spec.yaml`.
    - Runs `uv sync --all-groups --all-packages` (pre-flight).
    - Installs `requiredDependencies` and commits them.
    - Applies `planned_diffs` in order with one commit per diff.
    - Writes and validates `scaffold.yaml` and `scaffold-report.md`.
- Then runs the **Stabilize** pass:
    - Validates `scaffold.yaml`.
    - Runs `uv sync --all-groups --all-packages` and ensures dependencies are present.
    - Runs linters and tests, applies up to three rounds of targeted fixes.
    - Writes and validates `stabilize.yaml` and `stabilize-report.md`.
    - Updates the task file to `status: in_review` with structured evidence.
    - Pushes the branch and (optionally) opens a PR.

### 3.1. Start the senior-developer session

Check out the task branch created by `architect`:

```bash
git checkout feat/TASK-003-add-config  # use the actual branch name returned by architect
```

Start a new Copilot chat using the `senior-developer` agent:

```bash
gh copilot chat \
  --agent senior-developer \
  --title "Scaffold + Stabilize for TASK-003" \
  --message "Run the Scaffold and Stabilize passes for task TASK-003 on the current branch. Use the existing spec artifacts in .ai/tasks/TASK-003/, follow the scaffold-pass and stabilize-pass instructions, and bring the task to status: in_review with all artifacts validated."
```

The agent will:

1. Read governance docs and scaffold/stabilize instructions.
2. Validate `.ai/tasks/TASK-003/spec.yaml` against `spec-artifact.schema.v0.1.json`.
3. Perform the Scaffold phase.
4. Perform the Stabilize phase.
5. Update `.ai/tasks/TASK-003.yaml`, push the branch, and open a PR (if permitted).

You can ask for progress updates at any time, for example:

```text
Summarize what you have done so far (Scaffold vs. Stabilize), including commits created and artifacts written.
```

---

## 4. Using `research-engineer` (optional helper)

The `research-engineer` agent is a read-only helper dedicated to external research. You can:

- Call it directly for library/standards questions.
- Let `architect` or `senior-developer` delegate to it via `run_subagent` when they need deeper external knowledge
  (e.g., choosing between libraries, confirming best practices).

Example standalone usage:

```bash
gh copilot chat \
  --agent research-engineer \
  --title "Compare HTTP client libraries" \
  --message "For Python 3.13 and this repo's style, compare httpx and aiohttp for async HTTP calls. Focus on ecosystem, performance, maintenance status, typing support, and testability. Recommend one with rationale and provide references."
```

You can then feed the `Key Findings` and `Recommendation` back into an `architect` session when planning dependencies.

---

## 5. End-to-end Sample Session

This section walks through an abbreviated, realistic flow for `TASK-003`.

### Step 1: Run Spec pass on `main` with architect

```bash
git checkout main

gh copilot chat \
  --agent architect \
  --prompt .github/prompts/spec-pass.prompt.md \
  --title "Spec pass for TASK-003" \
  --message "Run the Spec pass for .ai/tasks/TASK-003.yaml with write_spec_artifact: false. Load governance docs and instructions, summarize the task and acceptance criteria, and propose a DRAFT spec (planned_diffs + dependency analysis). Do not write spec artifacts or touch git yet."
```

In chat:

- Review the draft spec.
- Ask the agent to refine `planned_diffs` and `requiredDependencies` until they are acceptable.

Then approve and request artifact writing + validation:

```text
The spec for TASK-003 looks good. Please now:
1. Set write_spec_artifact: true.
2. Read .ai/schemas/spec-artifact.schema.v0.1.json.
3. Write .ai/tasks/TASK-003/spec.yaml and planned-diffs.md.
4. Validate spec.yaml with uv run .ai/tools/validate_yaml.py .ai/tasks/TASK-003/spec.yaml .ai/schemas/spec-artifact.schema.v0.1.json and fix any issues.
Do not create a branch or commit yet.
```

Once the artifacts look correct, perform the branch ritual:

```text
Artifacts look correct. Please:
1. Create a branch feat/TASK-003-<slug> from main.
2. On the new branch, update the task file to status: in_progress and record branchName and timestamp.
3. Commit the task file, spec.yaml, and planned-diffs.md together using:
   chore(artifacts): start task branch and add spec artifacts

   Refs: TASK-003

Report the branch name and commit SHA.
```

### Step 2: Run Scaffold + Stabilize with senior-developer

```bash
git checkout feat/TASK-003-<slug>  # branch name from architect

gh copilot chat \
  --agent senior-developer \
  --title "Scaffold + Stabilize for TASK-003" \
  --message "On this branch, run the Scaffold and Stabilize passes for TASK-003 using .ai/tasks/TASK-003/spec.yaml and planned-diffs.md. Validate all artifacts with the YAML schemas, update the task file to status: in_review with evidence, and prepare the branch and PR as described in the 3-pass plan."
```

The `senior-developer` agent will:

- Confirm `spec.yaml` and `scaffold.yaml` match their schemas.
- Use `uv sync --all-groups --all-packages` and `uv add` as needed.
- Apply each planned diff with one commit per diff.
- Create and validate `scaffold.yaml` / `scaffold-report.md` and `stabilize.yaml` / `stabilize-report.md`.
- Update `.ai/tasks/TASK-003.yaml` to `status: in_review` with `evidence` populated.
- Push the branch and open a PR.

You can then review the PR in GitHub, using the artifacts under `.ai/tasks/TASK-003/` as an audit trail.

---

## 6. Tips and Troubleshooting

- **Validation failures**: If any `uv run .ai/tools/validate_yaml.py ...` call fails, the agents are instructed to:
    - Not commit invalid YAML.
    - Fix artifacts to match the schema.
    - Re-run validation and surface QUESTIONS if interpretation is unclear.
- **Ambiguous planned diffs**: If a marker cannot be found or is ambiguous, `architect` should record that in the
  spec, and `senior-developer` will:
    - Insert `TODO` markers instead of guessing.
    - Document the issue in `scaffold-report.md` and surface QUESTIONS.
- **Flaky tests**: `senior-developer` will:
    - Retry or apply minimal test-only mitigations.
    - If still flaky, mark tests as `xfail` and document under `Flaky tests` in `stabilize-report.md`.
- **Cost control**: `architect` uses a larger model for planning; `senior-developer` and `research-engineer` use
  Claude Haiku 4.5 to keep implementation and research passes cost-efficient.

Use this document as a quick reference whenever you pick up a new task file under `.ai/tasks/`. It encodes the expected
Copilot CLI flow so the 3-pass plan is applied consistently across the project.

