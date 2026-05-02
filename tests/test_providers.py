import unittest

from song_pattern_workbench.models import SearchHit
from song_pattern_workbench.providers import (
    _hooktheory_child_path,
    _is_reasonable_musicbrainz_match,
    provider_signature,
)


class ProviderTests(unittest.TestCase):
    def test_provider_signature_distinguishes_configs(self) -> None:
        left = provider_signature({"type": "fixture", "path": "/tmp/a.json"})
        right = provider_signature(
            {"type": "api", "endpoint_template": "https://example.com", "token_env": "TOKEN"}
        )
        self.assertNotEqual(left, right)

    def test_musicbrainz_match_requires_exact_title_and_artist(self) -> None:
        hit = SearchHit(song_id="1", title="Autumn Leaves", artist="Joseph Kosma")
        good = {
            "title": "Autumn Leaves",
            "score": 100,
            "artist-credit": [{"name": "Joseph Kosma"}],
        }
        bad_title = {
            "title": "Autumn Leaves Live",
            "score": 100,
            "artist-credit": [{"name": "Joseph Kosma"}],
        }
        bad_artist = {
            "title": "Autumn Leaves",
            "score": 100,
            "artist-credit": [{"name": "Someone Else"}],
        }
        bad_score = {
            "title": "Autumn Leaves",
            "score": 75,
            "artist-credit": [{"name": "Joseph Kosma"}],
        }
        self.assertTrue(_is_reasonable_musicbrainz_match(hit, good))
        self.assertFalse(_is_reasonable_musicbrainz_match(hit, bad_title))
        self.assertFalse(_is_reasonable_musicbrainz_match(hit, bad_artist))
        self.assertFalse(_is_reasonable_musicbrainz_match(hit, bad_score))

    def test_hooktheory_child_path_mapping(self) -> None:
        self.assertEqual(_hooktheory_child_path("II-V-I"), "2,5,1")
        self.assertEqual(_hooktheory_child_path("I-VI-II-V"), "1,6,2,5")


if __name__ == "__main__":
    unittest.main()
