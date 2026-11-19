# Run live checks on a persistent shared EKS cluster, on `main` only, behind a human gate

Live checks apply a sample's Compositions to an existing EKS cluster whose providers already hold admin credentials in a disposable AWS account, and probe the real AWS resources. We chose that over an ephemeral `kind` cluster because real AWS is the point (real URLs, real services) and the cluster already has every provider and function kiln knows about. The cost is that untrusted, agent-written compositions run with powerful credentials, so the live job runs only on `main` (the OIDC trust is limited to that ref), pauses for a human to review the generated output through a GitHub Environment with required reviewers, and never installs or upgrades anything on the cluster.

## Consequences

- Cluster-scoped objects (XRDs, Compositions) are shared across samples and runs, so each sample gets its own API group (`s<run>-<n>.eval.example.com`) and namespace (`eval-<run>-<n>`), and live runs are serialised with a `concurrency` group.
- Teardown deletes the namespace, relying on the cascade to remove composed AWS resources, then deletes that sample's XRDs and Compositions by label. A composition with `deletionPolicy: Orphan` would defeat the cascade, so such samples are rejected before applying.
- Teardown that does not finish within 15 minutes makes the sample `infra_error` and flags the run for manual cleanup. No tag-based sweeper until a manual cleanup proves one necessary.
- Until a permissions boundary exists on the providers' role, only cases that create no IAM resources (S3 first) are allowed to run live.
- Crossplane, provider and function versions belong to the cluster, not to this repo, so every manifest records them.
- Probes use a separate OIDC-assumed role with only the service permissions the current cases need.
