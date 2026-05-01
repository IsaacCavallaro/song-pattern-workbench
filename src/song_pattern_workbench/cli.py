from __future__ import annotations

import argparse

from song_pattern_workbench.config import load_config
from song_pattern_workbench.evals import run_evals
from song_pattern_workbench.reporting import write_eval_report, write_search_report
from song_pattern_workbench.search import run_search


def main() -> None:
    parser = argparse.ArgumentParser(prog="song-pattern-workbench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--config", required=True)
    search_parser.add_argument("--pattern", required=True)
    search_parser.add_argument("--limit", type=int)
    search_parser.add_argument("--output-dir")

    eval_parser = subparsers.add_parser("eval")
    eval_parser.add_argument("--config", required=True)
    eval_parser.add_argument("--output-dir")

    args = parser.parse_args()
    config = load_config(args.config)

    if args.command == "search":
        run = run_search(config, args.pattern, args.limit)
        report_dir = args.output_dir or str(config["report_dir"])
        path = write_search_report(run, report_dir)
        print(path)
        return

    if args.command == "eval":
        payload = run_evals(config)
        report_dir = args.output_dir or str(config["report_dir"])
        path = write_eval_report(payload, report_dir)
        print(path)
        return

