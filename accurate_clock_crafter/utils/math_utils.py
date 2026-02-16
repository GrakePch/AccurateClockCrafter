def inv_interp(lower: float, upper: float, value: float) -> float:
    return (value - lower) / (upper - lower)


def interp(lower: float, upper: float, value: float) -> float:
    return (1 - value) * lower + value * upper
