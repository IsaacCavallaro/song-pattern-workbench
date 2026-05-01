import unittest

from song_pattern_workbench.normalize import normalize_pattern


class NormalizePatternTests(unittest.TestCase):
    def test_normalizes_common_progression(self) -> None:
        self.assertEqual(normalize_pattern("ii-V-I"), "II-V-I")

    def test_normalizes_with_spaces(self) -> None:
        self.assertEqual(normalize_pattern("i vi ii v"), "I-VI-II-V")

    def test_preserves_accidentals(self) -> None:
        self.assertEqual(normalize_pattern("bVII IV I"), "bVII-IV-I")

    def test_rejects_empty_pattern(self) -> None:
        with self.assertRaises(ValueError):
            normalize_pattern("---")


if __name__ == "__main__":
    unittest.main()

