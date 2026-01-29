from __future__ import annotations


def warn(msg: str) -> None:
    from ornata.api.exports.definitions import LAST_STYLING_WARNINGS
    LAST_STYLING_WARNINGS.append(msg)


def error(msg: str) -> None:
    from ornata.api.exports.definitions import LAST_STYLING_ERRORS
    LAST_STYLING_ERRORS.append(msg)


def last_errors() -> list[str]:
    from ornata.api.exports.definitions import LAST_STYLING_ERRORS
    return list(LAST_STYLING_ERRORS)


def last_warnings() -> list[str]:
    from ornata.api.exports.definitions import LAST_STYLING_WARNINGS
    return list(LAST_STYLING_WARNINGS)


def clear() -> None:
    from ornata.api.exports.definitions import LAST_STYLING_ERRORS, LAST_STYLING_WARNINGS
    LAST_STYLING_ERRORS.clear()
    LAST_STYLING_WARNINGS.clear()
