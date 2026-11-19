"""The bundle is all the generate job (and so the agent) ever receives: an allowlist, one case at a time."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent

# Everything the agent may be given for the case `alpha`. Nothing else, ever.
EXPECTED = {
    ".python-version",
    "pyproject.toml",
    "uv.lock",
    "scripts/install-tooling.sh",
    "src/kiln_evaluations/__init__.py",
    "src/kiln_evaluations/__main__.py",
    "cases/alpha/prompt.md",
    "cases/alpha/seed/kcl-scripts/start.k",
}


@pytest.fixture
def repo(tmp_path):
    """A copy of this repo plus two synthetic cases, one of them stuffed with things that must stay hidden."""
    root = tmp_path / "repo"
    shutil.copytree(REPO, root, symlinks=True, ignore=shutil.ignore_patterns(".venv", ".git", "outputs", "__pycache__"))
    alpha, beta = root / "cases" / "alpha", root / "cases" / "beta"
    (alpha / "seed" / "kcl-scripts").mkdir(parents=True)
    (alpha / "seed" / "kcl-scripts" / "start.k").write_text("# starting point\n")
    (alpha / "prompt.md").write_text("Alpha task\n")
    (alpha / "test_static.py").write_text("def test_x(): pass\n")
    (alpha / "fixtures").mkdir()
    (alpha / "fixtures" / "xr.yaml").write_text("kind: X\n")
    beta.mkdir()
    (beta / "prompt.md").write_text("Beta task, which alpha's agent must never see\n")
    return root


def _bundle(repo, tmp_path, case="alpha"):
    out = tmp_path / "bundle"
    shutil.rmtree(out, ignore_errors=True)
    subprocess.run([sys.executable, "-m", "kiln_evaluations", "bundle", case, "--root", str(repo), "--out", str(out)],
                   check=True, capture_output=True, text=True)
    return out


def _files(root):
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


def test_a_bundle_holds_exactly_the_allowlisted_files_for_its_own_case(repo, tmp_path):
    assert _files(_bundle(repo, tmp_path)) == EXPECTED


def test_a_new_file_dropped_into_a_case_directory_is_hidden_by_default(repo, tmp_path):
    (repo / "cases" / "alpha" / "notes.md").write_text("grader notes\n")
    (repo / "cases" / "alpha" / "expected").mkdir()
    (repo / "cases" / "alpha" / "expected" / "answer.yaml").write_text("secret\n")

    assert _files(_bundle(repo, tmp_path)) == EXPECTED


def test_the_bundled_runner_works_without_the_grading_code(repo, tmp_path):
    bundle = _bundle(repo, tmp_path)
    scenario = tmp_path / "scenario.json"
    scenario.write_text('{"tool_uses": [{"name": "WebSearch", "input": {"query": "x"}}]}')
    fake = tmp_path / "bin"
    fake.mkdir()
    (fake / "claude").write_text(f"#!{sys.executable}\n" + (REPO / "tests" / "fake_claude.py").read_text())
    (fake / "claude").chmod(0o755)
    env = {**os.environ, "PYTHONPATH": str(bundle / "src"), "FAKE_CLAUDE_SCENARIO": str(scenario),
           "PATH": f"{fake}{os.pathsep}{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}"}

    run = subprocess.run([sys.executable, "-m", "kiln_evaluations", "run", str(bundle / "cases" / "alpha"),
                          "--out", str(tmp_path / "outputs")], cwd=bundle, env=env, capture_output=True, text=True)
    grading = subprocess.run([sys.executable, "-c", "import kiln_evaluations.research"],
                             cwd=bundle, env=env, capture_output=True, text=True)

    assert run.returncode == 0, run.stderr
    assert (tmp_path / "outputs" / "alpha" / "1" / "manifest.json").exists()
    assert grading.returncode != 0  # the rules the agent is judged by are not on its machine
