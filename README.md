# kiln-evaluations

Evaluates how well an LLM agent can use [kiln](https://github.com/leprechaun/kiln): the agent gets a task in a fresh `kiln init` project, and hidden checks judge what it produces. See `GLOSSARY.md` for the vocabulary and `docs/adr/` for the decisions behind the design.

```
cases/<name>/
  agent/         everything the agent may see: prompt.md, plus any starting context (the only part that leaves the checkout)
  tests/         the hidden checks and their fixtures: never given to the agent
shared/
  agent/         context given to every case's agent (opencode.json, ...), merged under the case's own agent/ by the pipeline
tests/           tests of the checks themselves (a good Output, and broken ones)
```

## Pipeline

The whole evaluation runs on GitHub Actions, in `.github/workflows/evaluate.yml`. Nothing is run locally. It starts on every push, to any branch, or by hand from the Actions tab (`workflow_dispatch`).

```
setup ──┬─ agent-<model> ── test-<model>     one pair per model, independent of each other
        ├─ ...
aws-readonly, aws-github-actions             check the AWS roles; independent of the rest
```

1. **setup** checks out the repo and uploads two artifacts: `shared` (`shared/agent/`) and `case-<name>` (the case's `agent/`). Only these leave the checkout, so the hidden checks never reach the agent.
2. **agent-\<model\>** has no checkout and no GitHub token, only the LLM credentials. It downloads `shared`, then the case on top (so the case wins), installs `kcl`, `crossplane`, `kiln` and `opencode`, runs `kiln init` for an API group of `<case>.<model>.platform.demotw.com`, and runs `opencode run` non-interactively with `prompt.md` and every permission allowed. The model comes from the OpenAI-compatible endpoint set in `shared/agent/opencode.json` (`TW_OPENAI_API_URL` and `TW_OPENAI_API_KEY` secrets).
3. **test-\<model\>** checks out the repo, downloads the agent's workspace as `outputs/<case>/1/project`, and requires `kcl test`, `kiln render-all` and the hidden pytest checks to pass.

Each model gets its own pair of jobs and its own artifacts:

| Artifact | Contents | Kept |
| --- | --- | --- |
| `workspace-storage-bucket-<model>` | the agent's project, input to `test` | 1 day |
| `session-storage-bucket-<model>` | opencode `events.jsonl`, `session.json` and `stats.txt` | 30 days |

Token use per run is in the `agent` job's summary page. The full session is in the `session-*` artifact, for inspecting what the agent did.

The `aws-readonly` and `aws-github-actions` jobs assume the two AWS roles through OIDC and print the caller identity.

### Adding a model

1. Add it to `models` in `shared/agent/opencode.json`. The key is the id the endpoint serves.
2. Copy an `agent-*` and `test-*` pair in `evaluate.yml`. Set `MODEL_SLUG` (a DNS-safe name), the `--model agentworks/<id>` argument, and the artifact names.

### Pinned tooling

`kcl`, `crossplane` (the CLI from `cli.crossplane.io`), and `kiln` (a commit that must equal the one in `uv.lock`) are pinned as workflow-level env vars, so runs stay comparable.
