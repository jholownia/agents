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

Staged notes are individual Markdown files with YAML frontmatter:

```yaml
---
created_at: "2026-05-12T10:30:00+01:00"
kind: "decision"
source_cwd: "/Users/jh/Code/agents"
source_file: null
source: null
agent: "claude-code"
status: "staged"
---

# Decision: Short Title

Content here.
```

Files are stored at `inbox/YYYY/MM/YYYYMMDD-HHMMSS-<slug>.md`.

## Optional frontmatter conventions

These fields are not first-class CLI flags in v0 — `kb-dream` writes them when consolidating, and `rg` finds them later:

- `supersedes:` — list of inbox/knowledge paths this note or page replaces.
- `last_reviewed:` — ISO date stamped on canonical pages so staleness is greppable.

## Validation

`kb add` rejects missing contract files by default and accepts them only with `--force`.
`kb status` reports missing contract files without mutating the KB.
