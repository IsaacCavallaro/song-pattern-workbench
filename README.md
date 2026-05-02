# song-pattern-workbench

`song-pattern-workbench` is a CLI-first retrieval and evaluation workbench for finding recurring harmonic patterns across songs.

It is built around a simple idea:

```text
query like "ii-V-I"
        |
        v
normalize harmonic pattern
        |
        v
retrieve matching songs from a pattern source
        |
        v
enrich matches with catalog metadata
        |
        v
optionally ask an LLM grounded on those matches
        |
        v
cache results for repeatable runs and write reports
```

The repo is intentionally scoped to harmonic search first. It supports offline fixtures for deterministic testing and a config-driven API mode for real providers.

## Scope

| Capability | Included |
| --- | --- |
| Roman numeral pattern normalization | Yes |
| CLI search workflow | Yes |
| Config-driven provider wiring | Yes |
| Hooktheory-style pattern source interface | Yes |
| MusicBrainz-style enrichment interface | Yes |
| Local JSON cache | Yes |
| Grounded LLM question flow | Yes |
| Fixture-backed offline mode | Yes |
| Retrieval evals | Yes |
| Markdown and JSON reports | Yes |

## Quick Start

```bash
git clone <your-repo-url>
cd song-pattern-workbench
uv venv --seed .venv
source .venv/bin/activate
uv pip install -e .
song-pattern-workbench search \
  --config examples/configs/basic.json \
  --pattern "ii-V-I"
```

Reports are written to `reports/` by default.

Run the built-in retrieval evals:

```bash
song-pattern-workbench eval --config examples/configs/basic.json
```

For API-backed usage, export the variables from `.env.example` and use `examples/configs/api.json` as a starting point.

To ask a grounded question over retrieved songs:

```bash
song-pattern-workbench ask \
  --config examples/configs/basic.json \
  --pattern "ii-V-I" \
  --question "What should I practice first if I want to hear this cadence in many standards?"
```

## Config

The runner uses JSON config files. Paths are resolved relative to the config file location.

Example:

```json
{
  "cache_dir": "../../.cache/song-pattern-workbench",
  "report_dir": "../../reports/basic",
  "default_limit": 10,
  "providers": {
    "hooktheory": {
      "type": "fixture",
      "path": "../fixtures/hooktheory_matches.json"
    },
    "musicbrainz": {
      "type": "fixture",
      "path": "../fixtures/musicbrainz_metadata.json"
    }
  },
  "assistant": {
    "type": "fixture",
    "path": "../fixtures/assistant_answers.json"
  },
  "queries": [
    {
      "pattern": "ii-V-I",
      "expected_titles": ["Autumn Leaves", "Blue Bossa"]
    }
  ]
}
```

## Provider Modes

### `fixture`

Best for tests, demos, and deterministic evaluation.

### `api`

Real API mode is config-driven. The current implementation supports:

- a concrete `hooktheory_api` mode for progression search
- generic pattern-source endpoints through `endpoint_template`
- generic metadata endpoints through `endpoint_template`
- a concrete `musicbrainz_lookup` mode for title and artist enrichment
- an `openai_compatible` grounded assistant mode

That keeps the repo honest:

- fixture mode works out of the box
- API mode is ready for real credentials
- provider details can be adapted without changing the search pipeline

Example API config:

```json
{
  "providers": {
    "hooktheory": {
      "type": "hooktheory_api",
      "base_url": "https://api.hooktheory.com/v1",
      "username_env": "HOOKTHEORY_USERNAME",
      "password_env": "HOOKTHEORY_PASSWORD"
    },
    "musicbrainz": {
      "type": "musicbrainz_lookup"
    }
  },
  "assistant": {
    "type": "openai_compatible",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4.1-mini",
    "api_key_env": "OPENAI_API_KEY",
    "system_prompt": "Answer using only the retrieved matches and metadata."
  }
}
```

See `examples/configs/api.json` for a concrete starting point.

The Hooktheory integration translates normalized Roman numeral patterns into Hooktheory `cp` values and paginates through `trends/songs` in 20-song pages.

## Example Queries

```bash
song-pattern-workbench search --config examples/configs/basic.json --pattern "ii-V-I"
song-pattern-workbench ask --config examples/configs/basic.json --pattern "ii-V-I" --question "Which songs should I start with?"
song-pattern-workbench search --config examples/configs/basic.json --pattern "I-vi-ii-V" --limit 5
song-pattern-workbench search --config examples/configs/basic.json --pattern "ii-V-I" --limit 1000 --offset 0
song-pattern-workbench search --config examples/configs/basic.json --pattern "ii-V-I" --limit 1000 --offset 1000
song-pattern-workbench eval --config examples/configs/basic.json
```

## Output

Each search writes:

- `results.json`
- `summary.md`

Each ask run writes:

- `ask_results.json`
- `ask_summary.md`

Search reports include pagination fields so the CLI can page through large result sets instead of pretending everything should be returned in one giant response.

Each eval run writes:

- `eval_results.json`
- `eval_summary.md`

## Roadmap

- fuzzy pattern matching
- song-to-song similarity search
- optional LLM explanations grounded in retrieved evidence
- melodic interval search from symbolic inputs

## License

MIT
