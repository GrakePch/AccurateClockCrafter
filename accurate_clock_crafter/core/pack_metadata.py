from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResourceCompatibility:
    min_major: int
    min_minor: int
    max_major: int
    max_minor: int
    fallback_pack_format: int


RESOURCE_COMPAT_1_21_6_AND_ABOVE = ResourceCompatibility(
    min_major=63,
    min_minor=0,
    max_major=999,
    max_minor=0,
    fallback_pack_format=63,
)


def build_pack_meta(description: str | dict, compatibility: ResourceCompatibility) -> dict:
    return {
        "description": description,
        "pack_format": compatibility.fallback_pack_format,
        "supported_formats": [compatibility.min_major, compatibility.max_major],
        "min_format": [compatibility.min_major, compatibility.min_minor],
        "max_format": [compatibility.max_major, compatibility.max_minor],
    }
