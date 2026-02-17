from __future__ import annotations

import copy
import pathlib
from typing import Any, Callable

from accurate_clock_crafter.core.model_dispatch import (
    build_item_state,
    clock_model_name,
    create_virtual_pack,
    validate_virtual_pack,
)
from accurate_clock_crafter.core.pack_metadata import (
    RESOURCE_COMPAT_1_21_6_AND_ABOVE,
    build_pack_meta,
)
from accurate_clock_crafter.io.assets_loader import (
    load_json_template,
    load_pack_mcmeta,
    resolve_template_dir,
)
from accurate_clock_crafter.io.pack_writer import write_virtual_pack
from accurate_clock_crafter.utils.naming import pack_resource_key


def index_textures(template_dir: pathlib.Path, pack: dict[str, Any]) -> None:
    textures_root = template_dir / "assets/minecraft/textures"
    if not textures_root.exists():
        raise FileNotFoundError(f"Missing textures directory: {textures_root}")
    resource_key = pack_resource_key(pack["name"])

    for texture_file in textures_root.rglob("*"):
        if texture_file.is_file() and texture_file.suffix.lower() == ".png":
            texture_rel_path = texture_file.relative_to(textures_root)
            rel_parts = texture_rel_path.parts
            if len(rel_parts) >= 3 and rel_parts[0] == "item" and rel_parts[1] == "clock":
                suffix_path = pathlib.Path(*rel_parts[2:])
                output_texture_rel_path = pathlib.Path("item/clock") / resource_key / suffix_path
            else:
                output_texture_rel_path = texture_rel_path

            with open(texture_file, "rb") as f:
                pack["textures"][output_texture_rel_path.as_posix()] = f.read()
    print("[done] Textures indexed.")


def _find_element_by_name(elements: list[dict], name: str) -> dict | None:
    for element in elements:
        if element.get("name") == name:
            return element
    return None


def _split_base_and_relative_angle(angle: float) -> tuple[int, float]:
    angle = angle % 360
    if 0 <= angle < 45:
        return 0, angle
    if 45 <= angle < 135:
        return 90, angle - 90
    if 135 <= angle < 225:
        return 180, angle - 180
    if 225 <= angle < 315:
        return 270, angle - 270
    return 0, angle - 360


def _load_rotation_templates(template_models_dir: pathlib.Path) -> dict[int, dict]:
    template_paths = {
        0: template_models_dir / "clock_template.json",
        270: template_models_dir / "clock_template_3.json",
        180: template_models_dir / "clock_template_6.json",
        90: template_models_dir / "clock_template_9.json",
    }
    return {
        base_angle: load_json_template(template_path)
        for base_angle, template_path in template_paths.items()
    }


def _build_parent_model(base_template: dict, resource_key: str) -> dict:
    parent_model = copy.deepcopy(base_template)
    pack_texture_prefix = f"item/clock/{resource_key}"
    fallback_item_texture = f"{pack_texture_prefix}/bg"
    for texture_key, texture_path in parent_model["textures"].items():
        if texture_path.startswith("item/clock/"):
            suffix = texture_path[len("item/clock/") :]
            parent_model["textures"][texture_key] = f"{pack_texture_prefix}/{suffix}"
        elif texture_path.startswith("block/"):
            parent_model["textures"][texture_key] = fallback_item_texture
    return parent_model


def _build_textures_override_for_hour(
    hour: int, pack_texture_prefix: str, has_bg_night_texture: bool
) -> dict | None:
    if 18 <= hour or hour < 6:
        override = {"hands": f"{pack_texture_prefix}/hands_night"}
        if has_bg_night_texture:
            night_bg_path = f"{pack_texture_prefix}/bg_night"
            override["face"] = night_bg_path
            override["particle"] = night_bg_path
        return override
    return None


def _update_hand_rotation(
    elements: list[dict], element_name: str, raw_angle: float, templates_by_direction: dict[int, dict]
) -> None:
    element = _find_element_by_name(elements, element_name)
    if element is None:
        return

    base_angle, relative_angle = _split_base_and_relative_angle(raw_angle)
    if base_angle != 0:
        reference_element = _find_element_by_name(
            templates_by_direction[base_angle]["elements"], element_name
        )
        if reference_element is not None:
            element.update(copy.deepcopy(reference_element))

    element["rotation"]["axis"] = "z"
    element["rotation"]["angle"] = relative_angle


def _build_single_time_model(
    hour: int,
    minute: int,
    parent_model_path: str,
    base_template: dict,
    templates_by_direction: dict[int, dict],
    texture_override: dict | None,
) -> dict:
    model = {
        "parent": parent_model_path,
        "elements": copy.deepcopy(base_template["elements"]),
    }
    if texture_override:
        model["textures"] = texture_override

    hour_angle = -(hour * 60 + minute) * (360 / 12 / 60)
    minute_angle = -minute * (360 / 60)
    _update_hand_rotation(model["elements"], "hand_hour", hour_angle, templates_by_direction)
    _update_hand_rotation(model["elements"], "hand_minute", minute_angle, templates_by_direction)
    return model


def build_models(template_dir: pathlib.Path, pack: dict[str, Any]) -> None:
    template_models_dir = template_dir / "assets/minecraft/models/item/clock"
    textures_dir = template_dir / "assets/minecraft/textures/item/clock"
    has_bg_night_texture = (textures_dir / "bg_night.png").is_file()
    resource_key = pack_resource_key(pack["name"])
    output_models_dir = f"item/clock/{resource_key}/"
    pack_texture_prefix = f"item/clock/{resource_key}"

    templates_by_direction = _load_rotation_templates(template_models_dir)
    base_template = templates_by_direction[0]

    parent_model = _build_parent_model(base_template, resource_key)
    parent_model_rel_path = f"{output_models_dir}clock_template.json"
    parent_model_path = f"minecraft:{output_models_dir}clock_template"
    pack["models"][parent_model_rel_path] = parent_model

    for hour in range(24):
        for minute in range(60):
            texture_override = _build_textures_override_for_hour(
                hour, pack_texture_prefix, has_bg_night_texture
            )
            model_rel_path = f"{output_models_dir}clock_{hour:02d}{minute:02d}.json"
            pack["models"][model_rel_path] = _build_single_time_model(
                hour=hour,
                minute=minute,
                parent_model_path=parent_model_path,
                base_template=base_template,
                templates_by_direction=templates_by_direction,
                texture_override=texture_override,
            )

    print("[done] All model JSONs built.")


def _model_name_for_entry(pack_name: str) -> Callable[[int, int], str]:
    model_path_prefix = f"item/clock/{pack_resource_key(pack_name)}/clock_"
    return lambda hour, minute: clock_model_name(model_path_prefix, hour, minute)


def build_item_state_json(pack_name: str) -> dict:
    return build_item_state(
        model_name_for_entry=_model_name_for_entry(pack_name),
        fallback_mode="same",
    )


def build_virtual_pack(pack: dict[str, Any]) -> None:
    template_dir = resolve_template_dir(pack["name"])
    template_meta = load_pack_mcmeta(template_dir)
    description = template_meta.get("pack", {}).get("description", "")
    pack["pack_mcmeta"] = {
        "meta_type": template_meta.get("meta_type", "analog"),
        "pack": build_pack_meta(description, RESOURCE_COMPAT_1_21_6_AND_ABOVE),
    }

    index_textures(template_dir, pack)
    build_models(template_dir, pack)
    pack["items"]["clock.json"] = build_item_state_json(pack["name"])
    validate_virtual_pack(pack)
    print("[done] Item state JSON built.")


def build_analog_pack(template_name: str) -> None:
    virtual_pack = create_virtual_pack(template_name)
    build_virtual_pack(virtual_pack)
    write_virtual_pack(virtual_pack)


if __name__ == "__main__":
    build_analog_pack("Giant_Analog_Clock")
