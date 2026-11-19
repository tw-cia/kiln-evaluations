"""Research is looking outside kiln's own docs and skills; tooling_network is network use the tooling needs anyway."""

import pytest


def _bash(command):
    return {"name": "Bash", "input": {"command": command}}


def test_an_agent_that_only_used_kiln_and_its_own_files_did_no_research(run_case):
    manifest = run_case({"tool_uses": [
        {"name": "Read", "input": {"file_path": "AGENTS.md"}},
        _bash("kiln docs composing"),
        _bash("cd kcl-scripts && kcl test ."),
        _bash("kiln generate-all"),
    ]}).manifest

    assert manifest["research"]["count"] == 0
    assert manifest["tooling_network"]["count"] == 0


def test_web_searches_and_fetches_are_research_with_their_queries_and_urls(run_case):
    manifest = run_case({"tool_uses": [
        {"name": "WebSearch", "input": {"query": "crossplane bucket versioning"}},
        {"name": "WebFetch", "input": {"url": "https://docs.crossplane.io/latest/", "prompt": "read"}},
    ]}).manifest

    assert manifest["research"]["count"] == 2
    assert manifest["research"]["queries"] == ["crossplane bucket versioning"]
    assert manifest["research"]["urls"] == ["https://docs.crossplane.io/latest/"]


@pytest.mark.parametrize("command, urls", [
    ("curl -s https://example.com/a.json", ["https://example.com/a.json"]),
    ("wget https://example.com/x.tgz", ["https://example.com/x.tgz"]),
    ("git clone https://github.com/crossplane/crossplane", ["https://github.com/crossplane/crossplane"]),
    ("gh repo view crossplane/crossplane", []),
    ("pip install requests", []),
    ("pip3 install requests", []),
    ("uv pip install requests", []),
    ("uv add requests", []),
    ("npm install left-pad", []),
    ("npx left-pad", []),
    ("cd /tmp && curl https://a.example/x", ["https://a.example/x"]),
    ("cat spec.json | curl -d @- https://b.example/post", ["https://b.example/post"]),
    ("python3 -c \"import urllib.request; urllib.request.urlopen('https://c.example/y')\"", ["https://c.example/y"]),
])
def test_shell_commands_that_reach_outside_are_research(run_case, command, urls):
    manifest = run_case({"tool_uses": [_bash(command)]}).manifest

    assert manifest["research"]["count"] == 1
    assert manifest["research"]["commands"] == [command]
    assert manifest["research"]["urls"] == urls
    assert manifest["tooling_network"]["count"] == 0


def test_two_outside_commands_in_one_line_are_two_research_events(run_case):
    manifest = run_case({"tool_uses": [_bash("curl https://a.example; wget https://b.example")]}).manifest

    assert manifest["research"]["count"] == 2
    assert manifest["research"]["urls"] == ["https://a.example", "https://b.example"]


@pytest.mark.parametrize("command", [
    "kiln pull-crds",
    "kiln render StorageBucket",
    "kiln render-all",
    "docker pull alpine:3.20",
    "crossplane render xr.yaml composition.yaml functions.yaml",
    "kcl mod add k8s",
    "uvx --from git+https://github.com/leprechaun/kiln#subdirectory=tooling kiln generate-all",
])
def test_network_use_by_the_tooling_is_not_research(run_case, command):
    manifest = run_case({"tool_uses": [_bash(command)]}).manifest

    assert manifest["tooling_network"]["count"] == 1
    assert manifest["tooling_network"]["commands"] == [command]
    assert manifest["research"]["count"] == 0


@pytest.mark.parametrize("command", [
    "git status",
    "ls -la kcl-scripts",
    "echo 'see https://docs.crossplane.io for details' > NOTES.md",
])
def test_harmless_commands_and_urls_that_are_only_written_down_are_not_research(run_case, command):
    manifest = run_case({"tool_uses": [_bash(command)]}).manifest

    assert manifest["research"]["count"] == 0
    assert manifest["tooling_network"]["count"] == 0


def test_a_command_with_unbalanced_quotes_does_not_break_the_run(run_case):
    result = run_case({"tool_uses": [_bash('echo "unterminated')]})

    assert result.proc.returncode == 0, result.proc.stderr
    assert result.manifest["outcome"] == "completed"
