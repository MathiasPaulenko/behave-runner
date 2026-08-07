"""Entry point for python -m behave_runner."""

from __future__ import annotations

from behave_runner.cli.app import app


def main() -> None:
    """Console script entry point."""
    app()


if __name__ == "__main__":
    main()
