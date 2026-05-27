# kb — Command Reference

## Global flags

```
kb --help
kb <command> --help
kb --config <path> <command>
kb --json <command>
kb --version
```

`--json` produces machine-readable JSON output where supported.

## Config and default-KB resolution

The CLI honours Claude Code plugin config (per-repo or user-scope) via the standard `pluginConfigs.kb.options` → `CLAUDE_PLUGIN_OPTION_*` env var bridge.

**Registry config path** — first set source wins:

1. `--config <path>` flag
2. `KB_REGISTRY_CONFIG` env var
3. `CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH` (set via `pluginConfigs.kb.options.registry_config_path` in `.claude/settings.json`)
4. `~/.config/kb-registry/registry.json` (default)

**Default KB** (when a command's positional/--kb is omitted):

1. The explicit positional or `--kb <name>` argument
2. `CLAUDE_PLUGIN_OPTION_DEFAULT_KB` (set via `pluginConfigs.kb.options.default_kb` in `.claude/settings.json`)
3. The registry entry marked `"default": true`

Use the project-scope `.claude/settings.json` to bind a different KB per repo without touching the global registry.

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

Note: bare `kb status` (no KB name, no `--all`) shows **all** KBs — it does *not* fall back to the default KB. `brief`/`open`/`stage`/`pending` *do* fall back to the default KB when name is omitted.

## remember

Append a short single-paragraph memory to `<kb>/notes/`.

```bash
kb remember "<text>"
kb remember "<text>" --tags emma,domain
kb remember "<text>" --kb <kb>
```

- Writes to `notes/YYYY/MM/<timestamp>-<slug>.md` with `created_at` and (optional) `tags` frontmatter.
- The text is the body, verbatim. Notes own their headings (none auto-prepended).
- Falls back to the default KB if `--kb` is not given.
- `--no-commit` to skip the auto-commit.
- Use for **project / domain / codebase facts that are expensive to re-derive but too small for a `knowledge/` page**, e.g. "EMMA's nightly job runs at 02:00 UTC via cron."
- Do **not** use for personal user preferences ("I prefer rebase", "I like X") — those belong in Claude's auto-memory. The KB is not the right layer.
- `notes/` is append-only: `kb-dream` never touches it.

## recall

Search synthesised material in indexable sections, **excluding** the raw `inbox/`.

```bash
kb recall [<kb>] --query "<text>"
kb recall [<kb>] --tag <tag>
kb recall --query "<text>" --max-results 5
```

- `--query` checks `index.json` first, then runs lexical (`rg`-backed) search across indexable sections.
- `--tag` lists pages whose frontmatter `tags:` includes the given tag.
- One of `--query` or `--tag` is required.
- Defaults: 20 total results.
- Distinct from `kb search`, which covers the whole KB including the inbox. Use `recall` for "what do we know about X" style questions; use `search` when you specifically need to grep raw material.

## pending

List unprocessed inbox material.

```bash
kb pending [<kb>]
kb pending <kb> --max-results 10
kb pending --json
```

- Walks `<kb>/inbox/`, skipping `inbox/processed/` and `README.md`.
- Reports `[<kind>] <title>` plus relative path; URL pointers also print the URL.
- Title comes from frontmatter `title`, then the file's first H1, then a filename slug.
- Sorted most-recent-first by frontmatter `created_at` (ISO sorts lexically).
- Falls back to the default KB if no name is given.

Useful as a "what was I in the middle of?" check when picking up where a previous session left off.

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
- `--kind` accepts any string and is written verbatim to frontmatter. Suggested starting points: `decision`, `domain-fact`, `codebase-fact`, `runbook-note`, `retrospective`, `followup`, `raw-note` (default when `--kind` is omitted). Invent KB-specific kinds (`hypothesis`, `open-question`, `benchmark`, ...) freely.

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

## reindex

Rebuild `<kb>/index.json` — a structured manifest of every Markdown file under auto-discovered indexable sections (excluding READMEs and dotfiles).

```bash
kb reindex [<kb>]
kb reindex [<kb>] --dry-run
kb reindex [<kb>] --no-commit
kb reindex --json
```

- Each entry: `path`, `title`, `section` (top-level directory), `tags`, `summary` (first prose paragraph, ~200 chars), `word_count`, `last_modified` (ISO, from git), optional `kind` (when frontmatter carries one).
- Indexable sections are top-level directories that contain Markdown files, excluding dot-directories, `inbox/`, `sources/`, and `tools/`.
- Written to `<kb>/index.json` at the KB root — visible, committable, agent-readable.
- Auto-commits "kb: rebuild index.json" when content changes; `--no-commit` to skip. Use `--no-commit` when rebuilding as part of a larger KB content commit.
- `--dry-run` reports entry counts and diff without writing.
- Falls back to the default KB when `<kb>` is omitted.
- `INDEX.md` is left untouched — that file stays agent-curated narrative. The two indices serve different audiences: `INDEX.md` for humans/agents reading prose, `index.json` for machine retrieval.

`kb recall` consults `index.json` first (title/tag/summary hits) before falling back to body grep. When `index.json` is absent, `kb recall` still works but prints a tip to run `kb reindex`.

Refresh is explicit: `kb remember`, `kb stage`, and `kb-dream` do not auto-rebuild. Run `kb reindex --dry-run` during a writing cluster, then rebuild the generated index after the content changes are settled.

## forget

Remove a single page from an indexable section.

```bash
kb forget [<kb>] <path>
kb forget [<kb>] <path> --reason "<text>"
kb forget [<kb>] <path> --dry-run
kb forget [<kb>] <path> --no-commit
kb forget --json [<kb>] <path>
```

- `<path>` must be relative to the KB root and live under an indexable section. Inbox/source/tool material is out of scope (use direct git operations or move inbox material into `inbox/processed/`).
- Refuses contract files (`BRIEF.md`, `AGENTS.md`, `INDEX.md`, `LOG.md`, `index.json`, `README.md`, `.gitignore`) and any path that escapes the KB root.
- Removes the file, appends a one-line entry to `LOG.md` in the form `- YYYY-MM-DD: forgot PATH — REASON`, and auto-commits `kb: forget PATH` covering both the deletion and the log update. `--no-commit` leaves the changes uncommitted.
- Falls back to the default KB when `<kb>` is omitted.

### Soft for retrieval, hard for surface

Forget removes the file from the agent's working surface — `kb recall`, `kb search`, `kb open`, `index.json` after the next reindex — but git history preserves the content. `git log --all -- <path>` recovers what was forgotten and when. This is the v0 stand-in for `kb supersede`: replacement is implicit via git history.

### What forget does NOT do

- **Auto-rebuild `index.json`.** Run `kb reindex <kb>` afterwards. (Stale-index tip is printed.)
- **Auto-edit `INDEX.md`.** If the forgotten path is referenced from the agent-curated `INDEX.md`, forget warns and leaves the link in place — edit by hand. The check is a literal Markdown-link substring scan for that relative path.

Exit codes follow the global table at the top of this file: `1` on filesystem/commit failure or missing file, `2` on bad arguments (e.g. path outside indexable sections), `3` on safety rejection (traversal, protected file).

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
