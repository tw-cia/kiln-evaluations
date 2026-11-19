import json
import subprocess
import sys


def _plan(root, samples):
    proc = subprocess.run([sys.executable, "-m", "kiln_evaluations", "plan", "--root", str(root), "--samples", str(samples)],
                          check=True, capture_output=True, text=True)
    return json.loads(proc.stdout)


def test_the_matrix_has_one_entry_per_case_and_sample(tmp_path):
    for name in ("beta", "alpha"):
        (tmp_path / "cases" / name).mkdir(parents=True)
        (tmp_path / "cases" / name / "prompt.md").write_text("task\n")

    assert _plan(tmp_path, 2) == {"include": [
        {"case": "alpha", "sample": 1}, {"case": "alpha", "sample": 2},
        {"case": "beta", "sample": 1}, {"case": "beta", "sample": 2},
    ]}


def test_directories_without_a_prompt_and_stray_files_are_not_cases(tmp_path):
    (tmp_path / "cases" / "real").mkdir(parents=True)
    (tmp_path / "cases" / "real" / "prompt.md").write_text("task\n")
    (tmp_path / "cases" / "support").mkdir()  # helpers, no prompt
    (tmp_path / "cases" / "conftest.py").write_text("")

    assert _plan(tmp_path, 1) == {"include": [{"case": "real", "sample": 1}]}
