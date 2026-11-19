def test_run_produces_a_kiln_project_with_the_samples_own_api_group(run_case):
    result = run_case(sample=2, run_id="t1")

    assert result.proc.returncode == 0, result.proc.stderr
    assert 'group = "st1-2.eval.example.com"' in (result.project / "kiln.toml").read_text()


def test_the_agent_receives_the_prompt_and_works_inside_the_project(run_case):
    result = run_case({"write_files": {"kcl-scripts/demo.k": "schema Demo:\n    name: str\n"}})

    assert "schema Demo" in (result.project / "kcl-scripts" / "demo.k").read_text()
    assert "create a composite kind called Demo" in result.transcript.read_text()


def test_a_normal_finish_is_completed_with_tokens_and_cost_recorded(run_case):
    manifest = run_case().manifest

    assert manifest["case"] == "demo"
    assert manifest["sample"] == 1
    assert manifest["outcome"] == "completed"
    assert manifest["num_turns"] == 3
    assert manifest["cost_usd"] == 0.12
    assert manifest["tokens"] == {"input": 1000, "output": 200, "cache_read": 300, "cache_creation": 400}


import pytest


@pytest.mark.parametrize("subtype", ["error_max_turns", "error_max_budget_usd"])
def test_hitting_a_turn_or_budget_cap_is_exhausted_not_an_error(run_case, subtype):
    result = run_case({"result_overrides": {"subtype": subtype, "is_error": True}})

    assert result.proc.returncode == 0, result.proc.stderr
    assert result.manifest["outcome"] == "exhausted"


def test_a_crash_with_no_result_is_an_infra_error(run_case):
    result = run_case({"result": False, "exit_code": 1})

    assert result.proc.returncode == 0, result.proc.stderr
    assert result.manifest["outcome"] == "infra_error"


def test_claude_missing_entirely_is_an_infra_error(run_case):
    import sys
    from pathlib import Path

    # kiln is on PATH (the venv's bin), claude is not
    result = run_case(env={"PATH": str(Path(sys.executable).parent)})

    assert result.proc.returncode == 0, result.proc.stderr
    assert result.manifest["outcome"] == "infra_error"


SECRET = "sk-ant-api03-this-is-a-test-secret-value"


def test_the_api_key_never_appears_in_the_transcript(run_case):
    result = run_case({"echo_env": ["ANTHROPIC_API_KEY"]}, env={"ANTHROPIC_API_KEY": SECRET})

    transcript = result.transcript.read_text()
    assert SECRET not in transcript
    assert "create a composite kind called Demo" in transcript  # the rest is untouched


def test_the_api_key_never_appears_in_files_the_agent_wrote(run_case):
    result = run_case({"write_env_to": {"leak.txt": "ANTHROPIC_API_KEY"}}, env={"ANTHROPIC_API_KEY": SECRET})

    assert SECRET not in (result.project / "leak.txt").read_text()


def test_the_manifest_records_versions_and_settings(run_case):
    import re
    from pathlib import Path

    lock = (Path(__file__).parent.parent / "uv.lock").read_text()
    locked_kiln_commit = re.search(r'name = "kiln"\nversion = "[^"]+"\nsource = \{ git = "[^"]*#([0-9a-f]{40})"', lock).group(1)

    manifest = run_case({"version": "7.1.2 (Claude Code)"}, args=["--model", "claude-test-model"]).manifest

    assert manifest["claude_version"] == "7.1.2 (Claude Code)"
    assert manifest["kiln_commit"] == locked_kiln_commit
    assert manifest["model"] == "claude-test-model"
    assert manifest["max_turns"] == 40
    assert manifest["max_budget_usd"] == 0.5


def _tree(root):
    """Every path under root mapped to its content (or symlink target), for exact comparison."""
    import os

    entries = {}
    for path in sorted(root.rglob("*")):
        rel = str(path.relative_to(root))
        if path.is_symlink():
            entries[rel] = ("link", os.readlink(path))
        elif path.is_file():
            entries[rel] = ("file", path.read_bytes())
    return entries


def test_the_agent_starts_in_an_untouched_kiln_init_project(run_case, tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    reference = tmp_path / "reference"
    kiln = Path(sys.executable).parent / "kiln"
    subprocess.run([kiln, "init", str(reference), "--group", "st1-1.eval.example.com"], check=True, capture_output=True)

    result = run_case(run_id="t1", sample=1)  # the fake agent changes nothing

    assert _tree(reference), "reference project is empty, comparison would be vacuous"
    assert _tree(result.project) == _tree(reference)


def test_the_runner_itself_does_not_judge_research_so_the_agent_cannot_learn_the_rules(run_case):
    manifest = run_case({"tool_uses": [{"name": "WebSearch", "input": {"query": "x"}}]}).manifest

    assert "research" not in manifest
    assert "tooling_network" not in manifest
