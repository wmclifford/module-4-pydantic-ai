#!/usr/bin/env python3
"""Main entry point for the web search agent CLI."""

import argparse
import sys


def main():
    """Main entry point for the web search agent CLI."""
    parser = argparse.ArgumentParser(
        description="Web Search Agent - Perform web searches using AI"
    )
    parser.add_argument(
        "--version", action="version", version="Web Search Agent 0.1.0"
    )
    parser.add_argument(
        "--help", "-h", action="help", help="Show this help message and exit"
    )

    # For now, just print help if no arguments are provided
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    # Parse arguments
    args = parser.parse_args()

    # TODO: Implement actual CLI functionality
    print("Web Search Agent CLI - Implementation pending")
    return 0


if __name__ == "__main__":
    sys.exit(main())
