"""CLI/system integration coverage tests."""

from __future__ import annotations

import argparse
import runpy
from collections.abc import Callable

import pytest

from ornata.cli import main as cli_main


def _build_stub_parser(callback: Callable[[argparse.Namespace], None]) -> argparse.ArgumentParser:
    """Create a parser that always calls ``callback`` when parsed.

    :param callback: Callable invoked once ``parse_args`` completes.
    :type callback: Callable[[argparse.Namespace], None]
    :return: Configured argparse parser for tests.
    :rtype: argparse.ArgumentParser
    """

    parser = argparse.ArgumentParser(prog="ornata-test")
    parser.set_defaults(func=callback)
    return parser


def test_cli_main_missing_command_returns_parse_error() -> None:
    """Ensure ``cli.main`` surfaces parser errors for missing commands.

    :return: None.
    :rtype: None
    """

    exit_code = cli_main.main([])
    assert exit_code != 0


def test_cli_main_executes_stub_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify ``cli.main`` executes a provided command and succeeds.

    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: pytest.MonkeyPatch
    :return: None.
    :rtype: None
    """

    calls: list[argparse.Namespace] = []

    def _command(args: argparse.Namespace) -> None:
        """Record parsed arguments for assertions."""

        calls.append(args)

    def _fake_build_parser() -> argparse.ArgumentParser:
        """Return a stub parser that points to ``_command``.

        :return: Parser configured for the test command.
        :rtype: argparse.ArgumentParser
        """

        return _build_stub_parser(_command)

    monkeypatch.setattr(cli_main, "build_parser", _fake_build_parser)
    exit_code = cli_main.main([])
    assert exit_code == 0
    assert calls, "Command callback was never invoked"


def test_cli_main_returns_error_for_command_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure ``cli.main`` maps command exceptions to exit code ``1``.

    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: pytest.MonkeyPatch
    :return: None.
    :rtype: None
    """

    def _command(_: argparse.Namespace) -> None:
        """Raise an exception to trigger the error path."""

        raise RuntimeError("boom")

    def _fake_build_parser() -> argparse.ArgumentParser:
        """Provide a parser wired to the failing command.

        :return: Parser configured for the test command.
        :rtype: argparse.ArgumentParser
        """

        return _build_stub_parser(_command)

    monkeypatch.setattr(cli_main, "build_parser", _fake_build_parser)
    exit_code = cli_main.main([])
    assert exit_code == 1


def test_cli_main_handles_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure ``cli.main`` returns ``1`` when commands raise ``KeyboardInterrupt``.

    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: pytest.MonkeyPatch
    :return: None.
    :rtype: None
    """

    def _command(_: argparse.Namespace) -> None:
        """Raise ``KeyboardInterrupt`` to simulate ctrl+c."""

        raise KeyboardInterrupt()

    def _fake_build_parser() -> argparse.ArgumentParser:
        """Provide a parser wired to the keyboard interrupt simulation.

        :return: Parser configured for the test command.
        :rtype: argparse.ArgumentParser
        """

        return _build_stub_parser(_command)

    monkeypatch.setattr(cli_main, "build_parser", _fake_build_parser)
    exit_code = cli_main.main([])
    assert exit_code == 1


def test_cli_dunder_main_propagates_cli_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate ``python -m ornata.cli`` uses the CLI exit code.

    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: pytest.MonkeyPatch
    :return: None.
    :rtype: None
    """

    expected_exit = 3

    def _fake_main(_: list[str]) -> int:
        """Return a sentinel exit code for assertions.

        :param _: Ignored CLI argv from ``__main__``.
        :type _: list[str]
        :return: Sentinel exit code.
        :rtype: int
        """

        return expected_exit

    monkeypatch.setattr("ornata.cli.main.main", _fake_main)
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("ornata.cli.__main__", run_name="__main__")
    assert exc_info.value.code == expected_exit


def test_package_dunder_main_routes_through_api_exports(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure ``python -m ornata`` delegates to the API export shim.

    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: pytest.MonkeyPatch
    :return: None.
    :rtype: None
    """

    expected_exit = 7

    import ornata.api.exports.cli as cli_exports

    def _fake_main(_: list[str]) -> int:
        """Return a sentinel exit code for assertions.

        :param _: Ignored CLI argv from ``ornata.__main__``.
        :type _: list[str]
        :return: Sentinel exit code.
        :rtype: int
        """

        return expected_exit

    monkeypatch.setattr(cli_exports, "main", _fake_main)
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("ornata.__main__", run_name="__main__")
    assert exc_info.value.code == expected_exit
