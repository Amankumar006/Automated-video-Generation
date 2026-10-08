"""Module execution entrypoint for python3 -m aether.director."""

import sys
from aether.director.cli import main

if __name__ == "__main__":
    sys.exit(main())
