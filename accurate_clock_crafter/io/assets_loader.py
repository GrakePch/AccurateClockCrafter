from __future__ import annotations

import json
from pathlib import Path

INPUT_TEMPLATES_DIR = Path("inputs_templates")


def resolve_template_dir(pack_name: str) -> Path:
    template_dir = INPUT_TEMPLATES_DIR / pack_name
    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory not found: {template_dir}")
    return template_dir


def load_pack_mcmeta(template_dir: Path) -> dict:
    pack_mcmeta_path = template_dir / "pack.mcmeta"
    if not pack_mcmeta_path.exists():
        raise FileNotFoundError(f"Missing template file: {pack_mcmeta_path}")
    with open(pack_mcmeta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_json_template(json_path: Path) -> dict:
    if not json_path.exists():
        raise FileNotFoundError(f"Missing template file: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)
