---
description: "Create a reviewable spec (plan) for a single task using the project's 3-pass workflow."
write_spec_artifact: true
---

## Context to load

- Read these governing documents first and follow them exactly:
    - `docs/PLANNING.md`
    - `docs/TASKS.md`
- The agent must ask the operator for the exact task file path to process (e.g., `.ai/tasks/SEC-001.yaml`). Do not
  assume a task file-request it if not provided.

## Task

Produce a concise, review-ready "spec" (plan) describing the planned diffs for the requested task. The spec must:

- list the exact file diffs you propose (file paths and the regions/lines or clear markers),
- explain why each change is required, and
- describe the branch/commit plan that will be used if the spec is approved.

Do not make edits to existing code yet. This pass only produces the planned diffs and any clarifying questions.

## Constraints

- This spec pass must be generic-do NOT reference any specific task file by default.
- Existing repository files must remain unchanged in this pass (except optionally writing spec artifacts under
  `.ai/tasks/{{ task_id }}/` when `write_spec_artifact: true`, see the associated
  [instructions](../instructions/spec-pass.instructions.md)).
- The output must be limited to the planned diffs and a short list of QUESTIONS (if any).
- Do not include running tests or builds in this pass; these are handled in later passes.

## Instructions (execute in order)

1. Confirm you can read the governing documents listed in "Context to load".
2. Ask the operator for the exact task file path to be processed (relative to the repository root).
3. Once provided, read the task file and summarize its acceptance criteria in one paragraph.
4. Produce a list of planned diffs. For each planned change, include:

- file path
- a brief description of the change
- an approximate region or marker (e.g., "add new class X in `src/tools/x.py` after import statements")
- a short justification tying the change to the task's acceptance criteria

5. If `write_spec_artifact: true` is in the prompt header, write two artifacts to the repo under
   `.ai/tasks/{{ task_id }}/`:

- `spec.yaml` - a machine-readable YAML spec following the project's schema
  (`.ai/schemas/spec-artifact.schema.v0.1.json`)
- `planned-diffs.md` - a human-friendly planned-diffs document with small unified-diff sketches or clear edit
  markers. Note: writing artifacts is permitted in this pass, but do NOT commit them until the operator approves the
  spec and instructs the agent to create the task branch (see step 6).

6. Describe the branch and commit plan to be executed upon approval (branch name pattern, first commit must be the
   updated task file with status changed to `in_progress` and a note; include that the `*.yaml` artifacts under
   `.ai/tasks/{{ task_id }}/` will be committed together with the updated task file as part of the FIRST commit on
   the new branch).
7. Provide 1–3 QUESTIONS for the operator if any conventions or task details are ambiguous.
8. Wait for operator approval before creating branches or committing any files.

## Acceptance Criteria

- The output contains a clear, reviewable list of planned diffs (file paths and descriptions) that map to the task
  acceptance criteria.
- The branch/commit plan is specified (branch name pattern, required first commit of the task file to `in_progress`,
  and artifacts committed alongside the task file).
- The agent asked for the task file path and did not modify any existing repository files except optionally writing
  artifacts under `.ai/tasks/{{ task_id }}/` when `write_spec_artifact: true`.

## Output

A concise spec consisting of:

- One-paragraph summary of the task's acceptance criteria
- The planned diffs (list of file paths with descriptions and markers)
- Branch and commit plan
- 1–3 QUESTIONS (if any)
