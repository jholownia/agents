---
name: kb-registry
description: >
  Use when you need persistent project or domain knowledge that survives across
  conversations — architecture decisions, domain facts, runbook notes, or
  codebase patterns. Manages multiple git-backed knowledge bases with inbox
  staging, lexical search, and progressive disclosure.
---

# KB Registry

## When to use

- You suspect durable project/domain knowledge exists (architecture, domain rules, past decisions).
- You discover a fact worth preserving across conversations.
- You need context that goes beyond what the current repo contains.

## When NOT to use

- For ephemeral conversation state — use tasks or plans instead.
- For code that belongs in the project repo.
- For secrets, credentials, or private personal data.

## Progressive disclosure

Always follow this retrieval order — do not skip steps:

1. `kb list` — discover which KBs exist.
2. `kb brief <kb>` — read the compact summary before searching.
3. `kb search <kb> "<query>"` — find specific knowledge.
4. `kb open <kb> <path>` — read a specific file only when you know the path.
5. Direct repo inspection only if the KB is insufficient.

## Staging knowledge

When you discover durable facts during a conversation:

```bash
kb stage <kb> --kind <kind> --note "<text>"
```

Supported kinds: `decision`, `domain-fact`, `codebase-fact`, `runbook-note`, `retrospective`, `raw-note`.

Use `--title` for a descriptive heading. Notes are auto-committed to `inbox/`.

## Rules

- **Never edit `knowledge/` directly.** Stage to `inbox/` and let humans consolidate.
- Use the `kb-dream` skill when asked to consolidate inbox notes into canonical knowledge.
- **Search before staging** — avoid duplicating existing knowledge.
- **Keep notes concise and durable** — no conversation transcripts.
- **Preserve provenance** — note where facts came from.
- Run `kb sync <kb>` at logical handoff points when the KB has a remote.

## Command reference

See `references/commands.md` for full command documentation.
See `references/safety.md` for safety rules and secret scanning.
See `references/kb-contract.md` for KB structure and template details.
