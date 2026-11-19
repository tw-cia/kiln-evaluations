# Keep the agent blind by giving its job only its prompt, not by sandboxing it

Cases, prompts and checks live together in this repo, but the agent must never see the checks. A `prompts` job uploads one artifact per case containing only that case's `prompt.md`; the `generate` job downloads just that artifact, runs with `permissions: {}`, and never checks out the repo. We rejected a Docker sandbox around the agent because kiln's tooling (`crossplane render`) needs the host's Docker, and handing a container the Docker socket would leak more than it protects.

## Consequences

- Blindness holds only while the repo is **private**: the agent has no credentials to clone it. If the repo is made public, anyone (including the agent, via `git clone`) can read the checks, and artifacts and transcripts become publicly downloadable. Move the checks, and ideally the cases, to a private repo first.
- Only an explicit file (`prompt.md`, later `seed/`) ever enters a case's artifact, so a new file in a case directory is hidden by default.
- `anthropics/claude-code-action` mints a GitHub App token through OIDC unless it is given a `github_token`. The generate job therefore passes its own zero-permission `github.token` and grants no `id-token: write`, so no token that can read the repo ever exists in that job. Pinned by commit SHA, since it runs with the API key.
- The API key is in the agent's environment. Outputs are scrubbed of its literal value before upload, but the agent can still read it. The key is managed by someone else, so a dedicated spend-limited key was not an option.
- Grading rules (for example how Research is counted) must never run in the generate job, since the agent shares that machine.
