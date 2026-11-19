# Your composite resource (XR) spec schemas, one per kind, e.g. `schema MyKindSpec:`.

schema StorageBucketSpec:
    region: str
    versioning: bool = True
