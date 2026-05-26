# KB Registry — KB Contract

## Required structure

Every knowledge base must contain:

```
<kb-root>/
  AGENTS.md       # Agent rules for this KB
  BRIEF.md        # Compact summary — progressive disclosure entrypoint
  INDEX.md        # Navigational index
  LOG.md          # Maintenance and consolidation journal
  inbox/          # Staging area for raw material
  knowledge/      # Canonical synthesized knowledge
  sources/        # Optional source material or pointers
  tools/          # Reserved for future diagnostics (not executed in v0)
  .gitignore
```

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

## Inbox format

The inbox holds two shapes of material, distinguished by how they got there:

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
- `source` *(optional)* — short provenance string (e.g. `"discussion-123"`, `"external research"`).
- `title` *(optional)* — display title.
- `url` *(url notes only)* — the staged URL.

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

### Documents (verbatim, unstructured)

Produced by `kb stage --file <path>` or by manually dropping a Markdown file into `inbox/`. No frontmatter, no auto-heading — the file is what it is. Provenance lives in the git commit message (`kb: stage document <basename>`).

### Filenames

Both shapes are stored at `inbox/YYYY/MM/YYYYMMDD-HHMMSS-<slug>.md`. The slug is derived from `--title`/content for notes and from the source filename for documents.

## Optional frontmatter conventions (canonical pages only)

These fields apply to `knowledge/` pages, **not** inbox notes. `kb-dream` writes them when consolidating, and `rg` finds them later:

- `supersedes:` — list of inbox/knowledge paths this page replaces.
- `last_reviewed:` — ISO date stamped on canonical pages so staleness is greppable.

## Validation

`kb add` rejects missing contract files by default and accepts them only with `--force`.
`kb status` reports missing contract files without mutating the KB.
