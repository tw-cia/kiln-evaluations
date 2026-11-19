"""Tell Research (looking outside kiln's own docs) apart from network use the tooling needs anyway."""

import json
import re
import shlex
from pathlib import Path

_URL = re.compile(r"https?://[^\s\"'<>)]+")
_OPERATORS = {"&&", "||", ";", "|", "&", "\n"}

# Commands whose whole job is to reach outside kiln's documentation.
_OUTSIDE = {"curl", "wget", "gh", "npx"}
_INTERPRETERS = {"python", "python3", "node", "ruby", "perl"}
_INSTALLS = {("pip", "install"), ("pip3", "install"), ("uv", "add"), ("npm", "install"), ("npm", "i")}

# Network use the tooling needs anyway (pulling CRDs, rendering through Docker...). Reported, not penalised.
_TOOLING_ALWAYS = {"docker", "crossplane"}
_TOOLING_SUBCOMMANDS = {("kiln", "pull-crds"), ("kiln", "render"), ("kiln", "render-all"), ("kcl", "mod")}


def tool_uses(transcript: Path):
    """Yield (tool name, input) for every tool call the agent made."""
    for line in transcript.read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "assistant":
            continue
        for block in event.get("message", {}).get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use":
                yield block["name"], block.get("input", {})


def _segments(command: str) -> list[list[str]]:
    """Split a shell line into commands, on operators outside quotes."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""  # '#' is part of a URL fragment here, not a comment
    segments, current = [], []
    try:
        for token in lexer:
            if token in _OPERATORS:
                segments.append(current)
                current = []
            else:
                current.append(token)
    except ValueError:  # unbalanced quotes: fall back to treating the whole line as one command
        return [command.split()]
    segments.append(current)
    return [segment for segment in segments if segment]


def _classify(segment: list[str]) -> str | None:
    """'research', 'tooling', or None for a harmless command."""
    words = segment
    while words and words[0] in {"sudo", "env", "time"}:
        words = words[1:]
    if not words:
        return None
    first = words[0]
    second = words[1] if len(words) > 1 else ""
    if first == "uvx" and "kiln" in words:
        return "tooling"
    if first in _TOOLING_ALWAYS or (first, second) in _TOOLING_SUBCOMMANDS:
        return "tooling"
    if first in _OUTSIDE or (first, second) in _INSTALLS or (first, second) == ("uv", "pip") and "install" in words:
        return "research"
    if first == "git" and "clone" in words:
        return "research"
    if first in _INTERPRETERS and _URL.search(" ".join(words)):
        return "research"
    return None


def _account_shell(command: str, research: dict, tooling_network: dict) -> None:
    for segment in _segments(command):
        kind = _classify(segment)
        text = " ".join(segment)
        if kind == "research":
            research["count"] += 1
            research["urls"].extend(_URL.findall(text))
            research["commands"].append(command)
        elif kind == "tooling":
            tooling_network["count"] += 1
            tooling_network["commands"].append(command)


def account(transcript: Path) -> tuple[dict, dict]:
    research = {"count": 0, "queries": [], "urls": [], "commands": []}
    tooling_network = {"count": 0, "commands": []}
    for name, tool_input in tool_uses(transcript):
        if name == "WebSearch":
            research["count"] += 1
            research["queries"].append(tool_input.get("query", ""))
        elif name == "WebFetch":
            research["count"] += 1
            research["urls"].append(tool_input.get("url", ""))
        elif name == "Bash":
            _account_shell(tool_input.get("command", ""), research, tooling_network)
    return research, tooling_network
