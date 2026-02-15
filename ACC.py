from __future__ import annotations

import copy
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import ACC_analog
import ACC_digital


BASE_INPUT_DIR = Path("inputs_templates")
BASE_OUTPUT_DIR = Path("outputs")
ACCURATE_PACK_NAME = "AccurateClocks"


def _build_vanilla_clock_entries() -> list[dict]:
    entries: list[dict] = []
    for idx in range(64):
        threshold = 0.0 if idx == 0 else idx - 0.5
        entries.append(
            {
                "model": {
                    "type": "minecraft:model",
                    "model": f"minecraft:item/clock_{idx:02d}",
                },
                "threshold": threshold,
            }
        )
    entries.append(
        {
            "model": {
                "type": "minecraft:model",
                "model": "minecraft:item/clock_00",
            },
            "threshold": 63.5,
        }
    )
    return entries


def _build_vanilla_clock_range_dispatch(source: str) -> dict:
    return {
        "type": "minecraft:range_dispatch",
        "property": "minecraft:time",
        "source": source,
        "scale": 64.0,
        "entries": _build_vanilla_clock_entries(),
    }


# Matches the vanilla 1.21.4 clock item definition for unknown names.
DEFAULT_CLOCK_MODEL_PAYLOAD = {
    "type": "minecraft:select",
    "property": "minecraft:context_dimension",
    "cases": [
        {
            "when": "minecraft:overworld",
            "model": _build_vanilla_clock_range_dispatch("daytime"),
        }
    ],
    "fallback": _build_vanilla_clock_range_dispatch("random"),
}

META_TYPE_TO_BUILDER: dict[str, Callable[[str], None]] = {
    "analog": ACC_analog.build_pack,
    "digital": ACC_digital.build_pack,
}


@dataclass(slots=True)
class TemplatePack:
    name: str
    template_dir: Path
    meta_type: str
    pack_meta: dict

    @property
    def display_name(self) -> str:
        return self.name.replace("_", " ")

    @property
    def output_dir(self) -> Path:
        return BASE_OUTPUT_DIR / self.name


def discover_templates() -> list[TemplatePack]:
    templates: list[TemplatePack] = []
    if not BASE_INPUT_DIR.exists():
        raise FileNotFoundError(f"Missing {BASE_INPUT_DIR}")

    for entry in sorted(BASE_INPUT_DIR.iterdir()):
        if not entry.is_dir():
            continue
        pack_mcmeta = entry / "pack.mcmeta"
        if not pack_mcmeta.exists():
            print(f"[skip] {entry.name}: pack.mcmeta not found")
            continue
        with open(pack_mcmeta, "r", encoding="utf-8") as f:
            meta = json.load(f)

        meta_type = meta.get("meta_type")
        if not meta_type:
            print(f"[skip] {entry.name}: meta_type missing in pack.mcmeta")
            continue

        templates.append(
            TemplatePack(
                name=entry.name,
                template_dir=entry,
                meta_type=meta_type.lower(),
                pack_meta=meta.get("pack", {}),
            )
        )

    return templates


def build_templates(templates: list[TemplatePack]) -> list[TemplatePack]:
    successful: list[TemplatePack] = []
    for template in templates:
        builder = META_TYPE_TO_BUILDER.get(template.meta_type)
        if builder is None:
            print(
                f"[skip] {template.name}: no builder registered for meta_type='{template.meta_type}'"
            )
            continue

        print(f"[build] {template.name} ({template.meta_type})")
        try:
            builder(template.name)
        except Exception as exc:  # pragma: no cover - guardrail
            print(f"[error] {template.name}: {exc}")
            continue

        successful.append(template)

    return successful


@dataclass(slots=True)
class VariantCase:
    template: TemplatePack
    model_payload: dict


def load_variant_cases(templates: list[TemplatePack]) -> list[VariantCase]:
    cases: list[VariantCase] = []
    for template in templates:
        clock_path = template.output_dir / "assets/minecraft/items/clock.json"
        if not clock_path.exists():
            print(f"[warn] {template.name}: missing clock.json, skipping from aggregate")
            continue
        with open(clock_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        model_payload = data.get("model")
        if model_payload is None:
            print(f"[warn] {template.name}: clock.json missing 'model', skipping")
            continue

        cases.append(VariantCase(template=template, model_payload=copy.deepcopy(model_payload)))

    return cases


def write_pack_mcmeta(destination: Path, cases: list[VariantCase]) -> None:
    pack_formats = [
        case.template.pack_meta.get("pack_format") for case in cases if case.template.pack_meta
    ]
    pack_format = max(pack_formats) if pack_formats else 15
    description_lines = ["§7Accurate §6Clocks§r", "§8Rename clocks to select variants§r"]
    pack_data = {
        "pack": {
            "pack_format": pack_format,
            "description": "\n".join(description_lines),
        },
        "meta_type": "composite",
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "w", encoding="utf-8") as f:
        json.dump(pack_data, f, ensure_ascii=False, indent=4)


def build_combined_clock_json(cases: list[VariantCase]) -> dict:
    if not cases:
        raise ValueError("No variant cases available to build combined clock.json")

    fallback_model = copy.deepcopy(DEFAULT_CLOCK_MODEL_PAYLOAD)
    select_cases = [
        {
            "when": case.template.display_name,
            "model": copy.deepcopy(case.model_payload),
        }
        for case in cases
    ]
    return {
        "model": {
            "type": "minecraft:select",
            "property": "minecraft:component",
            "component": "minecraft:custom_name",
            "cases": select_cases,
            "fallback": fallback_model,
        }
    }


def write_combined_clock(destination: Path, cases: list[VariantCase]) -> None:
    combined = build_combined_clock_json(cases)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=4)


def merge_variant_assets(destination_assets: Path, templates: list[TemplatePack]) -> None:
    for template in templates:
        src_assets = template.output_dir / "assets"
        if not src_assets.exists():
            print(f"[warn] {template.name}: assets folder missing, skipping asset merge")
            continue

        for file in src_assets.rglob("*"):
            if not file.is_file():
                continue
            rel_path = file.relative_to(src_assets)
            if rel_path.as_posix() == "minecraft/items/clock.json":
                continue

            dest_file = destination_assets / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            if dest_file.exists():
                print(f"[overwrite] {rel_path.as_posix()} <- {template.name}")
            shutil.copy2(file, dest_file)


def assemble_accurate_clocks(templates: list[TemplatePack]) -> None:
    target_dir = BASE_OUTPUT_DIR / ACCURATE_PACK_NAME
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    cases = load_variant_cases(templates)
    if not cases:
        print("[warn] No variants available for AccurateClocks; nothing to assemble.")
        return

    write_pack_mcmeta(target_dir / "pack.mcmeta", cases)
    merge_variant_assets(target_dir / "assets", [case.template for case in cases])
    write_combined_clock(target_dir / "assets/minecraft/items/clock.json", cases)
    print(f"[done] AccurateClocks generated with {len(cases)} variants.")


def main() -> None:
    templates = discover_templates()
    if not templates:
        print("[warn] No templates found in inputs_templates.")
        return

    built_templates = build_templates(templates)
    if not built_templates:
        print("[warn] No templates built successfully.")
        return

    assemble_accurate_clocks(built_templates)


if __name__ == "__main__":
    main()
