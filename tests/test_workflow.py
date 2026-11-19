"""Guards on the properties the pipeline's trust model rests on (ADR 0001, ADR 0003).
A careless edit must not break them quietly."""

from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
EVALUATE = yaml.safe_load((WORKFLOWS / "evaluate.yml").read_text())
SANDBOX = yaml.safe_load((WORKFLOWS / "claude-sandbox.yml").read_text())
SANDBOX_USE = "./.github/workflows/claude-sandbox.yml"

# every job in every workflow, by (file, job)
ALL_JOBS = {
    **{("evaluate", name): job for name, job in EVALUATE["jobs"].items()},
    **{("claude-sandbox", name): job for name, job in SANDBOX["jobs"].items()},
}
THE_CLAUDE_JOB = ("claude-sandbox", "sandbox")

CLAUDE_CREDENTIALS = ("ANTHROPIC_API_KEY", "claude-code-action")
AWS_CREDENTIALS = ("AWS_", "aws-actions", "role-to-assume")


def _steps(job):
    return job.get("steps", [])


def _uses(job, prefix):
    return [s for s in _steps(job) if s.get("uses", "").startswith(prefix)]


def _mentions(job, needles):
    text = yaml.safe_dump(job)
    return any(n in text for n in needles)


def test_the_claude_job_has_no_token_and_never_checks_out_the_repo():
    job = SANDBOX["jobs"]["sandbox"]
    assert job["permissions"] == {}
    assert not _uses(job, "actions/checkout")


def test_the_claude_job_takes_its_key_from_the_claude_environment():
    assert SANDBOX["jobs"]["sandbox"]["environment"] == "claude"


def test_the_claude_job_receives_the_prompt_and_nothing_else():
    downloads = _uses(SANDBOX["jobs"]["sandbox"], "actions/download-artifact")
    assert [d["with"]["name"] for d in downloads] == ["${{ inputs.prompt-artifact }}"]


def test_only_the_claude_job_can_see_claude_credentials():
    for key, job in ALL_JOBS.items():
        assert _mentions(job, CLAUDE_CREDENTIALS) == (key == THE_CLAUDE_JOB), key


def test_no_job_holds_both_claude_and_aws_credentials():
    for key, job in ALL_JOBS.items():
        assert not (_mentions(job, CLAUDE_CREDENTIALS) and _mentions(job, AWS_CREDENTIALS)), key


def test_every_call_to_the_claude_sandbox_is_made_with_no_token():
    calls = [job for job in EVALUATE["jobs"].values() if job.get("uses") == SANDBOX_USE]
    assert calls, "the sandbox is not used"
    for job in calls:
        assert job["permissions"] == {}


def test_jobs_with_a_checkout_download_artifacts_only_into_outputs():
    for key, job in ALL_JOBS.items():
        if _uses(job, "actions/checkout"):
            for download in _uses(job, "actions/download-artifact"):
                assert download["with"]["path"].split("/")[0] == "outputs", f"{key} could overwrite the checkout"


def test_the_action_is_pinned_to_a_commit_and_given_the_jobs_zero_permission_token():
    action = _uses(SANDBOX["jobs"]["sandbox"], "anthropics/claude-code-action")[0]
    assert len(action["uses"].split("@")[1].split()[0]) == 40  # a full commit SHA, not a moving tag
    assert action["with"]["github_token"] == "${{ github.token }}"  # otherwise it mints an app token that can read the repo


def test_the_kiln_commit_in_the_sandbox_matches_the_lockfile():
    assert SANDBOX["env"]["KILN_COMMIT"] in (ROOT / "uv.lock").read_text()


def test_the_tool_versions_are_the_same_in_both_workflows():
    for pin in ("KCL_VERSION", "CROSSPLANE_VERSION"):
        assert EVALUATE["env"][pin] == SANDBOX["env"][pin], pin
