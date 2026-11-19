# kiln-evaluations

Evaluates an LLM's ability to author Crossplane compositions with [kiln](https://github.com/leprechaun/kiln).

- `cases/<name>/prompt.md` — the task given to Claude Code, inside a fresh `kiln init` project.
- `kiln-evaluations run cases/<name> --sample N` — runs one sample; writes `outputs/<name>/<N>/{project,transcript.jsonl,manifest.json}`.
- `.github/workflows/evaluate.yml` — matrix of cases × samples generates outputs (has `ANTHROPIC_API_KEY`), then a `test` job checks out `tw-cia/kiln-evaluations-tests`, downloads the outputs, and runs `pytest --outputs-dir ../outputs` (no API key).

Secrets: `ANTHROPIC_API_KEY`, `TESTS_REPO_TOKEN` (read access to the tests repo).
