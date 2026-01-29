"""
# CLI Entry Point

Entry point for the Ornata CLI when executed as a module (e.g., `python -m ornata`).
Passes command line arguments to `ornata.api.exports.cli.main`.

### Usage
```bash
python -m ornata --help
```
"""

from ornata.api.exports.cli import main

if __name__ == "__main__":
    # Same programmatic fallback for `python -m ornata`
    import sys as _sys

    try:
        raise SystemExit(main(_sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as _exc:
        raise SystemExit(1) from _exc