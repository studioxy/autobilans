from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from autobilans.models import BilansPosition


def _strip_ns(tag: str) -> str:
    return tag.split("}")[-1]


def _to_float(value: str | None) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def parse_bilans_xml(path: str | Path) -> list[BilansPosition]:
    xml_path = Path(path)
    root = ET.parse(xml_path).getroot()
    positions: list[BilansPosition] = []

    for elem in root.iter():
        tag = _strip_ns(elem.tag)
        if not (tag.startswith("Aktywa_") or tag.startswith("Pasywa_")):
            continue

        children = list(elem)
        if not children:
            continue

        child_map = {_strip_ns(child.tag): child for child in children}
        if "KwotaA" not in child_map or "KwotaB" not in child_map:
            continue

        nested_positions = [child for child in children if _strip_ns(child.tag).startswith((tag + "_",))]
        if nested_positions:
            continue

        section = "aktywa" if tag.startswith("Aktywa_") else "pasywa"
        positions.append(
            BilansPosition(
                code=tag,
                section=section,
                amount_current=_to_float(child_map["KwotaA"].text),
                amount_previous=_to_float(child_map["KwotaB"].text),
                source_path=str(xml_path),
            )
        )

    return positions
