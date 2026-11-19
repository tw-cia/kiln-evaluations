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

`prompt` (an artifact holding only the case's `prompt.md`) → `generate` (`anthropics/claude-code-action` in an empty job: no checkout, no permissions) → `static` (full checkout, no API key; runs `pytest cases --outputs-dir outputs`).

One case (`storage-bucket`), one sample, for now; more jobs and cases get added later. Secret needed: `ANTHROPIC_API_KEY`. The repo must stay private.

## Locally

`uv sync && uv run pytest` runs the tests of the checks. To run a case's checks on real Outputs: `uv run pytest cases --outputs-dir <dir holding <case>/<n>/project>`.
