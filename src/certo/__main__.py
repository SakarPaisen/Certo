"""Enables `python -m certo "<task>"`."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
