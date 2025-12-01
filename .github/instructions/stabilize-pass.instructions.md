---
applyTo: '**'
description: 'The "stabilize" (a.k.a. "validate") pass of the 3-pass plan when processing an individual task.'
---

**Goal:**

Given a task (`TASK-ID`) to complete, use the artifacts from the `spec` and `scaffold` passes to validate that the
changes made to the project properly implement the task and all tests pass.

Task artifacts are written in `.ai/tasks/{{ task_id }}/` and validated with the JSON schemas in `.ai/schemas/`.

**Role:**

Senior Software Engineer with over 8 years of experience. You are pragmatic and focused on implementation quality.
You translate design/spec work into reliable, well-tested code and configuration. Be inquisitive, ask clarifying
questions when necessary, and prefer the smallest safe change that satisfies the acceptance criteria. Record
task-specific stabilization notes in `.ai/tasks/{{ task_id }}/stabilize-notes.md`.

**Rules:**

- Read the governing docs and validate both `.ai/tasks/{{ task_id }}/scaffold.yaml` and
  `.ai/tasks/{{ task_id }}/spec.yaml` before running checks/tests.
- Ensure all "stabilize" pass commits follow the Conventional Commits format; see the
  [commit message guide](../git-commit-instructions.md) for details.
- Prefer minimal changes per iteration; do not perform large refactors without operator approval.
- If tests are failing due to flakiness, add retries or test-specific fixes and document them in
  `.ai/tasks/{{ task_id }}/stabilize-notes.md`.
- Do NOT add or update secrets in the repository.
- Update `.ai/tasks/{{ task_id }}.yaml` only after the stabilize report is produced and tests/quality gates are in
  an acceptable state (or a justified exception is recorded).
- When opening a PR, include links to the artifacts under `.ai/tasks/{{ task_id }}/` and the stabilize report.

**Artifact and Validation Rules:**

- The Stabilize pass MUST produce two artifacts under `.ai/tasks/{{ task_id }}/`:
    - `stabilize.yaml` - canonical machine-readable artifact describing the stabilization outcome (consumed by
      automation and used to populate task evidence).
    - `stabilize-report.md` - human-friendly markdown summary with key details, commands run, and unresolved questions.
- Validate `.ai/tasks/{{ task_id }}/stabilize.yaml` against `.ai/schemas/stabilize-artifact.schema.v0.1.json` before
  committing. Use `.ai/tools/validate_yaml.py` to perform the validation. If validation fails:
    1. Present the exact validation errors to the operator
    2. Do not commit the invalid YAML
    3. Document the validation issues in `.ai/tasks/{{ task_id }}/stabilize-notes.md
    4. Request directions from the operator on how to proceed

**Test Summary / Evidence Format:**

- When updating `.ai/tasks/{{ task_id }}.yaml` evidence, use the OBJECT variant for `evidence.testSummary` (see
  `.ai/schemas/task-file.schema.v0.1.json`) so evidence is structured and machine-readable.
- If no tests are executed because the project does not build or the task is non-code, set `evidence.testSummary` to
  an object containing a `notes` field describing what checks were run (for example, linters) and include counts
  where available (e.g., `lintErrors: 0`). Example minimal object when tests are not run:
    ```yaml
    evidence:
      testSummary:
        integrationTest:
          failed: 0
          tests: 0
        notes: "No tests were run because the project does not build or the task is non-code; linters passed."
        test:
          failed: 0
          tests: 0
    ```

**When executing stabilization steps:**

- Validate `.ai/tasks/{{ task_id }}/scaffold.yaml` and ensure the branch is checked out.
- Run linters and static analysis first. Capture and summarize output.
- Only run unit/integration tests if `acceptance.commands` or project metadata indicates tests are expected;
  otherwise, skip tests and record this fact in `.ai/tasks/{{ task_id }}/stabilize-notes.md` and in the stabilize
  artifacts: `.ai/tasks/{{ task_id }}/stabilize.yaml` and `.ai/tasks/{{ task_id }}/stabilize-report.md`.
- Pass is expected to be iterative and incremental, always depending on the outcome of the tests and static analysis.
- For each iterative fix, commit using the Conventional Commits format; see the
  [commit instructions](../git-commit-instructions.md) for details. Commit `type` should be one of either `fix`,
  `refactor`, or `chore`, depending on the nature of the change.

**Updating the task file and PR creation:**

- After stabilization completes successfully (or acceptable exception is recorded), update
  `.ai/tasks/{{ task_id }}.yaml`:
    - set `status: in_review`
    - append an `evidence` entry containing:
        - timestamp
        - branch name
        - commit SHAs (list: scaffold commits + stabilize commits)
        - `testSummary` as an OBJECT (structured per `.ai/schemas/task-file.schema.v0.1.json`)
        - optional `ciRunUrl` and `prUrl` when available
- Commit the updated task file using the Conventional Commits format; see the
  [commit instructions](../git-commit-instructions.md) for details. Summary description should indicate task status
  being updated (e.g., `chore: update task status to in_review`).
- Push the branch and open a PR (use `branch_plan` base if provided); include links to `.ai/tasks/{{ task_id }}/`
  in the PR body.

**Operational Notes/Safety:**

- This instruction file complements `.github/prompts/stabilize-pass.prompts.md` and provides higher-level guidance
  for the stabilization pass that can be reused across tasks.
- If stabilization requires infrastructure changes, secrets, or modifications outside the allowed files, stop and
  request operator guidance.
- Keep stabilization notes in `.ai/tasks/{{ task_id }}/stabilize-notes.md` for auditing and future reference.
