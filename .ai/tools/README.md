## validate_markdown.py

Validate that a Markdown file contains required level-two headings (## <SECTION>), case-insensitive.

Usage:

- List required sections with multiple -s flags
- Exits 0 when all sections are present, 1 otherwise

Example:

```
python3 tools/validate_markdown.py -s "validate_markdown.py" -s "validate_yaml.py" tools/README.md
```

Using with uv:

```
uv run python3 tools/validate_markdown.py -s "validate_markdown.py" -s "validate_yaml.py" tools/README.md
```

## validate_yaml.py

Validate a YAML file against a JSON Schema (Draft 2020-12) using PyYAML and jsonschema.

Usage:

```
python3 tools/validate_yaml.py <yaml_file> <schema_file>
```

Behavior:

- Prints "OK" and exits 0 when the YAML instance is valid
- Prints one error per line and exits 1 when invalid

Using with uv:

```
uv run python3 tools/validate_yaml.py <yaml_file> <schema_file>
```

References:

- jsonschema documentation: https://python-jsonschema.readthedocs.io/
- PyYAML documentation: https://pyyaml.org/wiki/PyYAMLDocumentation
