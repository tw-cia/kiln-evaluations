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
        def __init__(self, proc, sample):
            self.proc = proc
            self.sample_dir = out / "demo" / str(sample)
            self.project = self.sample_dir / "project"
            self.transcript = self.sample_dir / "transcript.jsonl"
            self.manifest_path = self.sample_dir / "manifest.json"

        @property
        def manifest(self):
            return json.loads(self.manifest_path.read_text())

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
        return Result(proc, sample)

    return _run
