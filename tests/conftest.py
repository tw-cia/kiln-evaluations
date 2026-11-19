import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

# ---- running a case's checks against fixture Outputs ------------------------------------------

REPO = Path(__file__).parent.parent
GOOD_STORAGE_BUCKET = Path(__file__).parent / "fixtures" / "storage-bucket-good"


class CheckSuite:
    """Builds a tree of fixture Outputs for one case and runs the case's checks over it."""

    def __init__(self, tmp_path, case):
        self.case = case
        self.outputs = tmp_path / "outputs"
        self.tmp_path = tmp_path

    def add_sample(self, n=1, mutate=None):
        sample = self.outputs / self.case / str(n)
        shutil.copytree(GOOD_STORAGE_BUCKET, sample, symlinks=True)
        if mutate:
            mutate(sample / "project")
        return sample / "project"

    def run(self):
        """Run the case's checks; return {(check, sample_id): "passed" | "failed"}."""
        report = self.tmp_path / "report.xml"
        env = {**os.environ, "PATH": f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}"}
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(REPO / "cases" / self.case), "-p", "no:cacheprovider",
             "--outputs-dir", str(self.outputs), f"--junitxml={report}"],
            cwd=REPO, env=env, capture_output=True, text=True,
        )
        if not report.exists():
            raise AssertionError(f"checks did not run:\n{proc.stdout}\n{proc.stderr}")
        outcomes = {}
        for case in ET.parse(report).getroot().iter("testcase"):
            check, _, rest = case.get("name").partition("[")
            failed = case.find("failure") is not None or case.find("error") is not None
            outcomes[(check, rest.rstrip("]"))] = "failed" if failed else "passed"
        return outcomes


@pytest.fixture
def storage_bucket_checks(tmp_path):
    return CheckSuite(tmp_path, "storage-bucket")
