"""Shared wiring for every case's checks. Lives under cases/ on purpose: the bundle the agent
receives contains only each case's prompt.md and seed/, so nothing here is ever visible to it."""

from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption("--outputs-dir", default="outputs", help="Directory holding outputs/<case>/<sample>/")


def pytest_generate_tests(metafunc):
    """Run every check once per sample found under outputs/<case>/."""
    if "sample" not in metafunc.fixturenames:
        return
    case = Path(metafunc.module.__file__).parent.name
    case_outputs = Path(metafunc.config.getoption("--outputs-dir")).resolve() / case
    samples = sorted((p for p in case_outputs.glob("*") if p.is_dir()), key=lambda p: int(p.name))
    metafunc.parametrize("sample", samples, ids=[f"{case}-{p.name}" for p in samples])
