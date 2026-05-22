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

Note: bare `kb status` (no KB name, no `--all`) shows **all** KBs — it does *not* fall back to the default KB. `brief`/`open`/`stage` *do* fall back to the default KB when name is omitted.

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
kb search <kb> "<query>" --max-results 10 --glob "*.md"
kb search <kb> "<query>" --exclude-inbox
```

- Default: 20 total results, up to 3 matches per file, inbox included.
- Uses `rg` when available; falls back to Python `re` over `.md` files.
- Excludes `.git/` automatically.
- `--glob` is passed through to `rg`. **Gotcha:** rg's `--glob` does *not* anchor on the search root — `--glob 'inbox/**/*.md'` will not match `inbox/2026/05/foo.md`. Use simple patterns like `*.md` or `*.json`.
- Result `title` field is taken from the file's first H1 heading, or first non-blank body line, falling back to a filename slug.

## stage

Stage one of three shapes into a KB inbox:

- **Note** — agent-written observation, semi-structured (YAML frontmatter + body).
- **Document** — any text file, copied verbatim, no frontmatter.
- **URL pointer** — a link to be fetched and summarised later by `kb-dream`.

```bash
kb stage <kb> --note "<text>"                              # note
kb stage <kb> --kind decision --note "<text>" --title T    # note with kind+title
kb stage <kb> --file <path>                                # document
kb stage <kb> --url <https://...>                          # URL pointer
kb stage <kb> --url <https://...> --note "<description>"   # URL + description
```

Mode is determined by which flag is set. `--file` is mutually exclusive with `--note` and `--url`. `--note` may accompany `--url` as an optional description body.

### Notes (`--note`)

- Agent-written observations: memory, preferences, decisions worth remembering.
- Written with YAML frontmatter (`created_at`, `kind`, optional `source`, optional `title`).
- Notes own their own headings — the CLI does not prepend one.
- Kinds: `decision`, `domain-fact`, `codebase-fact`, `runbook-note`, `retrospective`, `raw-note` (default).

### Documents (`--file`)

- Any text file, copied verbatim into `inbox/YYYY/MM/<timestamp>-<source-stem>.md`.
- **No frontmatter, no auto-heading** — the file is what it is.
- `--kind`, `--title`, `--source` are ignored for documents (they have no metadata layer).
- Manual drag-and-drop produces the same shape, so dropping a `.md` into `inbox/` is a first-class path. The next `kb-dream` pass picks it up.
- Commit message records the source filename (`kb: stage document <basename>`).

### URL pointers (`--url`)

- For "add this link / article to the KB" — the URL itself is the staged content.
- Written with frontmatter: `created_at`, `kind: url`, `url: <url>`, optional `title`, optional `source`.
- Body is empty unless `--note "<description>"` is provided.
- **No fetching at stage time.** `kb-dream` resolves and summarises during consolidation, then writes a synthesised page under `knowledge/` citing the URL.
- URL must start with `http://` or `https://`.
- Slug derives from the URL path's last segment, fallback to hostname.
- `--kind` is forced to `url`; passing it explicitly produces a soft warning.

### Common

- Writes to `inbox/YYYY/MM/` with a timestamp-prefixed filename.
- Rejects binary files; warns on files over 1 MB (`--force` to override).
- Does **not** scan content for secrets. Treat "no secrets in the KB" as agent guidance.
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
