import unittest
from pathlib import Path

from song_pattern_workbench.assistant import run_ask
from song_pattern_workbench.config import load_config


class AssistantTests(unittest.TestCase):
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

    def test_run_ask_uses_grounded_fixture_answer(self) -> None:
        run = run_ask(
            self.config,
            pattern="ii-V-I",
            question="What should I practice first?",
        )
        self.assertEqual(run.provider_name, "fixture")
        self.assertIn("Autumn Leaves", run.answer)
        self.assertEqual(run.search_run.normalized_pattern, "II-V-I")
        self.assertEqual(len(run.search_run.results), 10)


if __name__ == "__main__":
    unittest.main()
