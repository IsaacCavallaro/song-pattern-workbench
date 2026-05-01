from __future__ import annotations

import json
from pathlib import Path


def load_config(path_str: str) -> dict[str, object]:
    path = Path(path_str).resolve()
    config = json.loads(path.read_text())
    return _resolve_paths(config, path.parent)


def _resolve_paths(value: object, base_dir: Path) -> object:
    if isinstance(value, dict):
        resolved: dict[str, object] = {}
        for key, item in value.items():
            if key in {"path", "cache_dir", "report_dir"} and isinstance(item, str):
                resolved[key] = str((base_dir / item).resolve())
            else:
                resolved[key] = _resolve_paths(item, base_dir)
        return resolved
    if isinstance(value, list):
        return [_resolve_paths(item, base_dir) for item in value]
    return value

