---
description: Pull and push the git repos backing one or all knowledge bases.
argument-hint: [<kb>] [--all]
allowed-tools: ["Bash"]
---

# Sync KBs with their git remotes

The user invoked `/kb:sync` to synchronise KB repos. Their argument string:

**$ARGUMENTS**

Run the underlying CLI:

```bash
kb sync $ARGUMENTS
```

- Positional `<kb>`: sync a single KB. Falls back to the default KB if omitted.
- `--all`: sync every registered KB.

`kb sync` pulls with rebase, then pushes local commits. It **refuses** on a dirty working tree (commit or stash first) and on rebase conflicts (resolve manually, do not auto-resolve). KBs with no remote configured are reported as `local-only` and skipped successfully.

If the CLI exits non-zero with a conflict, do not attempt to auto-resolve. Report which KB is conflicted, suggest the user resolve in the KB repo directly, and stop.

After a clean sync, mention whether any KBs were local-only so the user knows which ones don't yet have a remote.
