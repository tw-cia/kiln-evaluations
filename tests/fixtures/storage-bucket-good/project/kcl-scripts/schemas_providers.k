# Curated provider schemas. `kiln import <crd>` appends here.

schema S3AwsmUpboundIoV1beta1BucketSpecForProvider:
    r"""
    bucket v1beta1 spec for provider

    Attributes
    ----------
    region : str, default is Undefined, optional
        region
    """


    region?: str




schema S3AwsmUpboundIoV1beta1BucketStatusAtProvider:
    r"""
    bucket v1beta1 status at provider

    Attributes
    ----------
    id : str, default is Undefined, optional
        id
    """


    id?: str

schema S3AwsmUpboundIoV1beta1BucketVersioningSpecForProviderBucketRef:
    r"""
    bucket versioning v1beta1 for provider bucket ref

    Attributes
    ----------
    name : str, default is Undefined, optional
        name
    """


    name?: str




schema S3AwsmUpboundIoV1beta1BucketVersioningSpecForProviderVersioningConfiguration:
    r"""
    bucket versioning v1beta1 for provider versioning configuration

    Attributes
    ----------
    status : str, default is Undefined, optional
        status
    """


    status?: str




schema S3AwsmUpboundIoV1beta1BucketVersioningSpecForProvider:
    r"""
    bucket versioning v1beta1 spec for provider

    Attributes
    ----------
    bucketRef : S3AwsmUpboundIoV1beta1BucketVersioningSpecForProviderBucketRef, default is Undefined, optional
        bucket ref
    region : str, default is Undefined, optional
        region
    versioningConfiguration : S3AwsmUpboundIoV1beta1BucketVersioningSpecForProviderVersioningConfiguration, default is Undefined, optional
        versioning configuration
    """


    bucketRef?: S3AwsmUpboundIoV1beta1BucketVersioningSpecForProviderBucketRef

    region?: str

    versioningConfiguration?: S3AwsmUpboundIoV1beta1BucketVersioningSpecForProviderVersioningConfiguration




schema S3AwsmUpboundIoV1beta1BucketVersioningStatusAtProvider:
    r"""
    bucket versioning v1beta1 status at provider

    Attributes
    ----------
    id : str, default is Undefined, optional
        id
    """


    id?: str


