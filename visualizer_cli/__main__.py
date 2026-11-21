"""Entry point for ``python -m visualizer_cli``."""

from __future__ import annotations

import sys

from visualizer_cli.cli import main

if __name__ == "__main__":
    sys.exit(main())
