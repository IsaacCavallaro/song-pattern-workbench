from __future__ import annotations

import hashlib
import json
from pathlib import Path


class JsonCache:
    def __init__(self, cache_dir: Path | str) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, namespace: str, key: str) -> dict[str, object] | None:
        path = self._path(namespace, key)
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def set(self, namespace: str, key: str, value: dict[str, object]) -> None:
        path = self._path(namespace, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True))

    def _path(self, namespace: str, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / namespace / f"{digest}.json"
