from __future__ import annotations

import copy
import random
from typing import Callable, Literal, TypedDict

from accurate_clock_crafter.core.time_curve import generate_accurate_hour_markers
from accurate_clock_crafter.utils.math_utils import interp
from accurate_clock_crafter.utils.naming import format_time

HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
HALF_DAY_HOURS = 12
TICKS_PER_DAY = 24000.0


class RangeModel(TypedDict):
    type: str
    model: str


class RangeEntry(TypedDict):
    model: RangeModel
    threshold: float


class VirtualPack(TypedDict):
    name: str
    pack_mcmeta: dict
    items: dict[str, dict]
    models: dict[str, dict]
    textures: dict[str, bytes]


def create_virtual_pack(pack_name: str) -> VirtualPack:
    return {
        "name": pack_name,
        "pack_mcmeta": {},
        "items": {},
        "models": {},
        "textures": {},
    }


def create_range_entry(model_name: str, threshold: float) -> RangeEntry:
    return {
        "model": {
            "type": "minecraft:model",
            "model": model_name,
        },
        "threshold": threshold,
    }


def _build_item_state_skeleton() -> dict:
    return {
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
                        "scale": TICKS_PER_DAY,
                        "entries": [],
                    },
                }
            ],
            "fallback": {
                "type": "minecraft:range_dispatch",
                "property": "minecraft:time",
                "source": "random",
                "scale": TICKS_PER_DAY,
                "entries": [],
            },
        }
    }


def _build_time_entries(model_name_for_entry: Callable[[int, int], str]) -> list[RangeEntry]:
    accurate_hours = [hour_ratio * TICKS_PER_DAY for hour_ratio in generate_accurate_hour_markers()]
    entries: list[RangeEntry] = []

    for hour in range(0, HALF_DAY_HOURS):
        for minute in range(0, MINUTES_PER_HOUR):
            threshold = interp(
                accurate_hours[hour], accurate_hours[hour + 1], minute / MINUTES_PER_HOUR
            )
            display_hour = hour + HALF_DAY_HOURS
            model_name = model_name_for_entry(display_hour, minute)
            entries.append(create_range_entry(model_name, threshold))

    for hour in range(HALF_DAY_HOURS, HOURS_PER_DAY):
        for minute in range(0, MINUTES_PER_HOUR):
            threshold = interp(
                accurate_hours[hour], accurate_hours[hour + 1], minute / MINUTES_PER_HOUR
            )
            display_hour = hour - HALF_DAY_HOURS
            model_name = model_name_for_entry(display_hour, minute)
            entries.append(create_range_entry(model_name, threshold))

    return entries


def _shuffle_fallback_models(entries: list[RangeEntry]) -> None:
    model_names = [entry["model"]["model"] for entry in entries]
    random.shuffle(model_names)
    for entry, model_name in zip(entries, model_names):
        entry["model"]["model"] = model_name


def build_item_state(
    model_name_for_entry: Callable[[int, int], str],
    fallback_mode: Literal["same", "shuffle"] = "same",
) -> dict:
    item_state = _build_item_state_skeleton()
    daytime_entries = _build_time_entries(model_name_for_entry)
    fallback_entries = copy.deepcopy(daytime_entries)

    if fallback_mode == "shuffle":
        _shuffle_fallback_models(fallback_entries)

    item_state["model"]["cases"][0]["model"]["entries"] = daytime_entries
    item_state["model"]["fallback"]["entries"] = fallback_entries
    return item_state


def clock_model_name(model_path_prefix: str, hour: int, minute: int) -> str:
    return f"{model_path_prefix}{format_time(hour, minute)}"


def validate_virtual_pack(pack: VirtualPack) -> None:
    for rel_path in pack["textures"].keys():
        if rel_path.lower() != rel_path:
            raise ValueError(f"Texture path must be lowercase: {rel_path}")

    for model_path, payload in pack["models"].items():
        textures = payload.get("textures", {}) if isinstance(payload, dict) else {}
        for texture_ref in textures.values():
            if isinstance(texture_ref, str) and texture_ref.startswith("block/"):
                raise ValueError(
                    f"Item model {model_path} uses block atlas texture reference: {texture_ref}"
                )
