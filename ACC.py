import sys
from PIL import Image
import pathlib
import json
import copy
import os
import shutil

# To make sure tick X000 => YY:00 not ZZ:59, offset a bit ahead. 
# Only for 6000<t<18000, t==4000, 5000
CORRECTION = 1/1440

CONFIG = {
    "mode": "d",                # d: Digital; a: Analog
    "is_hour_higher": False,    # True: hour layer is higher than minute layer
    "pack_icon_time": [9, 30],  # [HH, MM]: Use the texture of HHMM as pack.png
}
    
pack = {
    "pack": {
        "pack_format": 15,
        "description": "§7Accurate §6Clock§r\nmade w/ AccurateClockCrafter"
    }
}

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


def inv_interp(lower, upper, value):
    return (value - lower) / (upper - lower)

def interp(lower, upper, value):
    return (1 - value) * lower + value * upper

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
    
result = genAccurateHour()

# print result for debugging
if 0:
    for i in range(0, 25):
        targetTick = (i+6) * 1000
        if targetTick >= 24000:
            targetTick -= 24000
        displayTime = i + 12 if i < 12 else i - 12
        print("{:5d}".format(targetTick), "{:0.7f}".format(result[i]), "{:02d}".format(displayTime) + ":00")



# Get pack folder name under "inputs/"
dir_list = next(os.walk("./inputs"))[1]
pack_dir = dir_list[0]


# Read pack.mcmeta from "inputs/"
try:
    f_pack_json = open("./inputs/{}/pack.mcmeta".format(pack_dir), encoding='utf-8')
    pack_json = json.load(f_pack_json)
    for k, v in pack_json.items():
        if k == "pack":
            for k2, v2 in v.items():
                pack[k][k2] = v2
        elif k == "acc_config":
            for k2, v2 in v.items():
                CONFIG[k2] = v2
        else:
            pack[k] = v
    print("Input's pack.mcmeta found. Config applied:")
except:
    print("Input's pack.mcmeta not found / not correctly formatted. Default values used:")
print("  mode:           {}".format(CONFIG["mode"]))
print("  is_hour_higher: {}".format(CONFIG["is_hour_higher"]))
print("  pack_icon_time: {}".format(CONFIG["pack_icon_time"]))


# Read arguments 
# argc = len(sys.argv)
# if (argc > 2):
#     if (sys.argv[1] == "a"):
#         CONFIG["mode"] = "a" # Analog Clock
#     arg2 = int(sys.argv[2])

try:
    shutil.rmtree('./outputs/')
except:
    pass
# Create directories
pathlib.Path('./outputs/{}/assets/minecraft/textures/item/'.format(pack_dir)).mkdir(parents=True, exist_ok=True)
pathlib.Path('./outputs/{}/assets/minecraft/models/item/'.format(pack_dir)).mkdir(parents=True, exist_ok=True)

t_bg = Image.open("./inputs/{}/bg.png".format(pack_dir))

def formatTime(h, m):
    return "{:02d}{:02d}".format(h, m)

def getMinuteFromPNG(name):
    if not name.endswith(".png"): return -1
    try:
        m = int(name[0:-4])
        if 0 <= m < 60:
            return int(name[0:-4])
        else:
            return -1
    except:
        return -1

print("===Crafting Clock Start===")

list_m = []
if CONFIG["mode"] == "d":

    print("Generating Textures... ", end='')
    c = 0
    t_minuteDigit1 = []
    t_minuteDigit2 = []
    for m1 in range(0, 6):
        t_minuteDigit1.append(Image.open("./inputs/{}/m1/{}.png".format(pack_dir, m1)))
    for m2 in range(0, 10):
        t_minuteDigit2.append(Image.open("./inputs/{}/m2/{}.png".format(pack_dir, m2)))

    list_m = list(range(0, 60))
    for h in range(0, 24):
        t_result_hour_only = t_bg.copy()
        t_hour = Image.open("./inputs/{}/h/{}.png".format(pack_dir, h))
        t_result_hour_only.paste(t_hour, (0, 0), mask=t_hour)
        for m in range(0, 60):
            t_result = t_result_hour_only.copy()
            m1 = m // 10
            m2 = m % 10
            t_result.paste(t_minuteDigit1[m1], (0, 0), mask=t_minuteDigit1[m1])
            t_result.paste(t_minuteDigit2[m2], (0, 0), mask=t_minuteDigit2[m2])
            t_result.save("./outputs/{}/assets/minecraft/textures/item/clock_{}.png".format(pack_dir, formatTime(h, m)))
            # Generate pack.png
            if h == CONFIG["pack_icon_time"][0] and m == CONFIG["pack_icon_time"][1]:
                t_result.save("./outputs/{}/pack.png".format(pack_dir))
            c += 1
elif CONFIG["mode"] == "a":
    
    list_dir_in_m = os.listdir("./inputs/{}/m/".format(pack_dir))
    list_m_m_png = [(getMinuteFromPNG(name), name) for name in list_dir_in_m if getMinuteFromPNG(name) >= 0]
    dict_m_png = dict(list_m_m_png)
    list_m = sorted(dict_m_png.keys())
    
    if not (0 <= CONFIG["pack_icon_time"][0] < 24):
        CONFIG["pack_icon_time"][0] = 9
        print("WARNING: invalid 1st value of pack_icon_time. 9 is used.")
        print("  HINT: valid value should be integer in range [0, 23] (inclusively).")
    if CONFIG["pack_icon_time"][1] not in list_m:
        CONFIG["pack_icon_time"][1] = list_m[len(list_m) // 2]
        print("WARNING: invalid 2nd value of pack_icon_time. {} is used.".format(CONFIG["pack_icon_time"][1]))
        print("  HINT: valid value should be the name of one of the PNG file under \"m/\".")
    
    print("Generating Textures... ", end='')
    c = 0
    list_h_texture = [Image.open("./inputs/{}/h/{}.png".format(pack_dir, h)) 
                        for h in range(0, 24)]
    dict_m_texture = dict()
    for m, m_png in dict_m_png.items():
        dict_m_texture[m] = Image.open("./inputs/{}/m/{}".format(pack_dir, m_png))
        
    for h in range(0, 24):
        t_result_hour_only = t_bg.copy()
        if CONFIG["is_hour_higher"] == False:
            t_result_hour_only.paste(list_h_texture[h], (0, 0), mask=list_h_texture[h])
        for m in list_m:
            t_result = t_result_hour_only.copy()
            t_result.paste(dict_m_texture[m], (0, 0), mask=dict_m_texture[m])
            if CONFIG["is_hour_higher"] == True:
                t_result.paste(list_h_texture[h], (0, 0), mask=list_h_texture[h])
            t_result.save("./outputs/{}/assets/minecraft/textures/item/clock_{}.png".format(pack_dir, formatTime(h, m)))
            # Generate pack.png
            if h == CONFIG["pack_icon_time"][0] and m == CONFIG["pack_icon_time"][1]:
                t_result.save("./outputs/{}/pack.png".format(pack_dir))
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
    for m in list_m:
        if h == 0 and m == 0: continue
        j_result = copy.deepcopy(j_template)
        j_result["textures"]["layer0"] += formatTime(h, m)
        with open("./outputs/{}/assets/minecraft/models/item/clock_{}.json".format(pack_dir, formatTime(h, m)), "w") as outFile:
            json.dump(j_result, outFile, indent=4) 

# Generate clock.json
j_case_template = { "predicate": { "time": 0.0 }, "model": "item/clock_" }
j_0000 = copy.deepcopy(j_template)
j_0000["textures"]["layer0"] += "0000"
j_0000["overrides"] = []
for i in range(0, 12):
    for m in list_m:
        j_case = copy.deepcopy(j_case_template)
        j_case["predicate"]["time"] = interp(result[i], result[i+1], m/60)
        j_case["model"] += formatTime(i+12, m)
        j_0000["overrides"].append(j_case)

for i in range(12, 24):
    for m in list_m:
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


with open("./outputs/{}/assets/minecraft/models/item/clock.json".format(pack_dir), "w") as outFile:
    json.dump(j_0000, outFile, indent=2) 

with open("./outputs/{}/pack.mcmeta".format(pack_dir), "w") as packMcmeta:
    json.dump(pack, packMcmeta, indent=2)

print("Done.")
print("===Crafting Clock Succeeded===")
print("The result is in \"outputs/\"")