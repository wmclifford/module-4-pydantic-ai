#!/usr/bin/env python3
"""
validate_markdown.py — Simple Markdown validator for required H2 sections.

- Uses only the Python standard library
- CLI: validate a markdown file contains required level-two headings (## <SECTION>)
- Case-insensitive comparison for section names

Exit codes:
  0 - valid
  1 - invalid (missing file or missing required sections)

Version: 0.1.0
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple

__version__ = "0.1.0"

logger = logging.getLogger(__name__)


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="validate_markdown",
        description="Validate that a Markdown file contains required H2 sections (## <SECTION>).",
    )
    parser.add_argument(
        "markdown_file",
        help="Path to the Markdown file to validate.",
    )
    parser.add_argument(
        "-s",
        "--section",
        action="append",
        dest="sections",
        required=True,
        help="Expected section name (H2). Provide multiple times for multiple sections.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    ns = parser.parse_args(list(args))
    # Ensure at least one section provided (argparse required=True handles this, but keep explicit check)
    return ns


def read_text(path: Path | str) -> str:
    p = Path(path)
    # Will raise FileNotFoundError naturally if missing
    return p.read_text(encoding="utf-8")


def _normalize_section_name(name: str) -> str:
    # Normalize for case-insensitive comparison: strip and lower
    return name.strip().lower()


def extract_h2_sections(markdown_text: str) -> Set[str]:
    """Extract H2 section names from Markdown text.

    Rules:
    - H2 lines start with exactly two '#' characters ('##'). Spaces after '##' are optional.
    - Ignore headings of levels other than H2.
    - Strip trailing '#' markers and surrounding whitespace from the heading text.
    - Return the set of normalized (lower-cased) section names for comparison.
    """
    sections: Set[str] = set()
    for line in markdown_text.splitlines():
        s = line.strip()
        if not s.startswith("##"):
            continue
        # Ensure it's H2 and not H3+; next char after '##' must not be '#'
        if len(s) >= 3 and s[2] == "#":
            # This is ### (H3) or higher — skip
            continue
        # Remove leading '##' and optional space
        remainder = s[2:]
        remainder = remainder.lstrip()
        # Trim trailing ' #' patterns and whitespace
        remainder = remainder.rstrip().rstrip("#").rstrip()
        if remainder:
            sections.add(_normalize_section_name(remainder))
    return sections


def validate_sections(
    found_sections: Iterable[str], expected_sections: Iterable[str]
) -> Tuple[bool, Set[str]]:
    """Validate expected sections are all present in found sections.

    Comparison is case-insensitive; both sides are normalized to lower-case.

    Returns (valid, missing_set_lowercased)
    """
    found_norm = {_normalize_section_name(s) for s in found_sections}
    expected_norm = {_normalize_section_name(s) for s in expected_sections}
    missing = {s for s in expected_norm if s not in found_norm}
    return (len(missing) == 0, missing)


def validate_markdown_file(
    path: Path | str, expected_sections: Sequence[str]
) -> Tuple[bool, Set[str]]:
    """Validate the markdown file exists and contains all expected H2 sections.

    Returns (valid, missing_sections_lowercased)
    """
    try:
        text = read_text(path)
    except FileNotFoundError:
        return (
            False,
            {_normalize_section_name(s) for s in expected_sections}
            if expected_sections
            else set(),
        )

    found = extract_h2_sections(text)
    return validate_sections(found, expected_sections)


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    logging.basicConfig(level=logging.INFO)

    ns = parse_args(argv)
    md_file = ns.markdown_file
    expected_sections: List[str] = ns.sections

    valid, missing = validate_markdown_file(md_file, expected_sections)

    if valid:
        logger.info("Markdown validation succeeded: all required sections present.")
        return 0
    else:
        if missing:
            logger.error(
                "Markdown validation failed: missing required sections: %s",
                ", ".join(sorted(missing)),
            )
        else:
            logger.error("Markdown validation failed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
