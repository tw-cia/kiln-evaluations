"""Static checks for the static-website case. Hidden from the agent: only prompt.md ships to it."""

import shutil
import subprocess

import pytest
import yaml

KIND = "StaticWebsite"


def _copy_of_project(sample, tmp_path):
    """Checks never touch the Output itself, so run them in a throwaway copy."""
    project = tmp_path / "project"
    shutil.copytree(sample / "project", project, symlinks=True)
    return project


def _xrd(project):
    for path in (project / "manifests" / "crossplane-compositions").glob("*/xrd.yaml"):
        xrd = yaml.safe_load(path.read_text())
        if xrd["spec"]["names"]["kind"] == KIND:
            return xrd
    raise AssertionError(f"no generated XRD for kind {KIND}")


def _sample_xr(project):
    for path in (project / "render-fixtures").glob("*/xr.yaml"):
        if path.parent.name.lower() == KIND.lower():
            return yaml.safe_load(path.read_text())
    raise AssertionError(f"no sample {KIND} XR under render-fixtures/")


def _render(project, xr, path, observed=None):
    """Render the Composition against an XR (and optionally observed resources); return the composed resources."""
    path.write_text(yaml.safe_dump(xr))
    command = ["kiln", "--root", str(project), "render", KIND, "--xr", str(path), "--no-validate"]
    if observed is not None:
        command += ["--observed-resources", str(observed)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return [doc for doc in yaml.safe_load_all(result.stdout) if doc and doc.get("kind") != KIND]


def _of_kind(resources, kind):
    return [r for r in resources if r["kind"] == kind]


def test_xrd_declares_the_api(sample):
    xrd = _xrd(sample / "project")

    for version in xrd["spec"]["versions"]:
        spec = version["schema"]["openAPIV3Schema"]["properties"]["spec"]
        for required in ("domainName", "hostedZoneId"):
            assert spec["properties"][required]["type"] == "string"
            assert required in spec.get("required", [])
        region = spec["properties"]["region"]
        assert region["type"] == "string"
        assert region.get("default") == "ap-southeast-1"
        assert "region" not in spec.get("required", []) or region.get("default")


def _contents(directory):
    return {str(p.relative_to(directory)): p.read_bytes() for p in sorted(directory.rglob("*")) if p.is_file()}


def test_generated_files_are_current(sample, tmp_path):
    project = _copy_of_project(sample, tmp_path)
    generated = project / "manifests" / "crossplane-compositions"
    before = _contents(generated) if generated.exists() else {}

    result = subprocess.run(["kiln", "--root", str(project), "generate-all"], capture_output=True, text=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert _contents(generated) == before, "regenerating changed the generated files"


@pytest.fixture
def stages(sample, tmp_path):
    """The Composition rendered cold, then once per observed-*.yaml fixture, in name order: a list of stages.

    The distribution needs the certificate's ARN and the DNS records need the validation options, which only
    exist once AWS reports them, so a later stage is the only place some of the resources can appear.
    """
    project = _copy_of_project(sample, tmp_path)
    xr = _sample_xr(project)
    fixtures = next(d for d in (project / "render-fixtures").iterdir() if d.name.lower() == KIND.lower())
    observed = [None, *sorted(fixtures.glob("observed-*.yaml"))]
    return [_render(project, xr, tmp_path / f"xr-{number}.yaml", stage) for number, stage in enumerate(observed)]


@pytest.fixture
def rendered(stages):
    """The final stage, where everything the agent expects to exist does: the one to judge the shape of each resource on."""
    return stages[-1]


def test_it_composes_the_four_kinds_of_resource(stages):
    kinds = {r["kind"] for stage in stages for r in stage}

    assert {"Bucket", "Certificate", "Distribution", "Record"} <= kinds, (
        f"composed only {sorted(kinds)}: do the sample XR and its observed-*.yaml stages reach every resource?"
    )


def test_the_bucket_blocks_public_access(rendered):
    blocks = _of_kind(rendered, "BucketPublicAccessBlock")

    assert blocks, "no BucketPublicAccessBlock composed"
    for field in ("blockPublicAcls", "blockPublicPolicy", "ignorePublicAcls", "restrictPublicBuckets"):
        assert blocks[0]["spec"]["forProvider"].get(field) is True, field


def test_the_certificate_is_dns_validated_for_the_domain(rendered):
    [certificate] = _of_kind(rendered, "Certificate")
    spec = certificate["spec"]["forProvider"]

    assert spec["validationMethod"] == "DNS"
    assert spec["domainName"]
    # CloudFront only accepts certificates issued in us-east-1
    assert spec["region"] == "us-east-1"


def test_the_distribution_serves_the_domain_over_https(rendered):
    [distribution] = _of_kind(rendered, "Distribution")
    spec = distribution["spec"]["forProvider"]

    assert spec["aliases"], "the distribution has no alias for the custom domain"
    assert spec["defaultRootObject"] == "index.html"
    behaviour = spec["defaultCacheBehavior"]
    assert behaviour["viewerProtocolPolicy"] == "redirect-to-https"


def test_bucket_names_do_not_collide_across_namespaces(sample, tmp_path):
    """S3 names are global: the same XR name in two namespaces must not ask for the same bucket."""
    project = _copy_of_project(sample, tmp_path)
    xr = _sample_xr(project)
    xr["metadata"]["name"] = "same-name"

    def bucket_name(namespace, uid, path):
        metadata = {**xr["metadata"], "namespace": namespace, "uid": uid}
        [bucket] = _of_kind(_render(project, {**xr, "metadata": metadata}, path), "Bucket")
        return (bucket["metadata"].get("annotations") or {}).get("crossplane.io/external-name")

    in_a = bucket_name("ns-a", "00000000-0000-0000-0000-00000000000a", tmp_path / "a.yaml")
    in_b = bucket_name("ns-b", "00000000-0000-0000-0000-00000000000b", tmp_path / "b.yaml")

    # no external name at all means Crossplane names the bucket itself, which is unique
    assert in_a is None or in_a != in_b, f"both namespaces get the S3 bucket name {in_a!r}"
    assert in_a != "same-name", "the bucket is named after the bare XR name"
