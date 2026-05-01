import unittest
from copy import deepcopy
from pathlib import Path

from song_pattern_workbench.config import load_config
from song_pattern_workbench.search import run_search


class SearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config("examples/configs/basic.json")
        cls.cache_dir = Path(cls.config["cache_dir"])

    def setUp(self) -> None:
        if self.cache_dir.exists():
            for path in self.cache_dir.rglob("*"):
                if path.is_file():
                    path.unlink()
            for path in sorted(self.cache_dir.rglob("*"), reverse=True):
                if path.is_dir():
                    path.rmdir()

    def test_search_returns_fixture_results(self) -> None:
        run = run_search(self.config, "ii-V-I")
        titles = [result.title for result in run.results]
        self.assertEqual(titles[:2], ["Autumn Leaves", "Blue Bossa"])
        self.assertFalse(run.cache_hit)

    def test_search_uses_cache_on_repeat(self) -> None:
        run_search(self.config, "ii-V-I")
        cached = run_search(self.config, "ii-V-I")
        self.assertTrue(cached.cache_hit)

    def test_cache_isolated_by_provider_configuration(self) -> None:
        run_search(self.config, "ii-V-I")
        alt_config = deepcopy(self.config)
        alt_config["providers"]["musicbrainz"] = {
            "type": "fixture",
            "path": str(
                Path(self.config["providers"]["musicbrainz"]["path"]).with_name(
                    "hooktheory_matches.json"
                )
            ),
        }
        fresh = run_search(alt_config, "ii-V-I")
        self.assertFalse(fresh.cache_hit)
        self.assertNotEqual(
            run_search(self.config, "ii-V-I").cache_namespace,
            fresh.cache_namespace,
        )


if __name__ == "__main__":
    unittest.main()
