# No job holds more than one kind of credential, and jobs that run agent code hold none

The pipeline is a chain of jobs, each with the least it needs: extracting the case (checkout, no cloud credentials), the agent working (Claude key, no checkout, no AWS), static checks and rendering (checkout, no credentials), the agent writing an XR (Claude key, no AWS), applying to the cluster (AWS, no Claude key). Jobs that execute agent-written code (`kcl test`, `kiln render`) never hold a credential, and the one job that holds AWS credentials only applies YAML, never runs agent code. Secrets live in GitHub Environments (`claude`, and an `aws` one with required reviewers, limited to `main`) so the platform, not convention, keeps a job from reaching a secret it does not declare. We chose this over one job with everything because a prompt-injected or merely clever agent could otherwise turn a Claude job into a cloud-credential job.

## Consequences

- Artifacts are untrusted input to later jobs. Jobs with a checkout download them only into `outputs/`, and the apply job takes the composition from the generate artifact and exactly one file (the XR) from the XR-generation artifact.
- The XR is written by an agent from a second, agent-visible prompt, so the expected values live in that prompt and the live checks know what to assert.
- A human reviews the composition and the XR at the `aws` environment's approval, before anything touches the cluster. Teardown is a separate `if: always()` job.
- Tests over the workflow file enforce the matrix (no job references both Claude and AWS credentials, and so on). Weakening one is a deliberate act.
