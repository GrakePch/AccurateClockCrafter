import copy
import json
import pathlib
import random

from PIL import Image

from modules.AccurateHours import genAccurateHour
from modules.Utils import formatTime, interp, save_to_files


def index_textures(template_dir: pathlib.Path, pack: dict):

    textures_dir = template_dir / "assets/minecraft/textures/item/clock"
    for texture_file in textures_dir.rglob("*"):
        if texture_file.is_file() and texture_file.suffix.lower() == ".png":
            texture_rel_path = texture_file.relative_to(textures_dir)
            output_texture_dir = (
                pathlib.Path("item/clock/") / pack["name"] / texture_rel_path
            )
            with open(texture_file, "rb") as f:
                pack["textures"][output_texture_dir.as_posix()] = f.read()
    print("Textures indexed successfully.")
    


def build_models(template_dir: pathlib.Path, pack: dict):
    template_models_dir = template_dir / "assets/minecraft/models/item/clock"
    output_models_partial_dir = "item/clock/" + pack["name"] + "/"
    
    json_model_template_path = template_models_dir / "clock_template.json"
    
    # parse json model template
    with open(json_model_template_path, "r", encoding="utf-8") as f:
        json_model_template = json.load(f)
        
    # Build parent model "clock_template.json"
    parent_model = copy.deepcopy(json_model_template)
    texture_prefix = "item/clock/"
    for texture_key, texture_dir in parent_model["textures"].items():
        if texture_dir.startswith(texture_prefix):
            dir_after_prefix = texture_dir[len(texture_prefix):]
            parent_model["textures"][texture_key] = (
                texture_prefix + pack["name"] + "/" + dir_after_prefix
            )

    # Store parent model in virtual pack
    parent_model_rel_path = output_models_partial_dir + "clock_template.json"
    pack["models"][parent_model_rel_path] = parent_model

    derived_models_prototype = {
        "parent": "minecraft:" + output_models_partial_dir + "clock_template",
        "textures": copy.deepcopy(parent_model["textures"]),
    }
    
    # Build derived models "clock_hhmm.json"
    for h in range(0, 24):
        for m in range(0, 60):
            model_name = f"clock_{formatTime(h, m)}.json"
            derived_model = copy.deepcopy(derived_models_prototype)
            # Update texture references in the derived model
            derived_model["textures"]["hour"] = (
                "item/clock/" + pack["name"] + "/h/" + str(h)
            )
            derived_model["textures"]["min1"] = (
                "item/clock/" + pack["name"] + "/m1/" + str(m // 10)
            )
            derived_model["textures"]["min0"] = (
                "item/clock/" + pack["name"] + "/m0/" + str(m % 10)
            )
            
            # Store derived model in virtual pack
            derived_model_rel_path = output_models_partial_dir + f"clock_{formatTime(h, m)}.json"
            pack["models"][derived_model_rel_path] = derived_model
            
    print("All model JSONs built successfully.")


def build_item_state(pack: dict):
    json_item_state_prototype = {
        "model": {
            "type": "minecraft:select",
            "property": "minecraft:context_dimension",
            "cases": [
                {
                    "when": "minecraft:overworld",
                    "model": {
                        "type": "minecraft:range_dispatch",
                        "property": "minecraft:time",
                        "source": "daytime",
                        "scale": 24000.0,
                        "entries": [],
                    },
                }
            ],
            "fallback": {
                "type": "minecraft:range_dispatch",
                "property": "minecraft:time",
                "source": "random",
                "scale": 24000.0,
                "entries": [],
            },
        }
    }
    json_entry_prototype = {
        "model": {
            "type": "minecraft:model",
            "model": None,
        },
        "threshold": 0.0,
    }
    model_path_prefix = "item/clock/" + pack["name"] + "/clock_"

    json_item_state = copy.deepcopy(json_item_state_prototype)
    fallback_entries = []

    mapHourToValue = [v * 24000 for v in genAccurateHour()]

    for h in range(0, 12):
        for m in range(0, 60):
            json_entry = copy.deepcopy(json_entry_prototype)
            json_entry["threshold"] = interp(
                mapHourToValue[h], mapHourToValue[h + 1], m / 60
            )
            json_entry["model"]["model"] = model_path_prefix + formatTime(h + 12, m)
            json_item_state["model"]["cases"][0]["model"]["entries"].append(json_entry)
            fallback_entries.append(copy.deepcopy(json_entry))

    for h in range(12, 24):
        for m in range(0, 60):
            json_entry = copy.deepcopy(json_entry_prototype)
            json_entry["threshold"] = interp(
                mapHourToValue[h], mapHourToValue[h + 1], m / 60
            )
            json_entry["model"]["model"] = model_path_prefix + formatTime(h - 12, m)
            json_item_state["model"]["cases"][0]["model"]["entries"].append(json_entry)
            fallback_entries.append(copy.deepcopy(json_entry))

    shuffled_models = [entry["model"]["model"] for entry in fallback_entries]
    random.shuffle(shuffled_models)
    for entry, model_name in zip(fallback_entries, shuffled_models):
        entry["model"]["model"] = model_name
    json_item_state["model"]["fallback"]["entries"] = fallback_entries

    # Store item state in virtual pack
    pack["items"]["clock.json"] = json_item_state

    print("Item state JSON built successfully.")


def build_virtual_pack(pack: dict):
    input_template_dir = pathlib.Path("inputs_templates") / pack["name"]

    with open(input_template_dir / "pack.mcmeta", "r", encoding="utf-8") as f:
        pack["pack.mcmeta"] = json.load(f)

    index_textures(input_template_dir, pack)
    build_models(input_template_dir, pack)
    build_item_state(pack)


def build_pack(pack_name: str):
    virtual_pack = {
        "name": pack_name,
        "pack.mcmeta": {},
        "items": {},
        "models": {},
        "textures": {},
    }
    
    build_virtual_pack(virtual_pack)
    save_to_files(virtual_pack)

if __name__ == "__main__":
    build_pack("Square_Digital_Clock")
