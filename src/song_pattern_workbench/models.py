from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class SearchHit:
    song_id: str
    title: str
    artist: str
    section: str | None = None
    matched_progression: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class SearchRun:
    pattern: str
    normalized_pattern: str
    results: list[SearchHit]
    cache_hit: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "pattern": self.pattern,
            "normalized_pattern": self.normalized_pattern,
            "cache_hit": self.cache_hit,
            "results": [item.to_dict() for item in self.results],
        }


@dataclass
class EvalCaseResult:
    pattern: str
    normalized_pattern: str
    expected_titles: list[str]
    retrieved_titles: list[str]
    matched_expected_titles: list[str]
    pass_rate: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

