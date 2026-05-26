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
3. `kb pending <kb>` — list unprocessed inbox material when picking up where a previous session left off.
4. `kb search <kb> "<query>"` — find specific knowledge.
5. `kb open <kb> <path>` — read a specific file only when you know the path.
6. Direct repo inspection only if the KB is insufficient.

### Search tokenization

`kb search` is **lexical** and treats its query as a regex pattern. A quoted multi-word phrase must match the file *exactly* — if a phrase returns zero results, retry with single keywords or two-token slices. Searches default to 20 total results / 3 matches per file.

## Staging knowledge

Three staging shapes — choose the one that fits the material:

```bash
kb stage <kb> --note "<text>"                      # short agent-written note
kb stage <kb> --kind decision --note "<text>"      # note with explicit kind
kb stage <kb> --file <path>                        # text file, verbatim
kb stage <kb> --url <https://...>                  # URL pointer (kb-dream fetches/summarises later)
kb stage <kb> --url <https://...> --note "<why>"   # URL + description
```

Note kinds: `decision`, `domain-fact`, `codebase-fact`, `runbook-note`, `retrospective`, `followup`, `raw-note` (default).

- `--file` is mutex with `--note` and `--url`. Manual drag-and-drop into `inbox/` produces the same shape as `--file`.
- URL pointers must be `http://` or `https://`. They are **not fetched at stage time** — `kb-dream` resolves them during consolidation.
- Use `--title` for a descriptive heading on notes. All stages auto-commit to `inbox/`.
- Use `--kind followup` for deferred work the next session should pick up (e.g. "remember to gather more sources on X").

## Rules

- **Never edit `knowledge/` directly.** Stage to `inbox/` and let `kb-dream` consolidate.
- Use the `kb-dream` skill when asked to consolidate inbox notes into canonical knowledge.
- **Search before staging** — avoid duplicating existing knowledge.
- **Keep notes concise and durable** — no conversation transcripts.
- **Preserve provenance** — note where facts came from.
- Run `kb sync <kb>` at logical handoff points when the KB has a remote.
- **Stage to the KB only — do not also write the same fact to auto-memory.** If a fact belongs in a KB (project decisions, domain knowledge, runbook material, future follow-ups for that project), one source of truth: the KB. Pointers from auto-memory to KB content create drift; do not introduce them.

## Command reference

See `references/commands.md` for full command documentation.
See `references/safety.md` for safety rules.
See `references/kb-contract.md` for KB structure and template details.
