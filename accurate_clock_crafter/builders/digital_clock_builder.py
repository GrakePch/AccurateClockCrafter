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
from accurate_clock_crafter.utils.naming import format_time, pack_resource_key


def index_textures(template_dir: pathlib.Path, pack: dict[str, Any]) -> None:
    textures_dir = template_dir / "assets/minecraft/textures/item/clock"
    if not textures_dir.exists():
        raise FileNotFoundError(f"Missing textures directory: {textures_dir}")
    resource_key = pack_resource_key(pack["name"])

    for texture_file in textures_dir.rglob("*"):
        if texture_file.is_file() and texture_file.suffix.lower() == ".png":
            texture_rel_path = texture_file.relative_to(textures_dir)
            output_texture_rel_path = pathlib.Path("item/clock") / resource_key / texture_rel_path
            with open(texture_file, "rb") as f:
                pack["textures"][output_texture_rel_path.as_posix()] = f.read()
    print("[done] Textures indexed.")


def _load_digital_template(template_models_dir: pathlib.Path) -> dict:
    return load_json_template(template_models_dir / "clock_template.json")


def _build_digital_parent_model(json_model_template: dict, resource_key: str) -> dict:
    parent_model = copy.deepcopy(json_model_template)
    texture_prefix = "item/clock/"
    fallback_item_texture = f"{texture_prefix}{resource_key}/bg"
    for texture_key, texture_path in parent_model["textures"].items():
        if texture_path.startswith(texture_prefix):
            suffix = texture_path[len(texture_prefix) :]
            parent_model["textures"][texture_key] = f"{texture_prefix}{resource_key}/{suffix}"
        elif texture_path.startswith("block/"):
            parent_model["textures"][texture_key] = fallback_item_texture
    return parent_model


def _build_digital_time_model(parent_path: str, resource_key: str, hour: int, minute: int) -> dict:
    return {
        "parent": parent_path,
        "textures": {
            "hour": f"item/clock/{resource_key}/h/{hour}",
            "min1": f"item/clock/{resource_key}/m1/{minute // 10}",
            "min0": f"item/clock/{resource_key}/m0/{minute % 10}",
        },
    }


def build_models(template_dir: pathlib.Path, pack: dict[str, Any]) -> None:
    template_models_dir = template_dir / "assets/minecraft/models/item/clock"
    resource_key = pack_resource_key(pack["name"])
    output_models_dir = f"item/clock/{resource_key}/"

    json_model_template = _load_digital_template(template_models_dir)
    parent_model = _build_digital_parent_model(json_model_template, resource_key)

    parent_model_rel_path = f"{output_models_dir}clock_template.json"
    parent_model_path = f"minecraft:{output_models_dir}clock_template"
    pack["models"][parent_model_rel_path] = parent_model

    for hour in range(24):
        for minute in range(60):
            model_rel_path = f"{output_models_dir}clock_{format_time(hour, minute)}.json"
            pack["models"][model_rel_path] = _build_digital_time_model(
                parent_model_path, resource_key, hour, minute
            )

    print("[done] All model JSONs built.")


def _model_name_for_entry(pack_name: str) -> Callable[[int, int], str]:
    model_path_prefix = f"item/clock/{pack_resource_key(pack_name)}/clock_"
    return lambda hour, minute: clock_model_name(model_path_prefix, hour, minute)


def build_item_state_json(pack_name: str) -> dict:
    return build_item_state(
        model_name_for_entry=_model_name_for_entry(pack_name),
        fallback_mode="shuffle",
    )


def build_virtual_pack(pack: dict[str, Any]) -> None:
    template_dir = resolve_template_dir(pack["name"])
    template_meta = load_pack_mcmeta(template_dir)
    description = template_meta.get("pack", {}).get("description", "")
    pack["pack_mcmeta"] = {
        "meta_type": template_meta.get("meta_type", "digital"),
        "pack": build_pack_meta(description, RESOURCE_COMPAT_1_21_6_AND_ABOVE),
    }

    index_textures(template_dir, pack)
    build_models(template_dir, pack)
    pack["items"]["clock.json"] = build_item_state_json(pack["name"])
    validate_virtual_pack(pack)
    print("[done] Item state JSON built.")


def build_digital_pack(template_name: str) -> None:
    virtual_pack = create_virtual_pack(template_name)
    build_virtual_pack(virtual_pack)
    write_virtual_pack(virtual_pack)


if __name__ == "__main__":
    build_digital_pack("Square_Digital_Clock")
