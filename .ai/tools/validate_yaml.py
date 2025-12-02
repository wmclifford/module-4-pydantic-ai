#!/usr/bin/env python3
"""
validate_yaml.py — Validate a YAML file against a JSON Schema (Draft 2020-12).

- Uses PyYAML for YAML parsing (yaml.safe_load)
- Uses jsonschema Draft202012Validator for validation
- CLI requires two positional args: <yaml_file> <schema_file>
- Prints 'OK' when valid, otherwise prints each error on its own line

Exit codes:
  0 - valid
  1 - invalid (missing file, parse errors, or schema validation errors)

Version: 0.1.0
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import yaml  # type: ignore
from jsonschema import Draft202012Validator, ValidationError  # type: ignore

__version__ = "0.1.0"

logger = logging.getLogger(__name__)


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="validate_yaml",
        description=(
            "Validate a YAML file against a JSON Schema (Draft 2020-12). "
            "Provide two positional arguments: <yaml_file> <schema_file>."
        ),
    )
    parser.add_argument("yaml_file", help="Path to the YAML file to validate.")
    parser.add_argument(
        "schema_file", help="Path to the JSON Schema file (Draft 2020-12)."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    ns = parser.parse_args(list(args))
    return ns


def read_text(path: Path | str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8")


def read_yaml(path: Path | str):
    """Read YAML file to Python data using yaml.safe_load.

    Raises FileNotFoundError if the file does not exist.
    Propagates yaml.YAMLError for YAML syntax issues.
    """
    text = read_text(path)
    return yaml.safe_load(text)


def read_json(path: Path | str):
    """Read JSON file to Python data using json.loads.

    Raises FileNotFoundError if the file does not exist.
    Propagates json.JSONDecodeError for JSON syntax issues.
    """
    text = read_text(path)
    return json.loads(text)


def _format_error_path(err: ValidationError) -> str:
    # Prefer absolute_path for clarity; join tokens to a dotted path; use <root> for empty
    parts = [str(p) for p in err.absolute_path]
    return ".".join(parts) if parts else "<root>"


def format_errors(errors: Iterable[ValidationError]) -> List[str]:
    """Format jsonschema.ValidationError objects into human-readable lines."""
    lines: List[str] = []
    for e in errors:
        path = _format_error_path(e)
        lines.append(f"{path}: {e.message}")
    # Sort for deterministic output
    lines.sort()
    return lines


def validate_instance(instance, schema) -> Tuple[bool, List[ValidationError]]:
    """Validate instance against schema; return (valid, list_of_errors)."""
    validator = Draft202012Validator(schema)
    errs = list(validator.iter_errors(instance))
    return (len(errs) == 0, errs)


def validate_yaml_against_schema(
    yaml_path: Path | str, schema_path: Path | str
) -> Tuple[bool, List[str]]:
    """High-level validation wrapper returning (valid, error_lines)."""
    try:
        instance = read_yaml(yaml_path)
    except FileNotFoundError:
        return False, [f"file: YAML file not found: {yaml_path}"]
    except yaml.YAMLError as e:  # type: ignore
        return False, [f"yaml: {getattr(e, 'problem_mark', '')} {e}"]

    try:
        schema = read_json(schema_path)
    except FileNotFoundError:
        return False, [f"schema: Schema file not found: {schema_path}"]
    except json.JSONDecodeError as e:
        return False, [f"schema: JSON parse error at pos {e.pos}: {e.msg}"]

    valid, errors = validate_instance(instance, schema)
    if valid:
        return True, []
    return False, format_errors(errors)


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    logging.basicConfig(level=logging.INFO)

    ns = parse_args(argv)

    yaml_file = ns.yaml_file
    schema_file = ns.schema_file

    valid, error_lines = validate_yaml_against_schema(yaml_file, schema_file)

    if valid:
        print("OK")
        return 0
    else:
        for line in error_lines:
            print(line)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
