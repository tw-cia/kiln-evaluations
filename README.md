# kiln-evaluations

Evaluates how well an LLM agent can use [kiln](https://github.com/leprechaun/kiln): the agent gets a task in a fresh `kiln init` project, and hidden checks judge what it produces. See `GLOSSARY.md` for the vocabulary and `docs/adr/` for the decisions behind the design.

```
cases/<name>/
  agent/         everything the agent may see: prompt.md, plus any starting context (the only part that leaves the checkout)
  tests/         the hidden checks and their fixtures: never given to the agent
tests/           tests of the checks themselves (a good Output, and broken ones)
```

## Pipeline

None yet: being defined step by step.

## Locally

`uv sync && uv run pytest` runs the tests of the checks. To run a case's checks on real Outputs: `uv run pytest cases --outputs-dir <dir holding <case>/<n>/project>`.
