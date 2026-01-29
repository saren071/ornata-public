"""Shared pytest fixtures and helpers for Ornata tests."""
from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
DATA_DIR: Final[Path] = REPO_ROOT / "tests" / "data"


def _resolve_data_dir_path(repo_root: Path) -> Path:
    """Return the canonical data directory path, ensuring it exists.

    :param repo_root: Repository root path.
    :type repo_root: Path
    :return: Absolute path to the shared test data directory.
    :rtype: Path
    :raises FileNotFoundError: If the data directory has not been created.
    """

    data_path = repo_root / "tests" / "data"
    if not data_path.exists():
        msg = f"Missing test data directory: {data_path}"
        raise FileNotFoundError(msg)
    return data_path


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the absolute repository root.

    :return: Repository root path.
    :rtype: Path
    """
    return REPO_ROOT


@pytest.fixture(scope="session")
def data_dir(repo_root: Path) -> Path:
    """Return the shared data directory path.

    :param repo_root: Repository root fixture.
    :type repo_root: Path
    :return: Data directory path.
    :rtype: Path
    """
    return _resolve_data_dir_path(repo_root)
