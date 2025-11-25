# CI/CD Instructions

> Machine-readable summary

```yaml
project:
  name: ai-agent-mastery-course
  ci_checks:
    - commitlint
    - markdownlint
    - prettier
    - gitleaks
    - schema_validation
    - linkcheck
  secrets_scan: true
  releases: semantic-release
  branch_policy: "trunk-based (squash merges, PR required, commitlint titles)"
  approval_model: "owner-driven"
```

This document outlines the CI/CD policies and procedures for this repository.

## CI Checks

Our CI pipeline focuses on validation, linting, security scanning, and publishing of repo-level artifacts. All PRs that
change governance, templates, schemas, or `.github/workflows` must pass the following checks:

- **commitlint**: Validate commit messages on push/PR
- **markdownlint**: Lint docs and templates (fail on serious issues)
- **prettier/check-format**: Ensure formatting of code/markdown/YAML
- **gitleaks**: Secrets scan focused on changed files (templates, docs, workflows)
- **schema-validation**: Validate task files against the task file schema
- **linkcheck/site**: Optional link checking for docs and READMEs

## CI Behavior and Gating

- Block merges on any failure by using branch protection rules
- For speed, run fast checks (commitlint, quick lint) early
- Run heavier checks (schema validation, full gitleaks) in a subsequent job or in a PR `check` job
- Use matrix jobs to parallelize format/lint/security checks

## Build & CI Policies

- Lint rules auto-fix where possible; remaining violations block PR
- PR is **required** to merge to `main`
- CI **must** pass before merging
- **Trunk-based** development with squash merges to `main`
- PR title must be a Conventional Commit
- Include `Refs: [TASK-ID]` in the PR footer

## Secrets & Credentials

- **Never** store secrets in source code, configuration files, or documentation; use repository secrets instead
- Store tokens in repository or organization secrets (GitHub Actions secrets)
- Do not print secrets in logs
- Use `ACTIONS_STEP_DEBUG` carefully and avoid revealing secrets
- Prefer scoped tokens (repo-level or fine-grained tokens) and rotate them regularly
- Use short-lived tokens and least privilege for automation
- For publishing or automation that requires long-lived credentials, store them in an organization-level secrets store
  and rotate regularly
- For publishing actions/releases, use a separate deploy token with limited scope and store it as a repo secret

## Branch Protection

- Protect sensitive branches (`main`) with branch protection rules:
    - Require PRs
    - Require passing status checks
    - Require reviews
    - Limit who can push directly

## Evidence & Audit in CI

- Completed tasks must have `evidence.commit` set to the code SHA present in the repository:
    - Before the PR is merged, this will be the SHA of the PR branch commit referenced in the task file
    - After the PR is merged, this will be the SHA of the squashed commit on the `main` branch
- `evidence.prUrl` should reference the PR URL for the audit trail
- `evidence.ciRunUrl` may remain empty for this repo (it does not build artifacts), but templates that include CI should
  prefer linking to the CI run for traceability

## Releases & Publishing

- Use `semantic-release` (or similar) for automatic changelog and release tagging where appropriate
- Publishing reusable GitHub Actions from this repo:
    - Store action definitions under `.github/actions/<action-name>` or a top-level `actions/` directory
    - Use version tags and `semantic-release` to publish tags and update `action.yml` references accordingly
    - Publishing requires a repo token with `contents: write` and `packages: write` where applicable; prefer short-lived
      deploy tokens and store them as repository/organization secrets

## Validation Tooling

- Task-file validator and other enforcement tooling are expected to live in a separate tooling repo
- Example validators:
    - Task schema validation (JSON/YAML schema check)
    - Task status and evidence checks (ensures `evidence.commit` present when required)
    - Documentation link and build checks

## Observability & Monitoring

- Include basic monitoring via CI job success/failure notifications (Slack, email) as part of downstream projects that
  consume the templates
- Encourage template consumers to add health and observability guidance in their template READMEs
