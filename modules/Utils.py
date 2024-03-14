def inv_interp(lower, upper, value):
    return (value - lower) / (upper - lower)

def interp(lower, upper, value):
    return (1 - value) * lower + value * upper
