from __future__ import annotations

from song_pattern_workbench.models import EvalCaseResult
from song_pattern_workbench.search import run_search


def run_evals(config: dict[str, object]) -> dict[str, object]:
    queries = config.get("queries", [])
    if not isinstance(queries, list):
        raise ValueError("Config queries must be a list.")

    cases: list[EvalCaseResult] = []
    for query in queries:
        if not isinstance(query, dict):
            raise ValueError("Each query must be an object.")
        search_run = run_search(config, str(query["pattern"]))
        expected_titles = [str(item) for item in query.get("expected_titles", [])]
        retrieved_titles = [result.title for result in search_run.results]
        matched = [title for title in expected_titles if title in retrieved_titles]
        pass_rate = len(matched) / len(expected_titles) if expected_titles else 1.0
        cases.append(
            EvalCaseResult(
                pattern=str(query["pattern"]),
                normalized_pattern=search_run.normalized_pattern,
                expected_titles=expected_titles,
                retrieved_titles=retrieved_titles,
                matched_expected_titles=matched,
                pass_rate=pass_rate,
            )
        )

    avg_pass_rate = sum(case.pass_rate for case in cases) / len(cases) if cases else 1.0
    return {
        "cases": [case.to_dict() for case in cases],
        "summary": {
            "num_cases": len(cases),
            "avg_pass_rate": avg_pass_rate,
        },
    }

