"""Module execution entry for `python -m ornata.cli`."""

from __future__ import annotations

import sys

from ornata.cli.main import main as cli_main

if __name__ == "__main__":
    try:
        code = cli_main(sys.argv[1:])
        raise SystemExit(code)
    except SystemExit as _se:
        raise
    except Exception as _exc:
        raise SystemExit(1) from _exc
