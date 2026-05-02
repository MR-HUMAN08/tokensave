from __future__ import annotations

from typing import Dict


def to_toon(data: Dict[str, str]) -> str:
    lines = []
    for key, value in data.items():
        value_str = str(value)
        value_str = value_str.replace("\"", "")
        value_str = value_str.replace("{", "").replace("}", "")
        value_str = value_str.replace("[", "").replace("]", "")
        value_str = value_str.replace("_", "__")
        value_str = value_str.replace(" ", "_")
        lines.append(f"{key}: {value_str}")
    return "\n".join(lines)


def from_toon(toon_str: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for line in toon_str.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value_str = value.strip()
        value_str = value_str.replace("__", "\u0000")
        value_str = value_str.replace("_", " ")
        value_str = value_str.replace("\u0000", "_")
        result[key.strip()] = value_str
    return result


def count_tokens(text: str) -> int:
    return len(text.split())
