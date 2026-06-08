---
description: Register an existing knowledge base directory with the kb registry.
argument-hint: <name> --path <path> [--remote <url>] [--description "<text>"] [--default]
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/kb:*)
---

# Register an existing knowledge base

The user invoked `/kb:add` to register an existing KB directory. Their argument string:

**$ARGUMENTS**

Run the underlying CLI:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb add $ARGUMENTS
```

- The first positional argument is the KB name (required).
- `--path <path>` is the existing KB directory (required).
- `--remote <url>` records the git remote in the registry.
- `--description "<text>"` carries an optional one-liner.
- `--default` marks this KB as the registry default.

`${CLAUDE_PLUGIN_ROOT}/bin/kb add` validates the KB contract (presence of `AGENTS.md`, `BRIEF.md`, `INDEX.md`, `LOG.md`, and the seed dirs). Missing files are rejected unless the user adds `--force`. If the CLI rejects on contract grounds, list the missing items and ask whether to `--force` register anyway.

If the path is not a git repo, the CLI will warn — that's not fatal, but typical KBs are git-tracked.

After a successful add, suggest `${CLAUDE_PLUGIN_ROOT}/bin/kb status <name>` to confirm registration.
