# song-pattern-workbench

`song-pattern-workbench` is a CLI-first retrieval and evaluation workbench for finding recurring harmonic patterns across songs.

It is built around a simple idea:

- normalize a query like `ii-V-I`
- retrieve matching songs from a music-pattern source
- enrich those matches with catalog metadata
- cache results for repeatability
- evaluate whether known queries return the expected tunes

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

- generic pattern-source endpoints through `endpoint_template`
- generic metadata endpoints through `endpoint_template`
- a concrete `musicbrainz_lookup` mode for title and artist enrichment

That keeps the repo honest:

- fixture mode works out of the box
- API mode is ready for real credentials
- provider details can be adapted without changing the search pipeline

Example API config:

```json
{
  "providers": {
    "hooktheory": {
      "type": "api",
      "endpoint_template": "https://provider.example/search?pattern={pattern}&limit={limit}",
      "token_env": "HOOKTHEORY_API_TOKEN"
    },
    "musicbrainz": {
      "type": "musicbrainz_lookup"
    }
  }
}
```

See `examples/configs/api.json` for a concrete starting point.

## Example Queries

```bash
song-pattern-workbench search --config examples/configs/basic.json --pattern "ii-V-I"
song-pattern-workbench search --config examples/configs/basic.json --pattern "I-vi-ii-V" --limit 5
song-pattern-workbench eval --config examples/configs/basic.json
```

## Output

Each search writes:

- `results.json`
- `summary.md`

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
