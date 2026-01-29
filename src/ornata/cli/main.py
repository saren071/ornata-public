"""Ornata command-line entry point (modular)."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from collections.abc import Sequence


class _Parser(argparse.ArgumentParser):

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        raise SystemExit()


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="ornata", description="Ornata CLI utilities")
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Register commands from submodules
    # TODO: Add commands

    _add_parser = subparsers.add_parser # TODO: remove _ once using parser call

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        try:
            args.func(args)
        except Exception:
            return 1
        except KeyboardInterrupt:
            return 1
        return 0
    except SystemExit as se:
        # Normalize Windows subprocess handle errors into non-zero exit rather than raising
        try:
            code = int(se.code) if isinstance(se.code, int) else 1
        except Exception:
            code = 1
        return code


if __name__ == "__main__":
    raise SystemExit(main())
