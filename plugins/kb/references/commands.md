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

The CLI honours Claude Code plugin config (per-repo or user-scope) set under `pluginConfigs.kb.options` in `.claude/settings.json`. Claude Code exports those values as `CLAUDE_PLUGIN_OPTION_*` env vars, but **only into plugin-managed subprocesses** (hooks, MCP/LSP servers, monitors) — not into the generic Bash-tool subprocess the kb skills use to run this CLI. So when the env var is absent, the CLI reads the `.claude/settings.json` cascade itself (the same files Claude Code would merge). The env var still wins when present.

**Registry config path** — first set source wins:

1. `--config <path>` flag
2. `KB_REGISTRY_CONFIG` env var
3. `CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH` (set via `pluginConfigs.kb.options.registry_config_path`)
4. `registry_config_path` read directly from the `.claude/settings.json` cascade (env-var fallback)
5. `~/.config/kb-registry/registry.json` (default)

**Default KB** (when a command's positional/--kb is omitted):

1. The explicit positional or `--kb <name>` argument
2. `CLAUDE_PLUGIN_OPTION_DEFAULT_KB` (set via `pluginConfigs.kb.options.default_kb`)
3. `default_kb` read directly from the `.claude/settings.json` cascade — nearest project `settings.local.json` > project `settings.json` > user `~/.claude/settings.json` (env-var fallback)
4. The registry entry marked `"default": true`

Use the project-scope `.claude/settings.json` to bind a different KB per repo without touching the global registry. The cascade fallback (step 3) is what makes this work for the skill-invoked CLI, where the env var is never exported.

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
${CLAUDE_PLUGIN_ROOT}/bin/kb bootstrap <name> --path <path>
${CLAUDE_PLUGIN_ROOT}/bin/kb bootstrap <name> --path <path> --remote <url>
${CLAUDE_PLUGIN_ROOT}/bin/kb bootstrap <name> --remote <url>
```

- If `--remote` is provided and path does not exist or is empty, clones the remote.
- Otherwise creates a local KB from template and runs `git init`.
- First KB bootstrapped is automatically set as default.
- `--force` allows non-empty directories.

## add

Register an existing KB directory.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb add <name> --path <path> [--remote <url>] [--description <text>] [--default]
```

- Validates the path exists and checks KB contract.
- Rejects missing contract files by default. Use `--force` to register anyway.
- Warns if not a git repo.

## remove

Remove a KB from the registry.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb remove <name>
${CLAUDE_PLUGIN_ROOT}/bin/kb remove <name> --delete-local --yes
```

- Default: removes registry entry only, no file deletion.
- `--delete-local --yes` deletes the KB directory. Refuses if dirty unless `--force`.

## list

List all configured KBs.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb list
${CLAUDE_PLUGIN_ROOT}/bin/kb list --json
```

## status

Show registry and git status.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb status [<kb>]
${CLAUDE_PLUGIN_ROOT}/bin/kb status --all
```

Shows: path existence, git status, branch, clean/dirty, remote URL, missing contract files.

Note: bare `${CLAUDE_PLUGIN_ROOT}/bin/kb status` (no KB name, no `--all`) shows **all** KBs — it does *not* fall back to the default KB. `brief`/`open`/`stage`/`pending` *do* fall back to the default KB when name is omitted.

## remember

Append a short single-paragraph memory to `<kb>/notes/`.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb remember "<text>"
${CLAUDE_PLUGIN_ROOT}/bin/kb remember "<text>" --tags emma,domain
${CLAUDE_PLUGIN_ROOT}/bin/kb remember "<text>" --kb <kb>
```

- Writes to `notes/YYYY/MM/<timestamp>-<slug>.md` with `created_at` and (optional) `tags` frontmatter.
- The text is the body, verbatim. Notes own their headings (none auto-prepended).
- Falls back to the default KB if `--kb` is not given.
- `--no-commit` to skip the auto-commit.
- Use for **durable facts that are expensive to re-derive but too small for a canonical page** — project, domain, codebase, or personal-life. Examples: "EMMA's nightly job runs at 02:00 UTC via cron"; "My birthday is 15 November".
- Routes by the target KB's stated purpose. Project KBs hold project/domain/codebase facts; a personal `user-kb` (if registered) holds personal-life facts.
- Do **not** use for user preferences about agent behaviour ("address me as X", "I prefer rebase") or short-lived project state — those belong in Claude's auto-memory.
- Explicit user invocation (`/remember`, `${CLAUDE_PLUGIN_ROOT}/bin/kb remember ...`) overrides the heuristic: honour the routing the user chose.
- `notes/` is append-only: `kb-dream` never touches it.

## recall

Search synthesised material in indexable sections, **excluding** the raw `inbox/`.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb recall [<kb>] --query "<text>"
${CLAUDE_PLUGIN_ROOT}/bin/kb recall [<kb>] --tag <tag>
${CLAUDE_PLUGIN_ROOT}/bin/kb recall --query "<text>" --max-results 5
```

- `--query` checks `index.json` first, then runs lexical (`rg`-backed) search across indexable sections.
- `--tag` lists pages whose frontmatter `tags:` includes the given tag.
- One of `--query` or `--tag` is required.
- Defaults: 20 total results.
- Distinct from `${CLAUDE_PLUGIN_ROOT}/bin/kb search`, which covers the whole KB including the inbox. Use `recall` for "what do we know about X" style questions; use `search` when you specifically need to grep raw material.

## pending

List unprocessed inbox material.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb pending [<kb>]
${CLAUDE_PLUGIN_ROOT}/bin/kb pending <kb> --max-results 10
${CLAUDE_PLUGIN_ROOT}/bin/kb pending --json
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
${CLAUDE_PLUGIN_ROOT}/bin/kb brief <kb>
${CLAUDE_PLUGIN_ROOT}/bin/kb brief <kb> --max-chars 5000
```

Default max: 12,000 characters.

## open

Read a specific KB file by relative path.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb open <kb> <path>
${CLAUDE_PLUGIN_ROOT}/bin/kb open <kb> <path> --max-chars 10000
```

- Rejects absolute paths and path traversal.
- Default max: 20,000 characters.
- Prints content to stdout (does not open an editor).

## search

Lexical search using `rg` (with Python fallback).

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb search <kb> "<query>"
${CLAUDE_PLUGIN_ROOT}/bin/kb search "<query>"              # search all KBs
${CLAUDE_PLUGIN_ROOT}/bin/kb search <kb> "<query>" --max-results 10 --glob "*.md"
${CLAUDE_PLUGIN_ROOT}/bin/kb search <kb> "<query>" --exclude-inbox
```

- Default: 20 total results, up to 3 matches per file, inbox included.
- Uses `rg` when available; falls back to Python `re` over `.md` files.
- Excludes `.git/` automatically.
- `--glob` is passed through to `rg`. **Gotcha:** rg's `--glob` does *not* anchor on the search root — `--glob 'inbox/**/*.md'` will not match `inbox/2026/05/foo.md`. Use simple patterns like `*.md` or `*.json`.
- Result `title` field is taken from the file's first H1 heading, or first non-blank body line, falling back to a filename slug.

## stage

Stage one of four shapes into a KB inbox:

- **Note** — agent-written observation, semi-structured (YAML frontmatter + body).
- **Document** — any text file, copied verbatim, no frontmatter.
- **URL pointer** — a link to be fetched and summarised later by `kb-dream`.
- **Directory** — bulk-stage every text file under a source tree as documents.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb stage <kb> --note "<text>"                              # note
${CLAUDE_PLUGIN_ROOT}/bin/kb stage <kb> --kind decision --note "<text>" --title T    # note with kind+title
${CLAUDE_PLUGIN_ROOT}/bin/kb stage <kb> --file <path>                                # document
${CLAUDE_PLUGIN_ROOT}/bin/kb stage <kb> --url <https://...>                          # URL pointer
${CLAUDE_PLUGIN_ROOT}/bin/kb stage <kb> --url <https://...> --note "<description>"   # URL + description
${CLAUDE_PLUGIN_ROOT}/bin/kb stage <kb> --dir <path>                                 # bulk: every text file under <path>
```

Mode is determined by which flag is set. `--dir` is mutually exclusive with `--note`, `--file`, and `--url`. `--file` is mutually exclusive with `--note` and `--url`. `--note` may accompany `--url` as an optional description body.

### Notes (`--note`)

- Agent-written observations: memory, preferences, decisions worth remembering.
- Written with YAML frontmatter (`created_at`, `kind`, optional `source`, optional `title`).
- Notes own their own headings — the CLI does not prepend one.
- `--kind` accepts any string and is written verbatim to frontmatter. Suggested starting points: `decision`, `domain-fact`, `codebase-fact`, `runbook-note`, `retrospective`, `followup`, `raw-note` (default when `--kind` is omitted). Invent KB-specific kinds (`hypothesis`, `open-question`, `benchmark`, ...) freely.

### Directory (`--dir`)

- Walks a source tree recursively and bulk-stages every recognised text file as a document.
- **Text formats** (`.md`, `.markdown`, `.txt`, `.org`, `.rst`) — copied verbatim, no frontmatter.
- **Extractable formats** (`.pdf`, `.docx`, `.pptx`, `.xlsx`, `.epub`, `.html`/`.htm`) — converted to Markdown via `markitdown`, written with provenance frontmatter (`extracted_from`, `extractor`, `kind: extracted`). Original binary is dropped by default. Use `--keep-source` to also copy originals to `sources/YYYY/MM/`.
- **Skipped**: hidden files/dirs, common SCM/build dirs (`.git`, `node_modules`, `__pycache__`, `dist`, `build`, `venv`, `target`, `out`, `.tox`), binary text-extension files (null bytes in first 8 KB), empty files, and oversized text files (> 1 MB unless `--force`). Extractable formats bypass binary + size checks — the source byte count doesn't matter, the extracted text does.
- **Without `markitdown` installed**: extractable formats land in a separate `extractor_missing` skip category with a one-line install hint (`pip install markitdown`); surrounding text formats still ingest normally.
- All files land under a single `inbox/YYYY/MM/<timestamp>-NNN-<slug>.md` prefix and are committed together: `kb: stage directory <basename> (N files[, +K source])`.
- `--kind`, `--title`, `--source`, `--note` are ignored for `--dir`; extracted files carry their own provenance frontmatter, while text files are copied verbatim. A warning is printed if these flags are set.
- JSON output enumerates `staged`, `extracted`, `sources_kept`, and per-category `skipped` so the agent can decide whether to re-run with `--force`, `--keep-source`, or stage misses individually via `--file`.
- Typical use: "set up a KB from this project's sources" → `${CLAUDE_PLUGIN_ROOT}/bin/kb bootstrap <name> --path ...` then `${CLAUDE_PLUGIN_ROOT}/bin/kb stage <name> --dir ~/Documents/project-foo/`, then a `kb-dream` pass to consolidate.

### Documents (`--file`)

For text formats: copied verbatim into `inbox/YYYY/MM/<timestamp>-<source-stem>.md`, no frontmatter, no auto-heading. The file is what it is.

For extractable formats (`.pdf`, `.docx`, `.pptx`, `.xlsx`, `.epub`, `.html`/`.htm`): same destination shape, but content is the `markitdown` output, prepended with provenance frontmatter:

```yaml
---
created_at: "<ISO>"
extracted_from: "/abs/path/to/foo.pdf"
extractor: "markitdown"
kind: "extracted"
source: "sources/2026/06/foo.pdf"     # only present when --keep-source was set
---
```

- `--kind`, `--title`, `--source` are ignored (extracted documents own their own provenance).
- `--keep-source` (default off) copies the original binary to `sources/YYYY/MM/<basename>.ext` alongside the extracted Markdown, and adds the `source:` line to frontmatter. Use when visual layout matters or you may re-extract later. Default behaviour drops the binary — the KB stays git-friendly.
- Without `markitdown`: errors with an install hint (`pip install markitdown`).
- Manual drag-and-drop of a `.md` into `inbox/` still produces the same shape as a text-format `--file`; first-class path. The next `kb-dream` pass picks it up.
- Commit message: `kb: stage document <basename>` for text formats, `kb: stage extracted <basename>` (with optional `(+source)`) for extracted formats.

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
- Rejects unsupported binary files; extractable formats are converted via `markitdown`. Text files over 1 MB warn and require `--force`.
- Does **not** scan content for secrets. Treat "no secrets in the KB" as agent guidance.
- Auto-commits by default (`--no-commit` to skip).

## reindex

Rebuild `<kb>/index.json` — a structured manifest of every Markdown file under auto-discovered indexable sections (excluding READMEs and dotfiles).

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb reindex [<kb>]
${CLAUDE_PLUGIN_ROOT}/bin/kb reindex [<kb>] --dry-run
${CLAUDE_PLUGIN_ROOT}/bin/kb reindex [<kb>] --no-commit
${CLAUDE_PLUGIN_ROOT}/bin/kb reindex --json
```

- Each entry: `path`, `title`, `section` (top-level directory), `tags`, `summary` (first prose paragraph, ~200 chars), `word_count`, `last_modified` (ISO, from git), optional `kind` (when frontmatter carries one).
- Indexable sections are top-level directories that contain Markdown files, excluding dot-directories, `inbox/`, `sources/`, and `tools/`.
- Written to `<kb>/index.json` at the KB root — visible, committable, agent-readable.
- Auto-commits "kb: rebuild index.json" when content changes; `--no-commit` to skip. Use `--no-commit` when rebuilding as part of a larger KB content commit.
- `--dry-run` reports entry counts and diff without writing.
- Falls back to the default KB when `<kb>` is omitted.
- `INDEX.md` is left untouched — that file stays agent-curated narrative. The two indices serve different audiences: `INDEX.md` for humans/agents reading prose, `index.json` for machine retrieval.

`${CLAUDE_PLUGIN_ROOT}/bin/kb recall` consults `index.json` first (title/tag/summary hits) before falling back to body grep. When `index.json` is absent, `${CLAUDE_PLUGIN_ROOT}/bin/kb recall` still works but prints a tip to run `${CLAUDE_PLUGIN_ROOT}/bin/kb reindex`.

Refresh is explicit: `${CLAUDE_PLUGIN_ROOT}/bin/kb remember`, `${CLAUDE_PLUGIN_ROOT}/bin/kb stage`, and `kb-dream` do not auto-rebuild. Run `${CLAUDE_PLUGIN_ROOT}/bin/kb reindex --dry-run` during a writing cluster, then rebuild the generated index after the content changes are settled.

## forget

Remove a single page from an indexable section.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb forget [<kb>] <path>
${CLAUDE_PLUGIN_ROOT}/bin/kb forget [<kb>] <path> --reason "<text>"
${CLAUDE_PLUGIN_ROOT}/bin/kb forget [<kb>] <path> --dry-run
${CLAUDE_PLUGIN_ROOT}/bin/kb forget [<kb>] <path> --no-commit
${CLAUDE_PLUGIN_ROOT}/bin/kb forget --json [<kb>] <path>
```

- `<path>` must be relative to the KB root and live under an indexable section. Inbox/source/tool material is out of scope (use direct git operations or move inbox material into `inbox/processed/`).
- Refuses contract files (`BRIEF.md`, `AGENTS.md`, `INDEX.md`, `LOG.md`, `index.json`, `README.md`, `.gitignore`) and any path that escapes the KB root.
- Removes the file, appends a one-line entry to `LOG.md` in the form `- YYYY-MM-DD: forgot PATH — REASON`, and auto-commits `kb: forget PATH` covering both the deletion and the log update. `--no-commit` leaves the changes uncommitted.
- Falls back to the default KB when `<kb>` is omitted.

### Soft for retrieval, hard for surface

Forget removes the file from the agent's working surface — `${CLAUDE_PLUGIN_ROOT}/bin/kb recall`, `${CLAUDE_PLUGIN_ROOT}/bin/kb search`, `${CLAUDE_PLUGIN_ROOT}/bin/kb open`, `index.json` after the next reindex — but git history preserves the content. `git log --all -- <path>` recovers what was forgotten and when. This is the v0 stand-in for `kb supersede`: replacement is implicit via git history.

### What forget does NOT do

- **Auto-rebuild `index.json`.** Run `${CLAUDE_PLUGIN_ROOT}/bin/kb reindex <kb>` afterwards. (Stale-index tip is printed.)
- **Auto-edit `INDEX.md`.** If the forgotten path is referenced from the agent-curated `INDEX.md`, forget warns and leaves the link in place — edit by hand. The check is a literal Markdown-link substring scan for that relative path.

Exit codes follow the global table at the top of this file: `1` on filesystem/commit failure or missing file, `2` on bad arguments (e.g. path outside indexable sections), `3` on safety rejection (traversal, protected file).

## sync

Synchronize KB git repos with their remotes.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/kb sync <kb>
${CLAUDE_PLUGIN_ROOT}/bin/kb sync --all
```

- Pulls with rebase, then pushes local commits.
- Stops on dirty working tree.
- Stops on conflicts — does not auto-resolve.
- Reports local-only KBs (no remote) and exits successfully.
