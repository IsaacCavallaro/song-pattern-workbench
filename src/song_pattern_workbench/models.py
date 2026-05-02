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
class SearchPage:
    results: list[SearchHit]
    total_available: int
    offset: int
    limit: int


@dataclass
class SearchRun:
    pattern: str
    normalized_pattern: str
    results: list[SearchHit]
    cache_hit: bool
    cache_namespace: str
    offset: int
    limit: int
    total_available: int

    def to_dict(self) -> dict[str, object]:
        return {
            "pattern": self.pattern,
            "normalized_pattern": self.normalized_pattern,
            "cache_hit": self.cache_hit,
            "cache_namespace": self.cache_namespace,
            "offset": self.offset,
            "limit": self.limit,
            "total_available": self.total_available,
            "results": [item.to_dict() for item in self.results],
        }


@dataclass
class AskRun:
    question: str
    search_run: SearchRun
    answer: str
    provider_name: str
    raw: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "question": self.question,
            "provider_name": self.provider_name,
            "search_run": self.search_run.to_dict(),
            "answer": self.answer,
            "raw": self.raw,
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
