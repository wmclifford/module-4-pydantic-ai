# Architecture Decision Records (ADR)

This file records significant deviations from the standard workflow, architecture, or conventions.

## When to add an ADR

Create an ADR entry when:

- deviating from the documented 3-pass workflow,
- changing core architecture or cross-cutting patterns,
- introducing or removing major dependencies or infrastructure,
- making exceptions to security or evidence policies.

## Format

Append a new section for each decision using this template:

### ADR-{{ id }}: {{ short-title }}

- **Date:** {{ YYYY-MM-DD }}
- **Status:** proposed \| accepted \| superseded
- **Related tasks:** {{ task IDs or `n/a` }}
- **Context:**
    - Briefly describe the situation and why a change or exception is needed.
- **Decision:**
    - Describe the decision that was made.
- **Consequences:**
    - List the positive and negative consequences of this decision, including technical debt and follow-up work.
- **Rollback Plan:**
    - Describe how to revert this decision if necessary.
- **Approval:**
    - Person or role approving this decision (owner-driven by default).

Example:

### ADR-001: Switch to new configuration backend

- **Date:** 2025-01-01
- **Status:** accepted
- **Related tasks:** CFG-001
- **Context:**
    - The existing configuration system cannot support per-tenant overrides.
- **Decision:**
    - Adopt `pydantic`-based settings with environment-driven overrides.
- **Consequences:**
    - \+ More flexible configuration.
    - \- Requires migration of existing configs and additional tests.
- **Rollback Plan:**
    - Keep the old configuration loader behind a feature flag for one release.
- **Approval:**
    - Repository owner
