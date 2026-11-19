#!/usr/bin/env bash
# Install the pinned tooling kiln and the evals need. Used by every job so versions stay in step.
# Bump deliberately: results are only comparable across runs when these are unchanged.
set -euo pipefail

KCL_VERSION="${KCL_VERSION:-v0.13.3}"
CROSSPLANE_VERSION="${CROSSPLANE_VERSION:-v2.4.3}"
CLAUDE_CODE_VERSION="${CLAUDE_CODE_VERSION:-2.1.328}"
WITH_CLAUDE="${WITH_CLAUDE:-0}"   # only the generate job needs the agent CLI

BIN="${HOME}/.local/bin"
mkdir -p "$BIN"

curl -fsSL "https://github.com/kcl-lang/cli/releases/download/${KCL_VERSION}/kcl-${KCL_VERSION}-linux-amd64.tar.gz" \
  | tar -xz -C "$BIN" kcl

curl -fsSL -o "$BIN/crossplane" \
  "https://releases.crossplane.io/stable/${CROSSPLANE_VERSION}/bin/linux_amd64/crossplane"
chmod +x "$BIN/crossplane"

if [ "$WITH_CLAUDE" = "1" ]; then
  npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}"
fi

echo "$BIN" >> "${GITHUB_PATH:-/dev/null}"
"$BIN/kcl" --version
"$BIN/crossplane" --version
