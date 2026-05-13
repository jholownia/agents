# KB Registry — Command Reference

## Global flags

```
kb --help
kb <command> --help
kb --config <path> <command>
kb --json <command>
kb --version
```

`--json` produces machine-readable JSON output where supported.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Operational failure |
| 2 | Invalid arguments or config |
| 3 | Safety rejection |
| 4 | Git conflict or dirty-state blocker |

---

## bootstrap

Create or clone a KB and register it.

```bash
kb bootstrap <name> --path <path>
kb bootstrap <name> --path <path> --remote <url>
kb bootstrap <name> --remote <url>
```

- If `--remote` is provided and path does not exist or is empty, clones the remote.
- Otherwise creates a local KB from template and runs `git init`.
- First KB bootstrapped is automatically set as default.
- `--force` allows non-empty directories.

## add

Register an existing KB directory.

```bash
kb add <name> --path <path> [--remote <url>] [--description <text>] [--default]
```

- Validates the path exists and checks KB contract.
- Rejects missing contract files by default. Use `--force` to register anyway.
- Warns if not a git repo.

## remove

Remove a KB from the registry.

```bash
kb remove <name>
kb remove <name> --delete-local --yes
```

- Default: removes registry entry only, no file deletion.
- `--delete-local --yes` deletes the KB directory. Refuses if dirty unless `--force`.

## list

List all configured KBs.

```bash
kb list
kb list --json
```

## status

Show registry and git status.

```bash
kb status [<kb>]
kb status --all
```

Shows: path existence, git status, branch, clean/dirty, remote URL, missing contract files.

## brief

Print the compact KB summary (BRIEF.md).

```bash
kb brief <kb>
kb brief <kb> --max-chars 5000
```

Default max: 12,000 characters.

## open

Read a specific KB file by relative path.

```bash
kb open <kb> <path>
kb open <kb> <path> --max-chars 10000
```

- Rejects absolute paths and path traversal.
- Default max: 20,000 characters.
- Prints content to stdout (does not open an editor).

## search

Lexical search using `rg` (with Python fallback).

```bash
kb search <kb> "<query>"
kb search "<query>"              # search all KBs
kb search --all "<query>"
kb search <kb> "<query>" --max-results 10 --glob "*.md"
kb search <kb> "<query>" --exclude-inbox
```

- Default: 20 results max, inbox included.
- Uses `rg` when available; falls back to Python `re` over `.md` files.
- Excludes `.git/` automatically.

## stage

Stage a note or file into a KB inbox.

```bash
kb stage <kb> --note "<text>"
kb stage <kb> --file <path>
kb stage <kb> --kind decision --note "<text>" --title "Short title"
```

Kinds: `decision`, `domain-fact`, `codebase-fact`, `runbook-note`, `retrospective`, `raw-note` (default).

- Writes to `inbox/YYYY/MM/` with timestamp filename.
- Adds frontmatter metadata.
- Runs secret scanning before writing (exit 3 if detected, `--force` to override).
- Auto-commits by default (`--no-commit` to skip).

## sync

Synchronize KB git repos with their remotes.

```bash
kb sync <kb>
kb sync --all
```

- Pulls with rebase, then pushes local commits.
- Stops on dirty working tree.
- Stops on conflicts — does not auto-resolve.
- Reports local-only KBs (no remote) and exits successfully.
