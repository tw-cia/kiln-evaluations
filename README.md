# kiln-evaluations

Evaluates how well an LLM agent can use [kiln](https://github.com/leprechaun/kiln): the agent gets a task in a fresh `kiln init` project, and hidden checks judge what it produces. See `GLOSSARY.md` for the vocabulary and `docs/adr/` for the decisions that shape the design.

```
cases/<name>/
  prompt.md          what the agent sees
  seed/              optional starting project state (agent sees it)
  fixtures/, test_*.py   grader only: never leave the repo checkout
src/kiln_evaluations/    runner (shipped to the agent's job) and grading-side modules (not shipped)
tests/                   tests of the harness itself
```

## Commands

| Command | Does |
|---|---|
| `kiln-evaluations run cases/<name> --sample N` | one sample: project, scrubbed transcript and manifest under `outputs/<name>/<N>/` |
| `kiln-evaluations analyze --out outputs` | grading side: adds Research accounting to the manifests |
| `kiln-evaluations plan --samples N` | the cases x samples matrix, as JSON |
| `kiln-evaluations bundle <name> --out DIR` | the allowlist bundle the generate job receives for one case |
| `pytest cases --outputs-dir outputs` | the hidden checks, once per sample |
| `pytest` | tests of the harness (uses a scripted fake `claude`) |

## Pipeline (`.github/workflows/evaluate.yml`)

`plan` → `bundle` (one per case) → `generate` (API key, no token, no checkout) → `static` (full checkout, no API key).
Live checks and the report are later tickets. Secret needed: `ANTHROPIC_API_KEY`. The repo must stay private.
