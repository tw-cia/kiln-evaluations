"""Guards on the properties the blindness design (ADR 0001) rests on. A careless edit must not break them quietly."""

from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
WORKFLOW = yaml.safe_load((ROOT / ".github" / "workflows" / "evaluate.yml").read_text())
JOBS = WORKFLOW["jobs"]


def _action(job):
    return next(s for s in JOBS[job]["steps"] if s.get("uses", "").startswith("anthropics/claude-code-action"))


def test_the_generate_job_has_no_token_and_never_checks_out_the_repo():
    assert JOBS["generate"]["permissions"] == {}
    assert not any(s.get("uses", "").startswith("actions/checkout") for s in JOBS["generate"]["steps"])


def test_only_the_generate_job_can_see_the_api_key():
    for name, job in JOBS.items():
        has_key = "ANTHROPIC_API_KEY" in yaml.safe_dump(job)
        assert has_key == (name == "generate"), f"{name} {'has' if has_key else 'lacks'} the API key"


def test_the_action_is_pinned_to_a_commit_and_given_the_jobs_zero_permission_token():
    action = _action("generate")
    assert len(action["uses"].split("@")[1].split()[0]) == 40  # a full commit SHA, not a moving tag
    assert action["with"]["github_token"] == "${{ github.token }}"  # otherwise it mints an app token that can read the repo


def test_the_prompt_in_the_workflow_is_the_cases_prompt():
    assert _action("generate")["with"]["prompt"].strip() == (ROOT / "cases" / "storage-bucket" / "prompt.md").read_text().strip()


def test_the_kiln_commit_in_the_workflow_matches_the_lockfile():
    assert WORKFLOW["env"]["KILN_COMMIT"] in (ROOT / "uv.lock").read_text()
