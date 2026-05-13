# KB Registry — KB Contract

## Required structure

Every knowledge base must contain:

```
<kb-root>/
  AGENTS.md       # Agent rules for this KB
  BRIEF.md        # Compact summary — progressive disclosure entrypoint
  INDEX.md        # Navigational index
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
- Don't casually rewrite canonical knowledge
- Preserve provenance
- Prefer concise, durable notes
- No secrets or credentials
- Use git history for auditability

## Inbox format

Staged notes are individual Markdown files with YAML frontmatter:

```yaml
---
created_at: "2026-05-12T10:30:00+01:00"
kind: "decision"
source_cwd: "/Users/jh/Code/agents"
source_file: null
agent: "claude-code"
status: "staged"
---

# Decision: Short Title

Content here.
```

Files are stored at `inbox/YYYY/MM/YYYYMMDD-HHMMSS-<slug>.md`.

## Validation

`kb add` rejects missing contract files by default and accepts them only with `--force`.
`kb status` reports missing contract files without mutating the KB.
