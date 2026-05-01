import unittest
from pathlib import Path

from song_pattern_workbench.config import load_config
from song_pattern_workbench.evals import run_evals


class EvalTests(unittest.TestCase):
    def test_eval_summary(self) -> None:
        config = load_config("examples/configs/basic.json")
        cache_dir = Path(config["cache_dir"])
        if cache_dir.exists():
            for path in cache_dir.rglob("*"):
                if path.is_file():
                    path.unlink()
            for path in sorted(cache_dir.rglob("*"), reverse=True):
                if path.is_dir():
                    path.rmdir()
        payload = run_evals(config)
        self.assertEqual(payload["summary"]["num_cases"], 2)
        self.assertGreaterEqual(payload["summary"]["avg_pass_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
