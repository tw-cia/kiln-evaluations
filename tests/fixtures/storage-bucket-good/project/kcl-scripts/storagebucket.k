import .schemas_compositions
import .schemas_providers

composeStorageBucket = lambda oxr, ocds -> [any] {
    spec: schemas_compositions.StorageBucketSpec = oxr.spec

    _bucketName = "bucket"
    _versioningName = "versioning"

    _bucketForProvider: schemas_providers.S3AwsmUpboundIoV1beta1BucketSpecForProvider = {
        region = spec.region
    }
    _bucket = {
        apiVersion = "s3.aws.m.upbound.io/v1beta1"
        kind = "Bucket"
        metadata.annotations = {"krm.kcl.dev/composition-resource-name" = _bucketName}
        spec.forProvider = _bucketForProvider
    }

    _versioningForProvider: schemas_providers.S3AwsmUpboundIoV1beta1BucketVersioningSpecForProvider = {
        region = spec.region
        bucketRef = {name = "bucket"}
        versioningConfiguration = {status = "Enabled"}
    }
    _versioning = {
        apiVersion = "s3.aws.m.upbound.io/v1beta1"
        kind = "BucketVersioning"
        metadata.annotations = {"krm.kcl.dev/composition-resource-name" = _versioningName}
        spec.forProvider = _versioningForProvider
    }

    [_bucket, _versioning] if spec.versioning else [_bucket]
}
