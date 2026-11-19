"""Shared wiring for every case's checks. Lives under cases/ on purpose: only a case's agent/ directory
is ever given to the agent, so nothing here (or in a case's tests/) is ever visible to it."""

from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption("--outputs-dir", default="outputs", help="Directory holding outputs/<case>/<sample>/")


def pytest_generate_tests(metafunc):
    """Run every check once per sample found under outputs/<case>/."""
    if "sample" not in metafunc.fixturenames:
        return
    case = Path(metafunc.module.__file__).parent.parent.name  # cases/<case>/tests/test_*.py
    case_outputs = Path(metafunc.config.getoption("--outputs-dir")).resolve() / case
    samples = sorted((p for p in case_outputs.glob("*") if p.is_dir()), key=lambda p: int(p.name))
    metafunc.parametrize("sample", samples, ids=[f"{case}-{p.name}" for p in samples])
