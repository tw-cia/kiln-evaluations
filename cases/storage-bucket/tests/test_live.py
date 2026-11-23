"""Live checks for the storage-bucket case: probe what Crossplane really created in AWS.

Hidden from the agent. They read the composed resources recorded from the cluster (LIVE_RESOURCES) and ask AWS
about them; without that file they skip, so the static run is unaffected.
"""

import json
import os
import re
import subprocess

import pytest

RESOURCES = os.environ.get("LIVE_RESOURCES")

pytestmark = pytest.mark.skipif(not RESOURCES, reason="LIVE_RESOURCES not set: no live run to probe")

# names come from agent-written compositions: never pass anything else to the aws CLI
BUCKET_NAME = re.compile(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]")


def _aws(*args):
    result = subprocess.run(["aws", *args, "--output", "json"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout or "{}")


@pytest.fixture(scope="module")
def live():
    with open(RESOURCES) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def bucket(live):
    buckets = [r for r in live["resources"] if r["kind"] == "Bucket"]
    assert len(buckets) == 1, f"expected exactly one composed Bucket, got {len(buckets)}"
    name = (buckets[0]["metadata"].get("annotations") or {}).get("crossplane.io/external-name")
    assert name and BUCKET_NAME.fullmatch(name), f"not a usable S3 bucket name: {name!r}"
    return name


def test_the_bucket_exists_in_the_requested_region(live, bucket):
    region = live["xr"]["spec"]["region"]

    location = _aws("s3api", "get-bucket-location", "--bucket", bucket)["LocationConstraint"]

    assert location == region  # (S3 reports us-east-1 as null, which this sample never asks for)


def test_versioning_matches_the_request(live, bucket):
    spec = live["xr"]["spec"]

    status = _aws("s3api", "get-bucket-versioning", "--bucket", bucket, "--region", spec["region"]).get("Status")

    assert (status == "Enabled") == bool(spec.get("versioning", True)), f"versioning is {status!r}"
