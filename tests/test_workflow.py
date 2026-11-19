"""Guards on the properties the pipeline's trust model rests on (ADR 0001, ADR 0003).
A careless edit must not break them quietly."""

from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
WORKFLOW = yaml.safe_load((ROOT / ".github" / "workflows" / "evaluate.yml").read_text())
JOBS = WORKFLOW["jobs"]

CLAUDE_CREDENTIALS = ("ANTHROPIC_API_KEY", "claude-code-action")
AWS_CREDENTIALS = ("AWS_", "aws-actions", "role-to-assume")


def _steps(job):
    return JOBS[job]["steps"]


def _uses(job, prefix):
    return [s for s in _steps(job) if s.get("uses", "").startswith(prefix)]


def _mentions(job, needles):
    text = yaml.safe_dump(JOBS[job])
    return any(n in text for n in needles)


def test_the_job_that_runs_the_agent_has_no_token_and_never_checks_out_the_repo():
    assert JOBS["generate"]["permissions"] == {}
    assert not _uses("generate", "actions/checkout")


def test_the_agent_job_takes_its_key_from_the_claude_environment():
    assert JOBS["generate"]["environment"] == "claude"


def test_only_the_agent_job_can_see_claude_credentials():
    for name in JOBS:
        assert _mentions(name, CLAUDE_CREDENTIALS) == (name == "generate"), name


def test_no_job_holds_both_claude_and_aws_credentials():
    for name in JOBS:
        assert not (_mentions(name, CLAUDE_CREDENTIALS) and _mentions(name, AWS_CREDENTIALS)), name


def test_the_agent_job_receives_the_prompt_and_nothing_else():
    downloads = _uses("generate", "actions/download-artifact")
    assert [d["with"]["name"] for d in downloads] == ["prompt"]


def test_jobs_with_a_checkout_download_artifacts_only_into_outputs():
    for name in JOBS:
        if _uses(name, "actions/checkout"):
            for download in _uses(name, "actions/download-artifact"):
                assert download["with"]["path"].split("/")[0] == "outputs", f"{name} could overwrite the checkout"


def test_the_action_is_pinned_to_a_commit_and_given_the_jobs_zero_permission_token():
    action = _uses("generate", "anthropics/claude-code-action")[0]
    assert len(action["uses"].split("@")[1].split()[0]) == 40  # a full commit SHA, not a moving tag
    assert action["with"]["github_token"] == "${{ github.token }}"  # otherwise it mints an app token that can read the repo


def test_the_kiln_commit_in_the_workflow_matches_the_lockfile():
    assert WORKFLOW["env"]["KILN_COMMIT"] in (ROOT / "uv.lock").read_text()
