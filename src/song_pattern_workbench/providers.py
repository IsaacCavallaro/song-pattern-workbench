from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from song_pattern_workbench.models import SearchHit


class FixturePatternClient:
    def __init__(self, path: str) -> None:
        self.payload = json.loads(Path(path).read_text())

    def search_progression(self, normalized_pattern: str, limit: int) -> list[SearchHit]:
        matches = self.payload.get(normalized_pattern, [])[:limit]
        return [SearchHit(**item) for item in matches]


class ApiPatternClient:
    def __init__(self, endpoint_template: str, token_env: str | None = None) -> None:
        self.endpoint_template = endpoint_template
        self.token_env = token_env

    def search_progression(self, normalized_pattern: str, limit: int) -> list[SearchHit]:
        url = self.endpoint_template.format(
            pattern=urllib.parse.quote(normalized_pattern),
            limit=limit,
        )
        payload = _load_json(url, self.token_env)
        results = payload.get("results", [])
        return [SearchHit(**item) for item in results[:limit]]


class FixtureMetadataClient:
    def __init__(self, path: str) -> None:
        self.payload = json.loads(Path(path).read_text())

    def enrich(self, hit: SearchHit) -> SearchHit:
        hit.metadata = dict(self.payload.get(hit.song_id, {}))
        return hit


class ApiMetadataClient:
    def __init__(self, endpoint_template: str, token_env: str | None = None) -> None:
        self.endpoint_template = endpoint_template
        self.token_env = token_env

    def enrich(self, hit: SearchHit) -> SearchHit:
        url = self.endpoint_template.format(
            artist=urllib.parse.quote(hit.artist),
            title=urllib.parse.quote(hit.title),
            song_id=urllib.parse.quote(hit.song_id),
        )
        hit.metadata = _load_json(url, self.token_env)
        return hit


class MusicBrainzLookupClient:
    def enrich(self, hit: SearchHit) -> SearchHit:
        query = urllib.parse.quote(f'recording:"{hit.title}" AND artist:"{hit.artist}"')
        url = (
            "https://musicbrainz.org/ws/2/recording/"
            f"?query={query}&fmt=json&limit=1"
        )
        payload = _load_json(url, token_env=None)
        recordings = payload.get("recordings", [])
        if not recordings:
            hit.metadata = {}
            return hit
        recording = recordings[0]
        artist_credit = recording.get("artist-credit", [])
        hit.metadata = {
            "musicbrainz_recording_id": recording.get("id"),
            "musicbrainz_title": recording.get("title"),
            "artist_credit": [
                item.get("name") for item in artist_credit if isinstance(item, dict)
            ],
            "first_release_date": recording.get("first-release-date"),
            "score": recording.get("score"),
        }
        return hit


def build_pattern_client(config: dict[str, object]) -> FixturePatternClient | ApiPatternClient:
    provider_type = config["type"]
    if provider_type == "fixture":
        return FixturePatternClient(path=str(config["path"]))
    if provider_type == "api":
        return ApiPatternClient(
            endpoint_template=str(config["endpoint_template"]),
            token_env=str(config["token_env"]) if "token_env" in config else None,
        )
    raise ValueError(f"Unsupported hook provider type: {provider_type}")


def build_metadata_client(
    config: dict[str, object],
) -> FixtureMetadataClient | ApiMetadataClient | MusicBrainzLookupClient:
    provider_type = config["type"]
    if provider_type == "fixture":
        return FixtureMetadataClient(path=str(config["path"]))
    if provider_type == "api":
        return ApiMetadataClient(
            endpoint_template=str(config["endpoint_template"]),
            token_env=str(config["token_env"]) if "token_env" in config else None,
        )
    if provider_type == "musicbrainz_lookup":
        return MusicBrainzLookupClient()
    raise ValueError(f"Unsupported metadata provider type: {provider_type}")


def _load_json(url: str, token_env: str | None) -> dict[str, object]:
    headers = {"User-Agent": "song-pattern-workbench/0.1.0"}
    if token_env:
        token = os.environ.get(token_env)
        if not token:
            raise ValueError(f"Missing required token env var: {token_env}")
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))
