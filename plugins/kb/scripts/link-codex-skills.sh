#!/usr/bin/env bash
# Expose the kb plugin's skills to OpenAI Codex.
#
# Codex discovers skills as self-contained folders under $CODEX_HOME/skills/<name>/
# and resolves their paths relative to the skill dir or absolute. It has no
# ${CLAUDE_PLUGIN_ROOT} — the variable Claude Code sets at runtime and that the kb
# skills use to reach bin/kb and references/. So exposing kb to Codex takes two steps:
#
#   1. Symlink each skill into the Codex skills dir as kb-<skill>.
#   2. Export CLAUDE_PLUGIN_ROOT to Codex's shell subprocesses (via config.toml
#      [shell_environment_policy.set]) so the existing ${CLAUDE_PLUGIN_ROOT}/bin/kb
#      and ${CLAUDE_PLUGIN_ROOT}/references/* paths resolve unchanged.
#
# This script does (1) idempotently and prints the snippet for (2) if it is missing.
# Safe to re-run after `git pull`. The symlinks point at this live plugin tree, so
# Codex always sees the current source (unlike Claude Code, which serves kb from its
# versioned plugin cache).
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DIR="$CODEX_HOME/skills"
CONFIG="$CODEX_HOME/config.toml"
PREFIX="kb-"
SKILLS=(info recall registry remember stage retrospective)

if [ ! -d "$CODEX_HOME" ]; then
  echo "error: Codex home not found at $CODEX_HOME (install Codex or set CODEX_HOME)" >&2
  exit 1
fi
mkdir -p "$SKILLS_DIR"

for s in "${SKILLS[@]}"; do
  src="$PLUGIN_ROOT/skills/$s"
  dst="$SKILLS_DIR/$PREFIX$s"
  if [ ! -d "$src" ]; then
    echo "warning: skill source missing, skipping: $src" >&2
    continue
  fi
  ln -sfn "$src" "$dst"
  echo "linked $dst -> $src"
done

echo
if grep -q 'CLAUDE_PLUGIN_ROOT' "$CONFIG" 2>/dev/null; then
  echo "config.toml already references CLAUDE_PLUGIN_ROOT — leaving it untouched."
  echo "(verify it points at: $PLUGIN_ROOT)"
else
  cat <<EOF
ACTION REQUIRED — add this to $CONFIG so Codex resolves \${CLAUDE_PLUGIN_ROOT}:

[shell_environment_policy.set]
CLAUDE_PLUGIN_ROOT = "$PLUGIN_ROOT"

(If you already have a [shell_environment_policy.set] table, add only the
CLAUDE_PLUGIN_ROOT line under it.)
EOF
fi

echo
echo "Done. Restart Codex to pick up the linked skills."
