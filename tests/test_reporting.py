import unittest

from song_pattern_workbench.models import SearchHit, SearchRun
from song_pattern_workbench.reporting import _search_summary


class ReportingTests(unittest.TestCase):
    def test_search_summary_contains_matches(self) -> None:
        run = SearchRun(
            pattern="ii-V-I",
            normalized_pattern="II-V-I",
            cache_hit=False,
            cache_namespace="search::fixture",
            offset=0,
            limit=100,
            total_available=2500,
            results=[
                SearchHit(
                    song_id="autumn-leaves",
                    title="Autumn Leaves",
                    artist="Joseph Kosma",
                    section="A section",
                )
            ],
        )
        summary = _search_summary(run)
        self.assertIn("Autumn Leaves", summary)
        self.assertIn("II-V-I", summary)
        self.assertIn("search::fixture", summary)
        self.assertIn("2500", summary)


if __name__ == "__main__":
    unittest.main()
