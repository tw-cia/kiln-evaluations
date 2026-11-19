"""A scripted stand-in for the `claude` CLI, installed on PATH by the tests.

Behaviour comes from the JSON file named by FAKE_CLAUDE_SCENARIO. It emits stream-json events in the
shape Claude Code documents, so the runner talks to it exactly as it would to the real thing.
"""

import json
import os
import sys
from pathlib import Path

DEFAULT_RESULT = {
    "type": "result",
    "subtype": "success",
    "is_error": False,
    "num_turns": 3,
    "duration_ms": 1234,
    "total_cost_usd": 0.12,
    "usage": {
        "input_tokens": 1000,
        "output_tokens": 200,
        "cache_read_input_tokens": 300,
        "cache_creation_input_tokens": 400,
    },
}


def emit(event):
    print(json.dumps(event), flush=True)


def main():
    scenario = json.loads(Path(os.environ["FAKE_CLAUDE_SCENARIO"]).read_text())
    args = sys.argv[1:]
    if "--version" in args:
        print(scenario.get("version", "9.9.9 (Claude Code)"))
        return 0

    prompt = args[args.index("-p") + 1]
    emit({"type": "system", "subtype": "init"})
    emit({"type": "assistant", "message": {"content": [{"type": "text", "text": prompt}]}})
    for name in scenario.get("echo_env", []):
        emit({"type": "assistant", "message": {"content": [{"type": "text", "text": os.environ.get(name, "")}]}})
    for path, env_name in scenario.get("write_env_to", {}).items():
        Path(path).write_text(os.environ.get(env_name, ""))
    for path, content in scenario.get("write_files", {}).items():
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    if scenario.get("result", True):
        emit({**DEFAULT_RESULT, **scenario.get("result_overrides", {})})
    return scenario.get("exit_code", 0)


sys.exit(main())
