import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

FAKE_CLAUDE = Path(__file__).parent / "fake_claude.py"


@pytest.fixture
def run_case(tmp_path):
    """Run `kiln-evaluations run` against a throwaway case with a scripted fake `claude`.

    Returns a function: run_case(scenario, sample=1, run_id="t1", env=None, args=()) -> Result
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    claude = bin_dir / "claude"
    claude.write_text(f"#!{sys.executable}\n" + FAKE_CLAUDE.read_text())
    claude.chmod(0o755)

    case = tmp_path / "cases" / "demo"
    case.mkdir(parents=True)
    (case / "prompt.md").write_text("Using kiln, create a composite kind called Demo.\n")
    out = tmp_path / "outputs"

    class Result:
        def __init__(self, proc, sample, env):
            self.proc = proc
            self.env = env
            self.sample_dir = out / "demo" / str(sample)
            self.project = self.sample_dir / "project"
            self.transcript = self.sample_dir / "transcript.jsonl"
            self.manifest_path = self.sample_dir / "manifest.json"

        @property
        def manifest(self):
            return json.loads(self.manifest_path.read_text())

        def analyzed(self):
            """Run the grading-side `analyze` step over the outputs, then return the sample's manifest."""
            subprocess.run([sys.executable, "-m", "kiln_evaluations", "analyze", "--out", str(out)],
                           env=self.env, check=True, capture_output=True, text=True)
            return self.manifest

    def _run(scenario=None, sample=1, run_id="t1", env=None, args=()):
        scenario_file = tmp_path / "scenario.json"
        scenario_file.write_text(json.dumps(scenario or {}))
        full_env = {
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}",
            "FAKE_CLAUDE_SCENARIO": str(scenario_file),
            **(env or {}),
        }
        proc = subprocess.run(
            [sys.executable, "-m", "kiln_evaluations", "run", str(case),
             "--sample", str(sample), "--out", str(out), "--run-id", run_id, *args],
            env=full_env, capture_output=True, text=True,
        )
        return Result(proc, sample, full_env)

    return _run


# ---- running a case's checks against fixture Outputs ------------------------------------------

import shutil
import xml.etree.ElementTree as ET

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
