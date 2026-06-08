---
description: Create or clone a knowledge base and register it.
argument-hint: <name> [--path <path>] [--remote <url>] [--description "<text>"] [--default]
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/kb:*)
---

# Bootstrap a knowledge base

The user invoked `/kb:bootstrap` to create a new KB. Their argument string:

**$ARGUMENTS**

Run the underlying CLI to do the work and report the result:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb bootstrap $ARGUMENTS
```

- The first positional argument is the KB name (required).
- `--path` sets a custom directory; otherwise the KB lands under `~/knowledge/<name>-kb`.
- `--remote <git-url>` clones (if target empty) or sets the remote on a fresh local KB.
- `--default` marks the new KB as the registry default.

If the user omitted required arguments (no name), report the CLI's error directly — don't guess. If `--remote` was given and the target path already exists with content, the CLI will refuse without `--force`; surface that and ask whether to retry.

After a successful bootstrap, suggest the next typical step: `${CLAUDE_PLUGIN_ROOT}/bin/kb stage <name> --note "..."` to start staging material, or `${CLAUDE_PLUGIN_ROOT}/bin/kb stage <name> --dir <path>` to bulk-ingest an existing source tree.
