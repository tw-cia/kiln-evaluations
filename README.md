# kiln-evaluations

Evaluates how well an LLM agent can use [kiln](https://github.com/leprechaun/kiln): the agent gets a task in a fresh `kiln init` project, and hidden checks judge what it produces. See `GLOSSARY.md` for the vocabulary and `docs/adr/` for the decisions behind the design.

Everything runs in GitHub Actions (`.github/workflows/evaluate.yml`); the only code is the checks.

```
cases/<name>/
  prompt.md              what the agent sees (the only file of a case that leaves the repo checkout)
  test_*.py, fixtures/   the hidden checks
tests/                   tests of the checks themselves (a good Output, and broken ones)
```

## Pipeline

Built one job at a time (`.github/workflows/evaluate.yml`); manual trigger only for now.

1. `prompt`: extract the case's `prompt.md` into an artifact (no cloud credentials)
2. `generate`: `anthropics/claude-code-action` in an empty job (Claude key; no checkout, no permissions, no AWS)
3. `static`: full checkout, hidden checks over the downloaded Output (no credentials)

Designed, not built yet (ADR 0003): the agent writes an XR, static checks on it, a human gate, apply to the cluster with AWS credentials (no Claude key), teardown. No job holds more than one kind of credential. Secret: `ANTHROPIC_API_KEY`, in the `claude` environment. The repo must stay private.

## Locally

`uv sync && uv run pytest` runs the tests of the checks. To run a case's checks on real Outputs: `uv run pytest cases --outputs-dir <dir holding <case>/<n>/project>`.
