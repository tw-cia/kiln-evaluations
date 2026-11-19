"""Build the bundle the generate job receives (ADR 0001): an allowlist, one case at a time.

Anything not named here is hidden by default, so a new file in a case directory never leaks.
"""

import shutil
from pathlib import Path


def plan(root: Path, samples: int) -> dict:
    """The cases x samples matrix. A case is a directory holding a prompt.md."""
    cases = sorted(p.name for p in (root / "cases").iterdir() if (p / "prompt.md").is_file())
    return {"include": [{"case": case, "sample": n} for case in cases for n in range(1, samples + 1)]}

# The minimal runner. Grading-side modules (research, bundle, report) are deliberately absent.
RUNNER_FILES = [
    ".python-version",
    "pyproject.toml",
    "uv.lock",
    "scripts/install-tooling.sh",
    "src/kiln_evaluations/__init__.py",
    "src/kiln_evaluations/__main__.py",
]


def build(root: Path, case: str, out: Path) -> None:
    shutil.rmtree(out, ignore_errors=True)
    for relative in RUNNER_FILES:
        _copy(root / relative, out / relative)
    case_dir = root / "cases" / case
    _copy(case_dir / "prompt.md", out / "cases" / case / "prompt.md")
    seed = case_dir / "seed"
    if seed.is_dir():
        shutil.copytree(seed, out / "cases" / case / "seed", symlinks=True)


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
