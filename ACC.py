import sys
from PIL import Image
import pathlib
import json
import copy

MODE = "d" # Digital Clock
SCALE_IN_1_HOUR = 1
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

for i in range(19, 25):
    fakeRealToTick[i] += 24000

def inv_interp(lower, upper, value):
    return (value - lower) / (upper - lower)

def interp(lower, upper, value):
    return (1 - value) * lower + value * upper

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
    
# print
if 0:
    for i in range(0, 25):
        targetTick = (i+6) * 1000
        if targetTick >= 24000:
            targetTick -= 24000
        displayTime = i + 12 if i < 12 else i - 12
        print("{:5d}".format(targetTick), "{:0.7f}".format(result[i]), "{:02d}".format(displayTime) + ":00")
    
# Read arguments to get user set scale of one hour
argc = len(sys.argv)
if (argc > 2):
    if (sys.argv[1] == "a"):
        MODE = "a" # Analog Clock
    arg2 = int(sys.argv[2])
    SCALE_IN_1_HOUR = arg2 if arg2 > 1 else SCALE_IN_1_HOUR


# Create directories
pathlib.Path('./outputs/assets/minecraft/textures/item/').mkdir(parents=True, exist_ok=True)
pathlib.Path('./outputs/assets/minecraft/models/item/').mkdir(parents=True, exist_ok=True)

t_bg = Image.open(r"./inputs/bg.png")

def formatTime(h, m):
    return "{:02d}{:02d}".format(h, m)

if MODE == "d":
    print("===Crafting Digital Clock Start===")

    print("Generating Textures... ", end='')
    c = 0
    t_minuteDigit1 = []
    t_minuteDigit2 = []
    for m1 in range(0, 6):
        t_minuteDigit1.append(Image.open(r"./inputs/m1/" + str(m1) + r".png"))
    for m2 in range(0, 10):
        t_minuteDigit2.append(Image.open(r"./inputs/m2/" + str(m2) + r".png"))

    for h in range(0, 24):
        t_result_hour_only = t_bg.copy()
        t_hour = Image.open(r"./inputs/h/" + str(h) + r".png")
        t_result_hour_only.paste(t_hour, (0, 0), mask=t_hour)
        for m in range(0, 60):
            t_result = t_result_hour_only.copy()
            m1 = m // 10
            m2 = m % 10
            t_result.paste(t_minuteDigit1[m1], (0, 0), mask=t_minuteDigit1[m1])
            t_result.paste(t_minuteDigit2[m2], (0, 0), mask=t_minuteDigit2[m2])
            t_result.save(r"./outputs/assets/minecraft/textures/item/clock_" + formatTime(h, m) + r".png")
            if h == 20 and m == 24:
                t_result.save(r"./outputs/pack.png")
            c += 1

print("Done.", c, "texture files created.")
print("Generating Model Jsons... ", end='')

# Generate clock_HHMM.json
j_template = {
  "parent": "minecraft:item/generated",
  "textures": {
    "layer0": "minecraft:item/clock_"
  }
}
for h in range(0, 24):
    for m in range(0, 60):
        if h == 0 and m == 0: continue
        j_result = copy.deepcopy(j_template)
        j_result["textures"]["layer0"] += formatTime(h, m)
        with open("./outputs/assets/minecraft/models/item/clock_" + formatTime(h, m) + ".json", "w") as outFile:
            json.dump(j_result, outFile, indent=4) 

# Generate clock.json
j_case_template = { "predicate": { "time": 0.0 }, "model": "item/clock_" }
j_0000 = copy.deepcopy(j_template)
j_0000["textures"]["layer0"] += "0000"
j_0000["overrides"] = []
for i in range(0, 12):
    for m in range(0, 60):
        j_case = copy.deepcopy(j_case_template)
        j_case["predicate"]["time"] = interp(result[i], result[i+1], m/60)
        j_case["model"] += formatTime(i+12, m)
        j_0000["overrides"].append(j_case)

for i in range(12, 24):
    for m in range(0, 60):
        j_case = copy.deepcopy(j_case_template)
        j_case["predicate"]["time"] = interp(result[i], result[i+1], m/60)
        if i == 12 and m == 0:
            j_case["model"] = "item/clock"
        else:
            j_case["model"] += formatTime(i-12, m)
        j_0000["overrides"].append(j_case)

j_case = copy.deepcopy(j_case_template)
j_case["predicate"]["time"] = result[24]
j_case["model"] = "item/clock_1200"
j_0000["overrides"].append(j_case)


with open("./outputs/assets/minecraft/models/item/clock.json", "w") as outFile:
    json.dump(j_0000, outFile, indent=2) 

with open("./outputs/pack.mcmeta", "w") as packMcmeta:
    pack = {
        "pack": {
            "pack_format": 15,
            "description": "§7Accurate §6Clock§r\nmade w/ AccurateClockCrafter"
        }
    }
    json.dump(pack, packMcmeta, indent=2)

print("Done.")
print("===Crafting Digital Clock Succeeded===")
print("The result is in \"outputs/\"")