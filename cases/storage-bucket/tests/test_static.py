"""Static checks for the storage-bucket case. Hidden from the agent: only prompt.md ships to it."""

import re
import shutil
import subprocess


def _copy_of_project(sample, tmp_path):
    """Checks never touch the Output itself, so run them in a throwaway copy."""
    project = tmp_path / "project"
    shutil.copytree(sample / "project", project, symlinks=True)
    return project


def test_kcl_tests_pass(sample, tmp_path):
    project = _copy_of_project(sample, tmp_path)

    result = subprocess.run(["kcl", "test", "."], cwd=project / "kcl-scripts", capture_output=True, text=True)

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    # `kcl test .` is green when there are no tests, so insist on at least one that covers the kind
    passed = re.search(r"PASS: (\d+)/", output)
    assert passed and int(passed.group(1)) >= 1, f"no tests ran:\n{output}"
    covers_kind = any(
        "composeStorageBucket" in test_file.read_text()
        for test_file in (project / "kcl-scripts").glob("*_test.k")
    )
    assert covers_kind, "no test file exercises composeStorageBucket"


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
