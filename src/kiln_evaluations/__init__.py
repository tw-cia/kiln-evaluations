"""Generate-side runner: have Claude Code solve a kiln task and record the result."""

import argparse
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_case(
    case: Path, sample: int, out: Path, run_id: str, model: str, max_turns: int, max_budget_usd: float
) -> int:
    sample_dir = out / case.name / str(sample)
    shutil.rmtree(sample_dir, ignore_errors=True)
    sample_dir.mkdir(parents=True)
    group = f"s{run_id}-{sample}.eval.example.com"
    project = sample_dir / "project"
    subprocess.run(["kiln", "init", str(project), "--group", group], check=True, capture_output=True)

    prompt = (case / "prompt.md").read_text()
    with (sample_dir / "transcript.jsonl").open("w") as transcript:
        try:
            subprocess.run(
                [
                    "claude", "-p", prompt,
                    "--output-format", "stream-json", "--verbose",
                    "--model", model,
                    "--max-turns", str(max_turns),
                    "--max-budget-usd", str(max_budget_usd),
                ],
                cwd=project,
                stdout=transcript,
            )
        except OSError:
            pass  # claude could not be started: no result event, so the outcome is infra_error

    _scrub_secret(sample_dir)
    result = _final_result(sample_dir / "transcript.jsonl")
    usage = result.get("usage", {})
    manifest = {
        "case": case.name,
        "sample": sample,
        "outcome": _outcome(result),
        "model": model,
        "max_turns": max_turns,
        "max_budget_usd": max_budget_usd,
        "claude_version": _claude_version(),
        "kiln_commit": _kiln_commit(),
        "num_turns": result.get("num_turns"),
        "cost_usd": result.get("total_cost_usd"),
        "tokens": {
            "input": usage.get("input_tokens"),
            "output": usage.get("output_tokens"),
            "cache_read": usage.get("cache_read_input_tokens"),
            "cache_creation": usage.get("cache_creation_input_tokens"),
        },
    }
    (sample_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return 0


def _claude_version() -> str | None:
    try:
        return subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip() or None
    except OSError:
        return None


def _kiln_commit() -> str | None:
    """The commit kiln was installed from (kiln has no --version, so read the package metadata)."""
    direct_url = importlib.metadata.distribution("kiln").read_text("direct_url.json")
    return json.loads(direct_url)["vcs_info"]["commit_id"] if direct_url else None


def _scrub_secret(root: Path) -> None:
    """Replace the literal API key in every text file under root, so Outputs are safe to upload."""
    secret = os.environ.get("ANTHROPIC_API_KEY")
    if not secret:
        return
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        if secret in text:
            path.write_text(text.replace(secret, "[REDACTED]"))


_CAP_SUBTYPES = {"error_max_turns", "error_max_budget_usd"}


def _outcome(result: dict) -> str:
    if not result:
        return "infra_error"
    if result.get("subtype") in _CAP_SUBTYPES:
        return "exhausted"
    return "infra_error" if result.get("is_error") else "completed"


def _final_result(transcript: Path) -> dict:
    result = {}
    for line in transcript.read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            result = event
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="kiln-evaluations")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run one sample of one case")
    run.add_argument("case", type=Path, help="Case directory")
    run.add_argument("--sample", type=int, default=1)
    run.add_argument("--out", type=Path, default=Path("outputs"))
    run.add_argument("--run-id", default="local")
    run.add_argument("--model", default="claude-sonnet-5-5")
    run.add_argument("--max-turns", type=int, default=40)
    run.add_argument("--max-budget-usd", type=float, default=0.5)
    args = parser.parse_args()
    return run_case(
        args.case.resolve(), args.sample, args.out.resolve(), args.run_id,
        args.model, args.max_turns, args.max_budget_usd,
    )
