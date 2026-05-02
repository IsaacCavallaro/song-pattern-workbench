import unittest
from copy import deepcopy
from pathlib import Path
import json
import tempfile

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

    def test_search_supports_offset_for_large_result_sets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_path = Path(temp_dir) / "large_matches.json"
            metadata_path = Path(temp_dir) / "large_metadata.json"
            all_matches = []
            all_metadata = {}
            for index in range(2500):
                song_id = f"song-{index}"
                title = f"Tune {index}"
                artist = f"Artist {index % 25}"
                all_matches.append(
                    {
                        "song_id": song_id,
                        "title": title,
                        "artist": artist,
                        "section": "A section",
                        "matched_progression": "ii-V-I",
                    }
                )
                all_metadata[song_id] = {
                    "work_title": title,
                    "artist_credit": artist,
                    "year": 1950 + (index % 50),
                }
            fixture_path.write_text(json.dumps({"II-V-I": all_matches}))
            metadata_path.write_text(json.dumps(all_metadata))

            config = deepcopy(self.config)
            config["providers"]["hooktheory"]["path"] = str(fixture_path)
            config["providers"]["musicbrainz"]["path"] = str(metadata_path)

            run = run_search(config, "ii-V-I", limit=1000, offset=1000)
            self.assertEqual(len(run.results), 1000)
            self.assertEqual(run.total_available, 2500)
            self.assertEqual(run.offset, 1000)
            self.assertEqual(run.limit, 1000)
            self.assertEqual(run.results[0].title, "Tune 1000")
            self.assertEqual(run.results[-1].title, "Tune 1999")


if __name__ == "__main__":
    unittest.main()
