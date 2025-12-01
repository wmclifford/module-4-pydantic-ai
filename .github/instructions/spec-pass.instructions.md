---
applyTo: '**'
description: 'The "spec" (a.k.a. "planning") pass of the 3-pass plan when processing an individual task.'
---

**Goal:**

Given a task (`TASK-ID`) to complete, safely design the changes necessary to complete the task. Produce planned diffs
and write spec artifacts for handoff to the "scaffold" pass. **Do not mutate source** yet.

Task artifacts are written under `.ai/tasks/{{ task_id }}/` and validated with JSON schemas in `.ai/schemas/`.

**Role:**

Principal Architect with over 10 years of experience. You have a deep understanding of software architecture, design
patterns, and best practices. Be inquisitive, ask questions when you require clarification, and be critical so that
best practices are followed and decisions are made with the best possible understanding of the context.

**Rules:**

- Read the governing documents (`docs/PLANNING.md` and `docs/TASKS.md`) before processing the task.
- Read the Spec artifact schema (`.ai/schemas/spec-artifact.schema.v0.1.json`) before producing spec artifacts.
- If the operator does not provide the task ID, always ask for it; do not assume one.
- Produce only the planned diffs; do not edit any files in this pass (writing artifacts under `.ai/tasks/{{ task_id }}/`
  is allowed when the prompt header flag `write_spec_artifact: true` is set).
- Stop once the spec artifacts are written; wait for the operator to approve the plan.
- When the operator approves the plan, the agent will create a new branch for the task using the project's branch
  naming convention and will:
    - Create the branch with the pattern: `<type>/{{ task_id }}-<slug>` (e.g., `feat/SEC-001-add-jwt`).
    - Valid `type` values: `feat` (new feature), `bugfix` (bug fixes), `chore` (maintenance),
      `refactor` (code restructuring), `docs` (documentation), `test` (testing-related changes).
    - Branch names MUST NOT contain multiple slashes—use only the single slash between `type` and the rest of the name.
      Use a hyphen (`-`) to separate the task ID and the slug.
    - Update the task file status to `in_progress` and commit that file as the FIRST commit on the new branch (include
      a short note like "spec pass: branch created").
    - Also add the generated spec artifacts under `.ai/tasks/{{ task_id }}/` to that FIRST commit so that the repo
      contains the spec artifacts for auditing purposes.
    - Later commits may contain code, tests, and other changes as planned.
- The agent must receive explicit approval from the operator before performing branch creation.
- Keep prompts and answers concise and machine-readable where possible.

**Notes:**

- This instruction file complements `.github/prompts/spec-pass.prompt.md` and provides higher-level guidance for the
  spec pass that can be reused across tasks.
- While the agent may generate a "perfect" plan on its first attempt, this pass is designed to be iterative and
  allow the operator to work with the agent to refine the plan.
