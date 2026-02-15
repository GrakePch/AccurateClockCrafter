import copy
import json
import pathlib

from modules.AccurateHours import genAccurateHour
from modules.Utils import formatTime, interp, save_to_files


def index_textures(template_dir: pathlib.Path, pack: dict):
    textures_root = template_dir / "assets/minecraft/textures"
    if not textures_root.exists():
        print("No textures directory found.")
        return

    for texture_file in textures_root.rglob("*"):
        if texture_file.is_file() and texture_file.suffix.lower() == ".png":
            texture_rel_path = texture_file.relative_to(textures_root)
            rel_parts = texture_rel_path.parts
            if len(rel_parts) >= 3 and rel_parts[0] == "item" and rel_parts[1] == "clock":
                suffix_path = pathlib.Path(*rel_parts[2:])
                output_texture_path = (
                    pathlib.Path("item/clock") / pack["name"] / suffix_path
                )
            else:
                output_texture_path = texture_rel_path

            with open(texture_file, "rb") as f:
                pack["textures"][output_texture_path.as_posix()] = f.read()
    print("Textures indexed successfully.")


def find_by_name(elements: list[dict], name: str):
    for element in elements:
        if element.get("name") == name:
            return element
    return None


def align_angle_to_UDLR(angle: float):
    angle = angle % 360
    if 0 <= angle < 45:
        return 0, angle - 0
    elif 45 <= angle < 135:
        return 90, angle - 90
    elif 135 <= angle < 225:
        return 180, angle - 180
    elif 225 <= angle < 315:
        return 270, angle - 270
    else:  # 315 <= angle < 360
        return 0, angle - 360


def build_models(template_dir: pathlib.Path, pack: dict):
    template_models_dir = template_dir / "assets/minecraft/models/item/clock"
    output_models_partial_dir = "item/clock/" + pack["name"] + "/"
    textures_dir = template_dir / "assets/minecraft/textures/item/clock"
    has_bg_night_texture = (textures_dir / "bg_night.png").is_file()
    pack_texture_prefix = "item/clock/" + pack["name"]

    json_model_template_path_0 = (
        template_models_dir / "clock_template.json"
    )  # hands pointing up
    json_model_template_path_3 = (
        template_models_dir / "clock_template_3.json"
    )  # hands pointing right
    json_model_template_path_6 = (
        template_models_dir / "clock_template_6.json"
    )  # hands pointing down
    json_model_template_path_9 = (
        template_models_dir / "clock_template_9.json"
    )  # hands pointing left

    # parse json model templates
    with open(json_model_template_path_0, "r", encoding="utf-8") as f:
        json_model_template_0 = json.load(f)
    with open(json_model_template_path_3, "r", encoding="utf-8") as f:
        json_model_template_3 = json.load(f)
    with open(json_model_template_path_6, "r", encoding="utf-8") as f:
        json_model_template_6 = json.load(f)
    with open(json_model_template_path_9, "r", encoding="utf-8") as f:
        json_model_template_9 = json.load(f)

    # Build parent model "clock_template.json"
    parent_model = copy.deepcopy(json_model_template_0)
    for texture_key, texture_dir in parent_model["textures"].items():
        # Insert virtual pack name after "item/clock/"
        if texture_dir.startswith("item/clock/"):
            dir_after_prefix = texture_dir[len("item/clock/") :]
            # Construct new texture path
            parent_model["textures"][texture_key] = (
                pack_texture_prefix + "/" + dir_after_prefix
            )

    # Store parent model in virtual pack
    parent_model_rel_path = output_models_partial_dir + "clock_template.json"
    pack["models"][parent_model_rel_path] = parent_model

    derived_models_prototype = {
        "parent": "minecraft:" + output_models_partial_dir + "clock_template",
        "elements": copy.deepcopy(json_model_template_0["elements"]),
    }

    def update_rotation(elements: list[dict], element_name: str, raw_angle: float):
        """1.21.6~1.21.10 only support rotation angle from -45 to 45 degrees"""
        element = find_by_name(elements, element_name)
        if element is None:
            return
        base_angle, relative_angle = align_angle_to_UDLR(raw_angle)
        # angle goes counter-clockwise
        if base_angle == 0:
            # use template 0 (by default)
            pass
        elif base_angle == 270:
            # use template 3
            element_direction_right = find_by_name(
                json_model_template_3["elements"], element_name
            )
            element.update(copy.deepcopy(element_direction_right))
        elif base_angle == 180:
            # use template 6
            element_direction_down = find_by_name(
                json_model_template_6["elements"], element_name
            )
            element.update(copy.deepcopy(element_direction_down))
        elif base_angle == 90:
            # use template 9
            element_direction_left = find_by_name(
                json_model_template_9["elements"], element_name
            )
            element.update(copy.deepcopy(element_direction_left))

        element["rotation"]["axis"] = "z"
        element["rotation"]["angle"] = relative_angle

    for h in range(24):
        for m in range(60):
            model_name = f"clock_{h:02d}{m:02d}.json"
            output_model_rel_path = output_models_partial_dir + model_name

            derived_model = copy.deepcopy(derived_models_prototype)

            # Update texture during 18:00-06:00
            textures_override = None
            if 18 <= h or h < 6:
                textures_override = {
                    "hands": pack_texture_prefix + "/hands_night"
                }
                if has_bg_night_texture:
                    night_bg_path = pack_texture_prefix + "/bg_night"
                    textures_override["face"] = night_bg_path
                    textures_override["particle"] = night_bg_path
            if textures_override:
                derived_model["textures"] = textures_override

            # Calculate rotation angles
            hour_angle = -(h * 60 + m) * (360 / 12 / 60)
            minute_angle = -m * (360 / 60)

            # print(f"Building model for {h:02d}:{m:02d} -> hour_angle: {hour_angle}, minute_angle: {minute_angle}")

            # Apply rotations to the model
            update_rotation(derived_model["elements"], "hand_hour", hour_angle)
            update_rotation(derived_model["elements"], "hand_minute", minute_angle)

            # Store derived model in virtual pack
            pack["models"][output_model_rel_path] = derived_model

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

    mapHourToValue = [v * 24000 for v in genAccurateHour()]

    for h in range(0, 12):
        for m in range(0, 60):
            json_entry = copy.deepcopy(json_entry_prototype)
            json_entry["threshold"] = interp(
                mapHourToValue[h], mapHourToValue[h + 1], m / 60
            )
            json_entry["model"]["model"] = model_path_prefix + formatTime(h + 12, m)
            json_item_state["model"]["cases"][0]["model"]["entries"].append(json_entry)
            json_item_state["model"]["fallback"]["entries"].append(json_entry)

    for h in range(12, 24):
        for m in range(0, 60):
            json_entry = copy.deepcopy(json_entry_prototype)
            json_entry["threshold"] = interp(
                mapHourToValue[h], mapHourToValue[h + 1], m / 60
            )
            json_entry["model"]["model"] = model_path_prefix + formatTime(h - 12, m)
            json_item_state["model"]["cases"][0]["model"]["entries"].append(json_entry)
            json_item_state["model"]["fallback"]["entries"].append(json_entry)

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
    build_pack("Giant_Analog_Clock")
