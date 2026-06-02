# KB Registry — KB Contract

## Required structure

Every knowledge base must contain:

```text
<kb-root>/
  AGENTS.md       # Agent rules for this KB
  BRIEF.md        # Compact summary — progressive disclosure entrypoint
  INDEX.md        # Navigational index
  LOG.md          # Maintenance and consolidation journal
  inbox/          # Staging area for raw material
  knowledge/      # Seed canonical section (KBs may add others)
  notes/          # Append-only single-paragraph memories with tags
  sources/        # Optional source material or pointers
  tools/          # Reserved for future diagnostics (not executed in v0)
  .gitignore
```

### Lifecycle of each directory

- `inbox/` — raw material. By default, `kb-dream` consolidates useful material from here into an indexable canonical section. Includes notes (`--note`), documents (`--file`), and URL pointers (`--url`).
- `notes/` — **append-only**, never consolidated. Short single-paragraph facts written by `kb remember`. `kb-dream` never touches this directory.
- `knowledge/` — seed section for synthesised long-form pages. Agents may add other top-level canonical sections (`runbooks/`, `decisions/`, `specs/`, etc.) when the KB calls for it.

### Three-layer scoping (what goes where)

Routing across Claude's auto-memory, project `CLAUDE.md` / `AGENTS.md`, and the KB is documented in [scoping.md](scoping.md). The axis is durable fact vs ephemeral state, not "personal vs project". See that file for the full table, litmus test, and personal-vs-project KB routing.

## BRIEF.md

The primary entrypoint for agents. Should contain:

- Purpose and scope
- Key areas with directory descriptions
- Retrieval guidance

## AGENTS.md

KB-local rules that agents must follow:

- Stage raw material in `inbox/`
- Treat `inbox/` as source material and `knowledge/` as synthesized output
- Follow the KB's existing organization before inventing new categories
- Propose a dry-run plan before canonical rewrites unless explicitly told to apply
- Preserve provenance
- Prefer concise, durable notes
- No secrets or credentials
- Use git history for auditability

## LOG.md

Append a short entry when inbox notes are consolidated into canonical knowledge.
Entries should record consumed inbox/source paths, canonical pages created or updated, and unresolved questions.

## Notes format

Produced by `kb remember "<text>" [--tags <a,b,c>]`. Stored at `notes/YYYY/MM/<timestamp>-<slug>.md`:

```yaml
---
created_at: "2026-05-22T10:30:00+01:00"
tags: ["emma", "domain"]
---
EMMA's nightly job runs at 02:00 UTC via cron.
```

- One fact per file. The text is the body, verbatim.
- `tags:` is optional but recommended — `kb recall --tag <t>` uses it.
- `kb-dream` never reads or modifies this directory.

## Inbox format

The inbox holds three shapes of material, distinguished by how they got there:

### Notes (agent-written, semi-structured)

Produced by `kb stage --note ...`. Short observations: memory, preferences, decisions worth remembering. YAML frontmatter at the top:

```yaml
---
created_at: "2026-05-12T10:30:00+01:00"
kind: "decision"
source: null
---
# Decision: Short Title

Content here.
```

Frontmatter fields:

- `created_at` — ISO timestamp.
- `kind` — one of `decision`, `domain-fact`, `codebase-fact`, `runbook-note`, `retrospective`, `followup`, `raw-note`, or `url`.
- `source` _(optional)_ — short provenance string (e.g. `"discussion-123"`, `"external research"`).
- `title` _(optional)_ — display title.
- `url` _(url notes only)_ — the staged URL.

Notes own their headings; the CLI does not prepend one.

### URL pointers (`kind: url`)

Produced by `kb stage --url <url>`. The URL itself is the staged content; `kb-dream` fetches and summarises later. Frontmatter has `kind: url` and `url: <url>`; body is empty unless `--note "<description>"` was passed.

```yaml
---
created_at: "2026-05-22T10:30:00+01:00"
kind: "url"
url: "https://example.com/article"
---
Optional description from the agent.
```

### Documents and extracted files

Text documents are produced by `kb stage --file <path>` or by manually dropping a Markdown file into `inbox/`. No frontmatter, no auto-heading — the file is what it is. Provenance lives in the git commit message (`kb: stage document <basename>`).

Extractable formats (`.pdf`, `.docx`, `.pptx`, `.xlsx`, `.epub`, `.html`) are converted to Markdown via `markitdown` when available. These extracted inbox files do carry provenance frontmatter (`kind: extracted`, `extracted_from`, `extractor`, optional `source` when `--keep-source` copies the original under `sources/`).

### Filenames

Staged material is stored at `inbox/YYYY/MM/YYYYMMDD-HHMMSS-<slug>.md`. The slug is derived from `--title`/content for notes and from the source filename for documents.

## Optional frontmatter conventions (canonical pages only)

These fields apply to canonical pages in indexable sections, **not** inbox notes. `kb-dream` writes them when consolidating, and `rg` finds them later:

- `supersedes:` — list of inbox/canonical paths this page replaces.
- `last_reviewed:` — ISO date stamped on canonical pages so staleness is greppable.

## Validation

`kb add` rejects missing contract files by default and accepts them only with `--force`.
`kb status` reports missing contract files without mutating the KB.
