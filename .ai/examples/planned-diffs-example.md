# Planned Diffs for EXAMPLE-001

## Summary

This task adds a new configuration file and updates the README to document it.

## Planned Changes

### 1. Add new configuration file

**File:** `config/new-config.yaml`
**Change:** Add
**Justification:** Required by acceptance criteria to add new configuration

```yaml
# New configuration file
database:
  host: localhost
  port: 5432
  name: example_db
```

### 2. Update README with configuration documentation

**File:** `README.md`
**Change:** Modify
**Marker:** `## Configuration`
**Justification:** Required by acceptance criteria to document new configuration

```markdown
## Configuration

The application can be configured using the `config/new-config.yaml` file.
```
