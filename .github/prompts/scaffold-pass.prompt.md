---
description: "Apply the planned diffs from a spec artifact and produce a scaffold report."
read_spec_artifact: true
write_scaffold_artifact: true
---

## Context to load

- Read these governing documents:
    - `docs/PLANNING.md`
    - `docs/TASKS.md`
    - `.ai/tasks/{{ task_id }}.yaml`
    - `.ai/tasks/{{ task_id }}/spec.yaml` (machine-readable spec artifact)
- Validate the machine-readable spec against: `.ai/schemas/task-file.schema.v0.1.json`

## Task

Take a previously approved spec artifact and apply the planned diffs to the repository. Produce a short scaffold
report documenting the applied diffs and commit SHAs.

## Constraints

- If not provided, ask the operator for the TASK ID or the path to the spec artifact.
- Do NOT modify files outside the union of:
    - files listed in `planned_diffs` inside the spec artifact
    - the `.ai/tasks/{{ task_id }}/` directory
- The scaffold pass must run on the task branch which must already exist and be checked out by the agent. If not
  already on the task branch, stop and request the branch name.
- All commits created by the scaffold pass MUST follow the Conventional Commits format as described in
  [the commit instructions](../git-commit-instructions.md).
- When attempting to resolve ambiguous markers or locations for `modify` diffs, make at most 3 targeted attempts before
  falling back to a TODO marker and recording a QUESTION in the scaffold report.

## Instructions (execute in order)

1. Confirm you can read the governing documents and the spec schema.
2. Ask the operator for the TASK ID or spec path.
3. Load and validate the spec artifact at `.ai/tasks/{{ task_id }}/spec.yaml` against
   `.ai/schemas/spec-artifact.schema.v0.1.json`. Use `.ai/tools/validate_yaml.py` to perform the validation. If
   validation fails, present errors and stop.
4. Confirm the current git branch matches `branch_plan.initial_branch_name` from the spec. If it does not, stop and
   ask the operator to check out the correct branch.
5. For each entry in `planned_diffs` (in order):

- If `change` == `add`: create the file and insert the content or marker-specified addition. If no content is
  provided in the spec, create a clear placeholder with a TODO and a short comment explaining what's expected.
- If `change` == `modify`: locate the `marker` in the target file. If the marker is clear, apply the modification
  inline. If the marker is ambiguous or missing, do NOT guess; instead add a TODO marker in the file and record a
  question in the report.
    - Limit yourself to at most three targeted attempts to locate a suitable marker or region; after that, insert a TODO
      marker and record a QUESTION instead of guessing.
- If `change` == `delete`: remove the file.
- If `change` == `rename`: rename the file as specified (include both old and new paths in the spec's `file` field;
  if missing, record a question and skip).
- After applying each file change, stage and commit the change with a Conventional Commit message.

6. After all diffs are processed, write two artifact files under `.ai/tasks/{{ task_id }}/`:

- `scaffold.yaml` - (machine-readable) containing applied diffs and their commit SHAs
- `scaffold-report.md` - (human-friendly) containing:
    - summary header (task_id, author, created_at from spec)
    - list of applied diffs with commit SHA for each
    - any QUESTIONS or unresolved markers
    - timestamp and agent identity

7. Stage and commit the scaffold artifacts with a Conventional Commit message:
   `chore({{ task_id }}): add scaffold artifacts`.
8. Present a concise summary to the operator with the list of commits and any QUESTIONS. Wait for the operator to
   review before proceeding to stabilize.

## Acceptance Criteria

- All planned diffs from the validated spec were applied or explicitly recorded as unresolved.
- Each applied diff produced a separate Conventional Commit with a descriptive message that includes the
  `{{ task_id }}` in the message footer.
- `.ai/tasks/{{ task_id }}/scaffold.yaml` and `.ai/tasks/{{ task_id }}/scaffold-report.md` exist and document
  applied diffs, commit SHAs, and questions.
- No files outside the allowed set were modified.

## Output

- A brief summary listing the commits created and amy QUESTIONS that need operator input.
