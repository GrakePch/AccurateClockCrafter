import sys
import os
sys.path.append(os.path.dirname(__file__))
from Utils import inv_interp

# To make sure tick X000 => YY:00 not ZZ:59, offset a bit ahead. 
# Only for 6000<t<18000, t==4000, 5000
CORRECTION = 1/1440

# Start at 12:00 = 0.0 (fake)
# The sun rotation in Minecraft is NOT at a constant speed.
# Which means, if we assign the HH:00 textures EVENLY, the time will NOT show HH:00 at time (H-6)000,
# except for 12:00(6000) and 00:00(18000).
# e.g. To display 14:00, we need to "/time set 8645".
# The following time values are measured manually. They will be used to calculate the accurate time value.
# The goal is to display 14:00 when "/time set 8000".
fakeRealToTick = [
    6000,   # 12:00
    7400,
    8645,
    9781,
    10837,
    11834,
    12786,  # 18:00
    13702,
    14591,
    15460,
    16314,
    17160,
    18000,  # 00:00
    18841,
    19687,
    20541,
    21410,
    22299,
    23215,  # 06:00
    167,
    1164,
    2220,
    3356,
    4569,
    6000,   # 12:00
]


def _hour_label(index: int) -> str:
    hour = index + 12 if index < 12 else index - 12
    return f"{hour:02d}:00"


def _assert_monotonic(values: list[float], epsilon: float = 1e-9) -> None:
    for i in range(1, len(values)):
        if values[i] + epsilon < values[i - 1]:
            raise ValueError(
                "genAccurateHour produced non-monotonic data between "
                f"{_hour_label(i - 1)} and {_hour_label(i)}: "
                f"{values[i - 1]:.7f} -> {values[i]:.7f}"
            )


def genAccurateHour():
    adjusted_ticks = fakeRealToTick.copy()
    for i in range(19, 25):
        adjusted_ticks[i] += 24000

    result = [0]

    for i in range(1, 12):
        targetTick = (i+6) * 1000
        targetJsonTime = (i-1) + inv_interp(adjusted_ticks[i-1], adjusted_ticks[i], targetTick)
        targetJsonTime /= 24
        result.append(targetJsonTime)

    result.append(0.5)

    for i in range(13, 24):
        targetTick = (i+6) * 1000
        targetJsonTime = (i) + inv_interp(adjusted_ticks[i], adjusted_ticks[i+1], targetTick)
        targetJsonTime /= 24
        if targetTick >= 24000:
            targetTick -= 24000
        result.append(targetJsonTime)

    result.append(1.0)

    for i in range(1, 12):
        result[i] -= CORRECTION
    # 10:00 and 11:00 should manually deduct a little time to make sure X000 shows YY:00 instead of ZZ:59
    result[22] -= CORRECTION / 4
    result[23] -= CORRECTION / 4

    _assert_monotonic(result)
    
    return result

if __name__ == "__main__":
    result = genAccurateHour()
    
    for i in range(0, 25):
        targetTick = (i+6) * 1000
        if targetTick >= 24000:
            targetTick -= 24000
        displayTime = i + 12 if i < 12 else i - 12
        print("{:5d}".format(targetTick), "{:0.7f}".format(result[i]), "{:02d}".format(displayTime) + ":00")
