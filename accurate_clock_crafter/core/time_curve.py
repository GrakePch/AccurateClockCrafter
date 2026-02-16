from __future__ import annotations

import math

TICKS_PER_DAY = 24000.0


def _hour_label(index: int) -> str:
    hour = index + 12 if index < 12 else index - 12
    return f"{hour:02d}:00"


def _assert_monotonic(values: list[float], epsilon: float = 1e-9) -> None:
    for i in range(1, len(values)):
        if values[i] + epsilon < values[i - 1]:
            raise ValueError(
                "generate_accurate_hour_markers produced non-monotonic data between "
                f"{_hour_label(i - 1)} and {_hour_label(i)}: "
                f"{values[i - 1]:.7f} -> {values[i]:.7f}"
            )


def _clock_angle_from_tick(tick: float) -> float:
    x = ((tick % TICKS_PER_DAY) / TICKS_PER_DAY) - 0.25
    x = (x + 1.0) % 1.0
    theta = 1.0 - (math.cos(math.pi * x) + 1.0) / 2.0
    return x + (theta - x) / 3.0


def _unwrap_cycle(values: list[float]) -> list[float]:
    unwrapped = [values[0]]
    for value in values[1:]:
        if value < unwrapped[-1]:
            value += 1.0
        unwrapped.append(value)
    return unwrapped


def _normalize(values: list[float]) -> list[float]:
    start = values[0]
    end = values[-1]
    if end <= start:
        raise ValueError("Cannot normalize marker values: end must be greater than start.")
    return [(value - start) / (end - start) for value in values]


def generate_accurate_hour_markers() -> list[float]:
    raw_values = [_clock_angle_from_tick((hour + 6) * 1000) for hour in range(25)]
    unwrapped_values = _unwrap_cycle(raw_values)
    result = _normalize(unwrapped_values)
    result[0] = 0.0
    result[-1] = 1.0
    _assert_monotonic(result)
    return result
