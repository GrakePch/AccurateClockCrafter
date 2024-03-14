import sys
import os
sys.path.append(os.path.dirname(__file__))
from Utils import inv_interp

# To make sure tick X000 => YY:00 not ZZ:59, offset a bit ahead. 
# Only for 6000<t<18000, t==4000, 5000
CORRECTION = 1/1440

# Start at 12:00 = 0.0 (fake)
fakeRealToTick = [
    6000,
    7400,
    8645,
    9781,
    10837,
    11834,
    12786,
    13702,
    14591,
    15460,
    16314,
    17160,
    18000,
    18841,
    19687,
    20541,
    21410,
    22299,
    23215,
    167,
    1164,
    2220,
    3356,
    4569,
    6000
]

def genAccurateHour():
    for i in range(19, 25):
        fakeRealToTick[i] += 24000

    result = [0]

    for i in range(1, 12):
        targetTick = (i+6) * 1000
        targetJsonTime = (i-1) + inv_interp(fakeRealToTick[i-1], fakeRealToTick[i], targetTick)
        targetJsonTime /= 24
        result.append(targetJsonTime)

    result.append(0.5)

    for i in range(13, 24):
        targetTick = (i+6) * 1000
        thisInterval = fakeRealToTick[i+1] - fakeRealToTick[i]
        targetJsonTime = (i) + inv_interp(fakeRealToTick[i], fakeRealToTick[i+1], targetTick)
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
    
    return result

if __name__ == "__main__":
    result = genAccurateHour()
    
    for i in range(0, 25):
        targetTick = (i+6) * 1000
        if targetTick >= 24000:
            targetTick -= 24000
        displayTime = i + 12 if i < 12 else i - 12
        print("{:5d}".format(targetTick), "{:0.7f}".format(result[i]), "{:02d}".format(displayTime) + ":00")
