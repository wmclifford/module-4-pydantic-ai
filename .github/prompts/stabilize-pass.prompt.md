---
description: "Run tests, linters, and finalize a task branch: ensure acceptance criteria are met, update the task status to in_review, commit evidence, and open a PR."
read_scaffold_artifact: true
write_stabilize_artifact: true
---

## Context to load

- Read these governing documents:
    - `docs/PLANNING.md`
    - `docs/TASKS.md`
    - `.ai/tasks/{{ task_id }}.yaml`
    - `.ai/tasks/{{ task_id }}/scaffold.yaml` (machine-readable scaffold artifact)
    - `.ai/tasks/{{ task_id }}/spec.yaml` (machine-readable spec artifact)
- Validate the scaffold artifact against: `.ai/schemas/scaffold-artifact.schema.v0.1.json`
- Validate the spec artifact against: `.ai/schemas/spec-artifact.schema.v0.1.json`

## Task

Take a validated scaffold artifact and bring the task branch to a state where the task's acceptance criteria are
satisfied. When complete, update the task file to `in_review`, add evidence (commit SHAs and a brief test summary),
commit the task file, and open a Pull Request for review.

## Constraints

- Ask the operator for the TASK ID or the path to the scaffold artifact if not provided.
- Operate only on the task branch that was created during the spec pass. If the branch is not checked out, stop and ask
  the operator to check out the branch.
- Do NOT modify files outside the union of:
    - files listed in `applied_diffs` inside the scaffold artifact
    - test and build-related files required to make the project pass; ask the operator before editing additional
      top-level build files
    - `.ai/tasks/{{ task_id }}/` files
    - `.ai/tasks/{{ task_id }}.yaml` (the task file to update at the end)
- All commits created during the stabilization pass MUST follow the Conventional Commits format as described
  in [the commit instructions](../git-commit-instructions.md).

## Instructions (execute in order)

1. Confirm you can read the governing documents and the scaffold/spec schemas.
2. Ask the operator for the TASK ID or scaffold path.
3. Load and validate `.ai/tasks/{{ task_id }}/scaffold.yaml` against `.ai/schemas/scaffold-artifact.schema.v0.1.json`.
   Use `.ai/tools/validate_yaml.py` to perform the validation. If validation fails, present errors and stop.
4. Confirm the current git branch matches `branch_plan.initial_branch_name` from `.ai/tasks/{{ task_id }}/spec.yaml` (or
   ask the operator for the branch name). If it does not, stop and ask the operator to check out the correct branch.
5. Run the project's checks in this order; for each step, capture the output and record failures (adapt to the project's
   build system):
    - Lint/static analysis
    - Unit tests (only if `acceptance.commands` indicate tests are expected)
    - Integration tests (only if `acceptance.commands` indicate tests are expected)
    - Any configured quality gates (e.g., coverage thresholds)
6. If checks fail, attempt iterative fixes up to **three** quick iterations:
    - For each iteration: fix the smallest set of issues that addresses the failures (tests, flaky tests, config), run
      the failing checks, and commit the fix using a Conventional Commit message. The `type` of commit should be one of
      `fix`, `refactor`, or `chore`, depending on the nature of the fix.
    - If a failing issue requires design changes or is ambiguous, record the problem in
      `.ai/tasks/{{ task_id }}/stabilize-notes.md` and create a QUESTION in the Stabilize report; do not guess large
      design changes.
7. After tests and quality gates pass (or you reach iteration limits), produce two artifacts under
   `.ai/tasks/{{ task_id }}/`:
    - `stabilize.yaml` - machine-readable artifact following `.ai/schemas/stabilize-artifact.schema.v0.1.json`
    - `stabilize-report.md` - human-friendly summary with test/lint commands, output snippets, applied commits with SHAs
      and messages, and unresolved QUESTIONS
8. Validate the generated `.ai/tasks/{{ task_id }}/stabilize.yaml` against
   `.ai/schemas/stabilize-artifact.schema.v0.1.json`. Use `.ai/tools/validate_yaml.py` to perform the validation. If
   validation fails, present errors and stop.
9. Update `.ai/tasks/{{ task_id }}.yaml`:
    - set `status` to `in_review`
    - append an `evidence` entry containing:
        - timestamp
        - branch name
        - commit SHAs (scaffold commits + stabilize commits)
        - `testSummary` as an OBJECT (structured per `.ai/schemas/task-file.schema.v0.1.json`)
        - optional `ciRunUrl` and `prUrl` when available
10. Commit the updated task file with a Conventional Commit message (e.g., `chore: update task status to in_review`).
11. Push the branch to the remote and open a Pull Request. If the spec contains a preferred base branch in `branch_plan`
    use it; otherwise ask the operator for the PR base. Use a PR title and body template:
    - Title: `<type>(<scope>): <subject>`
    - Body: include a short description, list of related commits, links to artifacts under `.ai/tasks/{{ task_id }}/`,
      and the stabilization report summary.
    - If CLI is available, create the PR with `gh pr create --fill --base <base> --head <branch>` or equivalent. If CLI
      is not available, provide the full PR data for the operator to open the PR manually.
12. Present the PR URL (or prepared PR payload) to the operator and wait for review/merge.

## Acceptance Criteria

- The project's checks pass locally (lint/tests/quality gates), or there is a written justification for otherwise in
  `.ai/tasks/{{ task_id }}/stabilize-report.md`.
- `.ai/tasks/{{ task_id }}.yaml` status is `in_review` and contains an evidence entry with commit SHAs and test summary.
- A Pull Request exists (or a prepared PR payload is provided) for the task branch against the chosen base branch.
- `.ai/tasks/{{ task_id }}/stabilize-report.md` exists documenting the steps, commits, and results.

## Output

- A concise summary of the stabilization work, commit list and SHAs, link to the PR (or PR payload), and any QUESTIONS
  for the operator.
