import .storagebucket

test_storageBucketVersioningOn = lambda {
    result = storagebucket.composeStorageBucket({spec = {region = "eu-west-1"}}, {})
    assert len(result) == 2
}

test_storageBucketVersioningOff = lambda {
    result = storagebucket.composeStorageBucket({spec = {region = "eu-west-1", versioning = False}}, {})
    assert len(result) == 1
}
