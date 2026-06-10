---
description: Show registration, git state, and contract status for one or all KBs.
argument-hint: "[<kb>] [--all]"
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/kb:*)
---

# KB status

The user invoked `/kb:status` to inspect KB state. Their argument string:

**$ARGUMENTS**

Run the underlying CLI:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb status $ARGUMENTS
```

- No argument and no `--all`: shows status for **all** registered KBs (this command does NOT fall back to the default KB — that's `${CLAUDE_PLUGIN_ROOT}/bin/kb status`'s deliberate behaviour).
- Positional `<kb>`: status for a single KB.
- `--all`: explicit form for everyone (same as bare `${CLAUDE_PLUGIN_ROOT}/bin/kb status`).

Status reports: path existence, git status (branch, clean/dirty), remote URL, and missing contract items. Surface the output verbatim; the user is the audience.

If the registry is empty, the CLI prints a hint to run `/kb:bootstrap` or `/kb:add`.
