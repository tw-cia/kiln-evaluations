# Keep the agent blind by shipping it an allowlist, not by sandboxing it

Cases, prompts and checks live together in this repo, but the agent must never see the checks. The `plan` job builds a bundle from an explicit allowlist (each case's `prompt.md` and `seed/`, plus the runner), and the `generate` job downloads only that bundle, runs with `permissions: {}` and never checks out the repo. We rejected a Docker sandbox around the agent because kiln's tooling (`crossplane render`) needs the host's Docker, and handing a container the Docker socket would leak more than it protects.

## Consequences

- Blindness holds only while the repo is **private**: the agent has no credentials to clone it. If the repo is made public, anyone (including the agent, via `git clone`) can read the checks, and artifacts and transcripts become publicly downloadable. Move the checks, and ideally the cases, to a private repo first.
- New files in a case directory are hidden by default, because only allowlisted paths enter the bundle.
- The API key is in the agent's environment. Transcripts are scrubbed of its literal value before upload, but the agent can still read it. The key is managed by someone else, so a dedicated spend-limited key was not an option.
