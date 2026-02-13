"""
Entry point for running the package as a module: python -m yazio_exporter
"""

import sys

from yazio_exporter.cli import main

if __name__ == "__main__":
    sys.exit(main())
