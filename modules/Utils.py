from PIL import Image
import json
import pathlib
import shutil

def inv_interp(lower, upper, value):
    return (value - lower) / (upper - lower)

def interp(lower, upper, value):
    return (1 - value) * lower + value * upper

def mask_subtract(i1, i2):
    alpha1 = list(i1.split()[-1].getdata())
    alpha2 = list(i2.split()[-1].getdata())
    
    result_alpha = []
    for p1, p2 in zip(alpha1, alpha2):
        p_new = max(p1 - p2, 0)
        result_alpha.append(p_new)
        
    result_mask = Image.new("L", i1.size)
    result_mask.putdata(result_alpha)
    return result_mask

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
    
def save_to_files(virtual_pack):
    output_pack_dir = pathlib.Path("outputs") / virtual_pack["name"]

    # Clear existing pack directory if it exists
    if output_pack_dir.exists():
        shutil.rmtree(output_pack_dir)

    output_pack_dir.mkdir(parents=True, exist_ok=True)

    # Save pack.mcmeta
    with open(output_pack_dir / "pack.mcmeta", "w", encoding="utf-8") as f:
        json.dump(virtual_pack["pack.mcmeta"], f, indent=4)

    # Save item states
    output_items_dir = output_pack_dir / "assets/minecraft/items"
    for item_rel_path, item_data in virtual_pack["items"].items():
        item_path = output_items_dir / item_rel_path
        item_path.parent.mkdir(parents=True, exist_ok=True)
        with open(item_path, "w", encoding="utf-8") as f:
            json.dump(item_data, f, indent=4)

    # Save models
    output_models_dir = output_pack_dir / "assets/minecraft/models"
    for model_rel_path, model_data in virtual_pack["models"].items():
        model_path = output_models_dir / model_rel_path
        model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(model_path, "w", encoding="utf-8") as f:
            json.dump(model_data, f, indent=4)

    # Save textures
    output_textures_dir = output_pack_dir / "assets/minecraft/textures"
    for texture_rel_path, texture_data in virtual_pack["textures"].items():
        texture_path = output_textures_dir / texture_rel_path
        texture_path.parent.mkdir(parents=True, exist_ok=True)
        with open(texture_path, "wb") as f:
            f.write(texture_data)

    print(f"Resource pack saved to {output_pack_dir.resolve()}")