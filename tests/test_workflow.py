"""Guards on the properties the blindness design (ADR 0001) rests on. A careless edit must not break them quietly."""

from pathlib import Path

import yaml

WORKFLOW = yaml.safe_load((Path(__file__).parent.parent / ".github" / "workflows" / "evaluate.yml").read_text())
JOBS = WORKFLOW["jobs"]


def _uses(job):
    return [step.get("uses", "") for step in JOBS[job]["steps"]]


def test_the_generate_job_has_no_token_and_never_checks_out_the_repo():
    assert JOBS["generate"]["permissions"] == {}
    assert not any(u.startswith("actions/checkout") for u in _uses("generate"))


def test_the_generate_job_only_receives_its_own_cases_prompt():
    download = next(s for s in JOBS["generate"]["steps"] if s.get("uses", "").startswith("actions/download-artifact"))
    assert download["with"]["name"] == "prompt-${{ matrix.case }}"


def test_only_the_generate_job_can_see_the_api_key():
    for name, job in JOBS.items():
        has_key = "ANTHROPIC_API_KEY" in yaml.safe_dump(job)
        assert has_key == (name == "generate"), f"{name} {'has' if has_key else 'lacks'} the API key"


def test_the_job_that_runs_the_hidden_checks_is_the_only_one_that_downloads_outputs():
    downloads_outputs = [
        name for name, job in JOBS.items()
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/download-artifact") and "output" in str(step.get("with", {}))
    ]
    assert downloads_outputs == ["static"]


def test_the_action_is_pinned_to_a_commit_and_given_the_jobs_zero_permission_token():
    action = next(s for s in JOBS["generate"]["steps"] if s.get("uses", "").startswith("anthropics/claude-code-action"))
    assert len(action["uses"].split("@")[1].split()[0]) == 40  # a full commit SHA, not a moving tag
    assert action["with"]["github_token"] == "${{ github.token }}"  # otherwise it mints an app token that can read the repo


def test_the_kiln_commit_in_the_workflow_matches_the_lockfile():
    lock = (Path(__file__).parent.parent / "uv.lock").read_text()
    assert WORKFLOW["env"]["KILN_COMMIT"] in lock
