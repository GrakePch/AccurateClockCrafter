from accurate_clock_crafter.builders.analog_clock_builder import build_analog_pack
from accurate_clock_crafter.builders.digital_clock_builder import build_digital_pack


def build_composite_pack() -> None:
    from accurate_clock_crafter.main import build_composite_pack as _build_composite_pack

    _build_composite_pack()


def run() -> None:
    from accurate_clock_crafter.main import run as _run

    _run()

__all__ = [
    "build_analog_pack",
    "build_digital_pack",
    "build_composite_pack",
    "run",
]
