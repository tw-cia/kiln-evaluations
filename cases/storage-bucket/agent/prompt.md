Using kiln, create a composite resource kind called `StorageBucket`.

Consumers set two things: a required `region` (string), and `versioning` (boolean,
defaulting to `true`). A `StorageBucket` composes one AWS S3 bucket in that region and,
when versioning is on, enables versioning on that bucket.

S3 bucket names are unique across all AWS accounts, so two `StorageBucket`s must never end
up asking for the same bucket name, even when they have the same `metadata.name` (in
different namespaces, or in different clusters).

Write tests for KCL, and add a sample `StorageBucket` for `kiln render` to use.
