"""Static checks for the storage-bucket case. Hidden from the agent: only prompt.md ships to it."""

import shutil
import subprocess


def _copy_of_project(sample, tmp_path):
    """Checks never touch the Output itself, so run them in a throwaway copy."""
    project = tmp_path / "project"
    shutil.copytree(sample / "project", project, symlinks=True)
    return project


def _xrd_for(project, kind):
    import yaml

    for path in (project / "manifests" / "crossplane-compositions").glob("*/xrd.yaml"):
        xrd = yaml.safe_load(path.read_text())
        if xrd["spec"]["names"]["kind"] == kind:
            return xrd
    raise AssertionError(f"no generated XRD for kind {kind}")


def test_xrd_declares_the_api(sample):
    xrd = _xrd_for(sample / "project", "StorageBucket")

    for version in xrd["spec"]["versions"]:
        spec = version["schema"]["openAPIV3Schema"]["properties"]["spec"]
        assert spec["properties"]["region"]["type"] == "string"
        assert "region" in spec.get("required", [])
        versioning = spec["properties"]["versioning"]
        assert versioning["type"] == "boolean"
        assert versioning.get("default") is True


def _contents(directory):
    return {str(p.relative_to(directory)): p.read_bytes() for p in sorted(directory.rglob("*")) if p.is_file()}


def test_generated_files_are_current(sample, tmp_path):
    project = _copy_of_project(sample, tmp_path)
    generated = project / "manifests" / "crossplane-compositions"
    before = _contents(generated) if generated.exists() else {}

    result = subprocess.run(["kiln", "--root", str(project), "generate-all"], capture_output=True, text=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert _contents(generated) == before, "regenerating changed the generated files"


def _sample_xr(project):
    import yaml

    for path in (project / "render-fixtures").glob("*/xr.yaml"):
        if path.parent.name.lower() == "storagebucket":
            return yaml.safe_load(path.read_text())
    raise AssertionError("no sample StorageBucket XR under render-fixtures/")


def _bucket_external_name(project, xr, path):
    """Render the XR and return the composed Bucket's external name (None if Crossplane generates one)."""
    import yaml

    path.write_text(yaml.safe_dump(xr))
    result = subprocess.run(
        ["kiln", "--root", str(project), "render", "StorageBucket", "--xr", str(path), "--no-validate"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    buckets = [doc for doc in yaml.safe_load_all(result.stdout) if doc and doc.get("kind") == "Bucket"]
    assert len(buckets) == 1, f"expected one composed Bucket, got {len(buckets)}:\n{result.stdout}"
    return (buckets[0]["metadata"].get("annotations") or {}).get("crossplane.io/external-name")


def test_bucket_names_do_not_collide_across_namespaces(sample, tmp_path):
    """S3 names are global: the same XR name in two namespaces must not ask for the same bucket."""
    project = _copy_of_project(sample, tmp_path)
    xr = _sample_xr(project)
    xr["metadata"]["name"] = "same-name"

    in_a = _bucket_external_name(
        project, {**xr, "metadata": {**xr["metadata"], "namespace": "ns-a", "uid": "00000000-0000-0000-0000-00000000000a"}}, tmp_path / "a.yaml"
    )
    in_b = _bucket_external_name(
        project, {**xr, "metadata": {**xr["metadata"], "namespace": "ns-b", "uid": "00000000-0000-0000-0000-00000000000b"}}, tmp_path / "b.yaml"
    )

    # no external name at all means Crossplane names the bucket itself, which is unique
    assert in_a is None or in_a != in_b, f"both namespaces get the S3 bucket name {in_a!r}"
    assert in_a != "same-name", "the bucket is named after the bare XR name"
