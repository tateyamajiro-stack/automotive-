"""Entry point for ``python -m hils_manager``."""

import sys

from hils_manager.app import run


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
