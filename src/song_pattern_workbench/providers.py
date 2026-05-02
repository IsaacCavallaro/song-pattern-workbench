from __future__ import annotations

import json
import os
import socket
import time
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

from song_pattern_workbench.models import SearchHit, SearchPage


DEFAULT_TIMEOUT_SECONDS = 10
HOOKTHEORY_PAGE_SIZE = 20
DEFAULT_HOOKTHEORY_BASE_URL = "https://api.hooktheory.com/v1"
HOOKTHEORY_CHORD_IDS = {
    "I": "1",
    "II": "2",
    "III": "3",
    "IV": "4",
    "V": "5",
    "VI": "6",
    "VII": "7",
    "bVII": "12",
}


class FixturePatternClient:
    def __init__(self, path: str) -> None:
        self.payload = json.loads(Path(path).read_text())

    def search_progression(self, normalized_pattern: str, limit: int, offset: int = 0) -> SearchPage:
        all_matches = self.payload.get(normalized_pattern, [])
        matches = all_matches[offset : offset + limit]
        return SearchPage(
            results=[SearchHit(**item) for item in matches],
            total_available=len(all_matches),
            offset=offset,
            limit=limit,
        )


class ApiPatternClient:
    def __init__(self, endpoint_template: str, token_env: str | None = None) -> None:
        self.endpoint_template = endpoint_template
        self.token_env = token_env

    def search_progression(self, normalized_pattern: str, limit: int, offset: int = 0) -> SearchPage:
        url = self.endpoint_template.format(
            pattern=urllib.parse.quote(normalized_pattern),
            limit=limit,
            offset=offset,
        )
        payload = _load_json(url, self.token_env)
        results = payload.get("results", [])
        total_available = int(payload.get("total_available", len(results)))
        return SearchPage(
            results=[SearchHit(**item) for item in results[:limit]],
            total_available=total_available,
            offset=offset,
            limit=limit,
        )


class HooktheoryPatternClient:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_HOOKTHEORY_BASE_URL,
        activkey_env: str | None = None,
        username_env: str | None = None,
        password_env: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.activkey_env = activkey_env
        self.username_env = username_env
        self.password_env = password_env
        self._activkey: str | None = None

    def search_progression(self, normalized_pattern: str, limit: int, offset: int = 0) -> SearchPage:
        cp = _hooktheory_child_path(normalized_pattern)
        results: list[SearchHit] = []
        page = (offset // HOOKTHEORY_PAGE_SIZE) + 1
        start_index = offset % HOOKTHEORY_PAGE_SIZE
        total_seen = (page - 1) * HOOKTHEORY_PAGE_SIZE

        while len(results) < limit:
            payload, headers = self._songs_page(cp=cp, page=page)
            if not isinstance(payload, list) or not payload:
                break
            total_seen += len(payload)
            page_hits = [_hooktheory_song_to_hit(item, cp) for item in payload]
            if start_index:
                page_hits = page_hits[start_index:]
                start_index = 0
            remaining = limit - len(results)
            results.extend(page_hits[:remaining])
            _maybe_wait_for_hooktheory_rate_limit(headers)
            if len(payload) < HOOKTHEORY_PAGE_SIZE:
                break
            page += 1

        return SearchPage(
            results=results,
            total_available=max(total_seen, offset + len(results)),
            offset=offset,
            limit=limit,
        )

    def _songs_page(self, *, cp: str, page: int) -> tuple[object, dict[str, str]]:
        token = self._resolve_activkey()
        query = urllib.parse.urlencode({"cp": cp, "page": page})
        url = f"{self.base_url}/trends/songs?{query}"
        return _load_json(url, token_env=None, bearer_token=token, include_headers=True)

    def _resolve_activkey(self) -> str:
        if self._activkey:
            return self._activkey
        if self.activkey_env:
            activkey = os.environ.get(self.activkey_env)
            if activkey:
                self._activkey = activkey
                return activkey
        if not self.username_env or not self.password_env:
            raise ValueError(
                "hooktheory_api requires either activkey_env or username_env/password_env"
            )
        username = os.environ.get(self.username_env)
        password = os.environ.get(self.password_env)
        if not username or not password:
            raise ValueError(
                f"Missing Hooktheory credentials in {self.username_env} / {self.password_env}"
            )
        url = f"{self.base_url}/users/auth"
        response = _post_json(url, {"username": username, "password": password})
        activkey = response.get("activkey")
        if not isinstance(activkey, str) or not activkey:
            raise RuntimeError("Hooktheory auth response did not contain an activkey")
        self._activkey = activkey
        return activkey


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
        if not _is_reasonable_musicbrainz_match(hit, recording):
            hit.metadata = {}
            return hit
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


def build_pattern_client(
    config: dict[str, object],
) -> FixturePatternClient | ApiPatternClient | HooktheoryPatternClient:
    provider_type = config["type"]
    if provider_type == "fixture":
        return FixturePatternClient(path=str(config["path"]))
    if provider_type == "api":
        return ApiPatternClient(
            endpoint_template=str(config["endpoint_template"]),
            token_env=str(config["token_env"]) if "token_env" in config else None,
        )
    if provider_type == "hooktheory_api":
        return HooktheoryPatternClient(
            base_url=str(config.get("base_url", DEFAULT_HOOKTHEORY_BASE_URL)),
            activkey_env=str(config["activkey_env"]) if "activkey_env" in config else None,
            username_env=str(config["username_env"]) if "username_env" in config else None,
            password_env=str(config["password_env"]) if "password_env" in config else None,
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


def _load_json(
    url: str,
    token_env: str | None,
    *,
    bearer_token: str | None = None,
    include_headers: bool = False,
) -> dict[str, object] | tuple[object, dict[str, str]]:
    headers = {"User-Agent": "song-pattern-workbench/0.1.0"}
    if token_env:
        token = os.environ.get(token_env)
        if not token:
            raise ValueError(f"Missing required token env var: {token_env}")
        headers["Authorization"] = f"Bearer {token}"
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
            if include_headers:
                return payload, dict(response.headers.items())
            return payload
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        raise RuntimeError(f"Request failed for {url}: {exc}") from exc


def _post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "User-Agent": "song-pattern-workbench/0.1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        raise RuntimeError(f"Request failed for {url}: {exc}") from exc


def provider_signature(config: dict[str, object]) -> str:
    provider_type = str(config.get("type", "unknown"))
    parts = [provider_type]
    if "path" in config:
        parts.append(f"path={config['path']}")
    if "endpoint_template" in config:
        parts.append(f"endpoint={config['endpoint_template']}")
    if "token_env" in config:
        parts.append(f"token_env={config['token_env']}")
    if "base_url" in config:
        parts.append(f"base_url={config['base_url']}")
    if "activkey_env" in config:
        parts.append(f"activkey_env={config['activkey_env']}")
    if "username_env" in config:
        parts.append(f"username_env={config['username_env']}")
    if "password_env" in config:
        parts.append(f"password_env={config['password_env']}")
    return "|".join(parts)


def _is_reasonable_musicbrainz_match(hit: SearchHit, recording: dict[str, object]) -> bool:
    title = str(recording.get("title", "")).strip().casefold()
    if title != hit.title.strip().casefold():
        return False

    score = recording.get("score")
    if isinstance(score, int) and score < 90:
        return False

    artist_credit = recording.get("artist-credit", [])
    names = [
        str(item.get("name", "")).strip().casefold()
        for item in artist_credit
        if isinstance(item, dict)
    ]
    expected_artist = hit.artist.strip().casefold()
    return expected_artist in names


def _hooktheory_child_path(normalized_pattern: str) -> str:
    tokens = normalized_pattern.split("-")
    chord_ids: list[str] = []
    for token in tokens:
        chord_id = HOOKTHEORY_CHORD_IDS.get(token)
        if chord_id is None:
            raise ValueError(
                f"Unsupported Hooktheory chord token {token!r}. "
                "Supported tokens are I, II, III, IV, V, VI, VII, and bVII."
            )
        chord_ids.append(chord_id)
    return ",".join(chord_ids)


def _hooktheory_song_to_hit(item: object, cp: str) -> SearchHit:
    if not isinstance(item, dict):
        raise ValueError("Hooktheory song payload entries must be objects")
    artist = item.get("artist")
    title = item.get("song")
    section = item.get("section")
    url = item.get("url")
    if not isinstance(artist, str) or not isinstance(title, str):
        raise ValueError("Hooktheory song entries require string artist and song fields")
    song_id = _slugify(f"{artist}-{title}")
    metadata: dict[str, object] = {}
    if isinstance(url, str):
        metadata["source_url"] = url
    return SearchHit(
        song_id=song_id,
        title=title,
        artist=artist,
        section=section if isinstance(section, str) else None,
        matched_progression=cp,
        metadata=metadata,
    )


def _maybe_wait_for_hooktheory_rate_limit(headers: dict[str, str]) -> None:
    remaining = headers.get("X-Rate-Limit-Remaining")
    reset = headers.get("X-Rate-Limit-Reset")
    try:
        if remaining is not None and int(remaining) <= 0 and reset is not None:
            wait_seconds = max(float(reset), 0.0)
            if wait_seconds > 0:
                time.sleep(wait_seconds)
    except ValueError:
        return


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    return "".join(character if character.isalnum() else "-" for character in lowered).strip("-")
