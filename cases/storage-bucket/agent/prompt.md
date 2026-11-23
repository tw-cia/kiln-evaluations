Using kiln, create a composite resource kind called `StorageBucket`.

Consumers set two things: a required `region` (string), and `versioning` (boolean,
defaulting to `true`). A `StorageBucket` composes one AWS S3 bucket in that region and,
when versioning is on, enables versioning on that bucket.

Write tests for KCL, and add a sample `StorageBucket` for `kiln render` to use.
