from __future__ import annotations

import json
from pathlib import Path
import shutil

from accurate_clock_crafter.core.model_dispatch import VirtualPack


def _write_json_files(base_dir: Path, entries: dict[str, dict]) -> None:
    for rel_path, payload in entries.items():
        output_path = base_dir / rel_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)


def _write_binary_files(base_dir: Path, entries: dict[str, bytes]) -> None:
    for rel_path, payload in entries.items():
        output_path = base_dir / rel_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(payload)


def write_virtual_pack(virtual_pack: VirtualPack, output_root: str = "outputs") -> None:
    output_pack_dir = Path(output_root) / virtual_pack["name"]
    if output_pack_dir.exists():
        shutil.rmtree(output_pack_dir)
    output_pack_dir.mkdir(parents=True, exist_ok=True)

    with open(output_pack_dir / "pack.mcmeta", "w", encoding="utf-8") as f:
        json.dump(virtual_pack["pack_mcmeta"], f, ensure_ascii=False, indent=4)

    _write_json_files(output_pack_dir / "assets/minecraft/items", virtual_pack["items"])
    _write_json_files(output_pack_dir / "assets/minecraft/models", virtual_pack["models"])
    _write_binary_files(output_pack_dir / "assets/minecraft/textures", virtual_pack["textures"])

    print(f"Resource pack saved to {output_pack_dir.resolve()}")
