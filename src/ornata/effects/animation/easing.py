"""Easing functions for animations."""

from collections.abc import Callable
from math import cos, pi, sin, sqrt

type EasingFunction = Callable[[float], float]


def linear_easing(t: float) -> float:
    """Linear easing function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return t


def ease_in_quad(t: float) -> float:
    """Quadratic ease-in function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return t * t


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return t * (2 - t)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t


def ease_in_cubic(t: float) -> float:
    """Cubic ease-in function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return t * t * t


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    t -= 1
    return t * t * t + 1


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    if t < 0.5:
        return 4 * t * t * t
    t -= 1
    return (t * t * t * 4) + 1


def ease_in_quart(t: float) -> float:
    """Quartic ease-in function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return t * t * t * t


def ease_out_quart(t: float) -> float:
    """Quartic ease-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    t -= 1
    return 1 - t * t * t * t


def ease_in_out_quart(t: float) -> float:
    """Quartic ease-in-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    if t < 0.5:
        return 8 * t * t * t * t
    t -= 1
    return 1 - 8 * t * t * t * t


def ease_in_sine(t: float) -> float:
    """Sine ease-in function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return 1 - cos(t * pi / 2)


def ease_out_sine(t: float) -> float:
    """Sine ease-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return sin(t * pi / 2)


def ease_in_out_sine(t: float) -> float:
    """Sine ease-in-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return -(cos(pi * t) - 1) / 2


def ease_in_expo(t: float) -> float:
    """Exponential ease-in function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return 0.0 if t == 0.0 else pow(2, 10 * (t - 1))


def ease_out_expo(t: float) -> float:
    """Exponential ease-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return 1.0 if t == 1.0 else 1 - pow(2, -10 * t)


def ease_in_out_expo(t: float) -> float:
    """Exponential ease-in-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    if t < 0.5:
        return pow(2, 20 * t - 10) / 2
    return (2 - pow(2, -20 * t + 10)) / 2


def ease_in_circ(t: float) -> float:
    """Circular ease-in function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return 1 - sqrt(1 - t * t)


def ease_out_circ(t: float) -> float:
    """Circular ease-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return sqrt(1 - (t - 1) * (t - 1))


def ease_in_out_circ(t: float) -> float:
    """Circular ease-in-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    if t < 0.5:
        return (1 - sqrt(1 - 4 * t * t)) / 2
    return (sqrt(1 - (-2 * t + 2) * (-2 * t + 2)) + 1) / 2


def ease_in_back(t: float) -> float:
    """Back ease-in function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    c1 = 1.70158
    c3 = c1 + 1
    return c3 * t * t * t - c1 * t * t


def ease_out_back(t: float) -> float:
    """Back ease-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) * (t - 1) * (t - 1) + c1 * (t - 1) * (t - 1)


def ease_in_out_back(t: float) -> float:
    """Back ease-in-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    c1 = 1.70158
    c2 = c1 * 1.525
    if t < 0.5:
        return ((2 * t) ** 2 * ((c2 + 1) * 2 * t - c2)) / 2
    return ((2 * t - 2) ** 2 * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2


def ease_in_elastic(t: float) -> float:
    """Elastic ease-in function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    c4 = (2 * pi) / 3
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    return -pow(2, 10 * t - 10) * sin((t * 10 - 10.75) * c4)


def ease_out_elastic(t: float) -> float:
    """Elastic ease-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    c4 = (2 * pi) / 3
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    return pow(2, -10 * t) * sin((t * 10 - 0.75) * c4) + 1


def ease_in_out_elastic(t: float) -> float:
    """Elastic ease-in-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    c5 = (2 * pi) / 4.5
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    if t < 0.5:
        return -(pow(2, 20 * t - 10) * sin((20 * t - 11.125) * c5)) / 2
    return (pow(2, -20 * t + 10) * sin((20 * t - 11.125) * c5)) / 2 + 1


def ease_in_bounce(t: float) -> float:
    """Bounce ease-in function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    return 1 - ease_out_bounce(1 - t)


def ease_out_bounce(t: float) -> float:
    """Bounce ease-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    n1 = 7.5625
    d1 = 2.75

    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def ease_in_out_bounce(t: float) -> float:
    """Bounce ease-in-out function.

    Args:
        t: Input value between 0.0 and 1.0.

    Returns:
        Eased value.
    """
    if t < 0.5:
        return (1 - ease_out_bounce(1 - 2 * t)) / 2
    return (1 + ease_out_bounce(2 * t - 1)) / 2


# Default easing function
ease_in_out = ease_in_out_quad
