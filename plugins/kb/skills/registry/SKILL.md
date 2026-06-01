---
name: registry
description: This skill should be used when the user asks to "register a KB", "add a KB", "remove a KB", "bootstrap a KB", "sync a KB", "check KB status", or wants to manage the lifecycle of a knowledge base (creation, registration, syncing, removal, contract checks). Not for querying KB contents — use kb:recall.
version: 0.2.0
---

# kb:registry

Lifecycle management and state inspection for KBs. Invoked when the user explicitly asks to mutate the registry, or check whether a KB is in a state where mutations are safe.

## Commands

```bash
kb bootstrap <name> [--path <path>] [--remote <url>]   # create or clone a KB
kb add <name> --path <path> [--remote <url>]           # register an existing KB
kb remove <name> [--delete-local --yes]                # remove from registry (files preserved by default)
kb sync <name> | kb sync --all                         # pull-rebase + push for the KB's remote
kb status [<kb>] | kb status --all                     # path / git / contract state
```

- `bootstrap` creates a KB from the template (`inbox/`, `knowledge/`, `notes/`, `BRIEF.md`, etc.) and registers it.
- `add` registers an existing directory; rejects KBs that don't satisfy the contract unless `--force`.
- `remove` defaults to registry-only — files preserved unless `--delete-local --yes`.
- `sync` refuses to operate on a dirty working tree; never auto-resolves conflicts.
- `status` is read-only; safe to run any time. Bare `kb status` shows all KBs.

Full flag reference and exit codes: `${CLAUDE_PLUGIN_ROOT}/references/commands.md`.
