# Conventional Commits

> Machine-readable summary

```yaml
project:
  name: ai-agent-mastery-course
  commit_header_case: "lower-case"
  commit_types: [ "feat", "fix", "docs", "style", "refactor", "test", "chore", "perf", "build", "ci", "revert" ]
  breaking_change_indicator: "!"
  task_reference: "Refs: [<TASK-ID>]"
```

See [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for full documentation.

**Format:**

```markdown
<type>(<optional scope>): <description>

[optional body]

Refs: [<TASK-ID>]
```

- Scope guidance: use scope to indicate the slice/component of the repository you changed (e.g., `docs`, `ci`,
  `governance`, `schemas`, `templates/java`, `examples`). Do NOT use the Task ID as scope; reference the Task ID in the
  commit footer using `Refs: <TASK-ID>`.
- Task IDs: Will be automatically generated as part of our development workflow and will follow a pre-defined schema.
  The format will be defined in the schema for the YAML task files.

**Body:**

- Use the imperative, present tense: "change" not "changed" nor "changes"
- Use bullet points for the body
- Wrap lines at 100 characters
- When only changing documentation, include `[ci skip]` in the commit body on its own line
- Always include the `Refs: [<TASK-ID>]` footer when a task ID is available (for audit purposes and changelog
  generation)

**Types:**

- `feat`: new feature
- `fix`: bug fix
- `docs`: documentation
- `style`: formatting, missing semicolons, etc.; no code change
- `refactor`: refactoring production code
- `test`: adding tests, refactoring test; no production code change
- `chore`: updating build tasks, package manager configs, etc; no production code change
- `perf`: performance improvements
- `revert`: reverting a previous commit
- `build`: changes that affect the build system or external dependencies
- `ci`: changes to our CI configuration files and scripts

**Miscellaneous:**

- `BREAKING CHANGE:` in the commit body, when the commit introduces a breaking change
- [TASK-ID]: the category ID, e.g. `[PAG-002]`
- Use `!` after scope to mark breaking change, per spec: `feat(api)!: ...`
- Use actual line feeds when generating commit messages; do not use `\n` in the message. This is
  important when using `git commit -m` to generate a commit message.
