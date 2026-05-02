from __future__ import annotations

import json
from pathlib import Path

from song_pattern_workbench.models import AskRun, SearchRun


def write_search_report(run: SearchRun, report_dir: str) -> Path:
    path = Path(report_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "results.json").write_text(json.dumps(run.to_dict(), indent=2, sort_keys=True))
    (path / "summary.md").write_text(_search_summary(run))
    return path


def write_eval_report(payload: dict[str, object], report_dir: str) -> Path:
    path = Path(report_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "eval_results.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    (path / "eval_summary.md").write_text(_eval_summary(payload))
    return path


def write_ask_report(run: AskRun, report_dir: str) -> Path:
    path = Path(report_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "ask_results.json").write_text(json.dumps(run.to_dict(), indent=2, sort_keys=True))
    (path / "ask_summary.md").write_text(_ask_summary(run))
    return path


def _search_summary(run: SearchRun) -> str:
    lines = [
        f"# Search Report",
        "",
        f"- Query: `{run.pattern}`",
        f"- Normalized: `{run.normalized_pattern}`",
        f"- Cache hit: `{str(run.cache_hit).lower()}`",
        f"- Cache namespace: `{run.cache_namespace}`",
        f"- Offset: `{run.offset}`",
        f"- Limit: `{run.limit}`",
        f"- Returned: `{len(run.results)}`",
        f"- Total available: `{run.total_available}`",
        "",
        "## Matches",
        "",
    ]
    for result in run.results:
        lines.append(
            f"- **{result.title}** by {result.artist}"
            + (f" ({result.section})" if result.section else "")
        )
    return "\n".join(lines) + "\n"


def _eval_summary(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    cases = payload["cases"]
    lines = [
        "# Eval Summary",
        "",
        f"- Cases: `{summary['num_cases']}`",
        f"- Average pass rate: `{summary['avg_pass_rate']:.2f}`",
        "",
        "## Cases",
        "",
    ]
    for case in cases:
        lines.append(
            f"- `{case['pattern']}` matched {len(case['matched_expected_titles'])}/"
            f"{len(case['expected_titles'])} expected titles"
        )
    return "\n".join(lines) + "\n"


def _ask_summary(run: AskRun) -> str:
    lines = [
        "# Ask Summary",
        "",
        f"- Question: `{run.question}`",
        f"- Provider: `{run.provider_name}`",
        f"- Pattern: `{run.search_run.pattern}`",
        f"- Returned matches: `{len(run.search_run.results)}`",
        f"- Total available: `{run.search_run.total_available}`",
        "",
        "## Answer",
        "",
        run.answer,
        "",
        "## Grounded Matches",
        "",
    ]
    for result in run.search_run.results:
        lines.append(f"- **{result.title}** by {result.artist}")
    return "\n".join(lines) + "\n"
