from __future__ import annotations

from song_pattern_workbench.cache import JsonCache
from song_pattern_workbench.models import SearchHit, SearchRun
from song_pattern_workbench.normalize import normalize_pattern
from song_pattern_workbench.providers import build_metadata_client, build_pattern_client


def run_search(config: dict[str, object], pattern: str, limit: int | None = None) -> SearchRun:
    providers = _providers(config)
    normalized_pattern = normalize_pattern(pattern)
    limit_value = limit if limit is not None else int(config.get("default_limit", 10))
    cache = JsonCache(_cache_dir(config))
    cache_key = f"{normalized_pattern}:{limit_value}"
    cached = cache.get("search", cache_key)
    if cached is not None:
        results = [SearchHit(**item) for item in cached["results"]]
        return SearchRun(
            pattern=pattern,
            normalized_pattern=normalized_pattern,
            results=results,
            cache_hit=True,
        )

    pattern_client = build_pattern_client(providers["hooktheory"])
    metadata_client = build_metadata_client(providers["musicbrainz"])
    results = [metadata_client.enrich(hit) for hit in pattern_client.search_progression(normalized_pattern, limit_value)]
    run = SearchRun(
        pattern=pattern,
        normalized_pattern=normalized_pattern,
        results=results,
        cache_hit=False,
    )
    cache.set("search", cache_key, {"results": [item.to_dict() for item in results]})
    return run


def _providers(config: dict[str, object]) -> dict[str, dict[str, object]]:
    providers = config.get("providers")
    if not isinstance(providers, dict):
        raise ValueError("Config must contain a providers object.")
    return providers  # type: ignore[return-value]


def _cache_dir(config: dict[str, object]) -> str:
    cache_dir = config.get("cache_dir")
    if not isinstance(cache_dir, str):
        raise ValueError("Config must contain a cache_dir path.")
    return cache_dir

