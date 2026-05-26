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

Use the KB for facts that are **expensive to re-derive** — facts that took grepping, reading across files, asking the user, or synthesising multiple sources to discover. Cheap-to-re-ask facts belong elsewhere.

### Three-layer routing — where does this fact go?

| Fact | Layer |
|---|---|
| Personal user preferences ("I prefer rebase", "I like X") | Claude's **auto-memory** — NOT the KB |
| Normative workflow rules ("don't push to master") | **CLAUDE.md** / **AGENTS.md** — NOT the KB |
| Short project / domain / codebase facts ("EMMA's nightly job runs at 02:00 UTC") | KB `notes/` via `kb remember` |
| Decisions, runbook material, longer-form facts | KB `inbox/` via `kb stage`, consolidated to `knowledge/` by `kb-dream` |
| URL pointers to read later | KB `inbox/` via `kb stage --url` |
| Project TODOs that should survive sessions | KB `inbox/` via `kb stage --kind followup` |

**Litmus test:** would re-deriving this fact require meaningful work? Yes → KB. Could just re-ask the user trivially → auto-memory.

## When NOT to use

- For ephemeral conversation state — use tasks or plans instead.
- For code that belongs in the project repo.
- For secrets, credentials, or private personal data.
- For personal user preferences — those are auto-memory's job.
- For team workflow rules — those belong in `CLAUDE.md` / `AGENTS.md`.

## Progressive disclosure

Always follow this retrieval order — do not skip steps:

1. `kb list` — discover which KBs exist.
2. `kb brief <kb>` — read the compact summary before searching.
3. `kb pending <kb>` — list unprocessed inbox material when picking up where a previous session left off.
4. `kb recall [<kb>] --query "<text>"` — preferred for "what do we know about X" questions; searches synthesised material (`notes/` + `knowledge/`) only.
5. `kb recall [<kb>] --tag <tag>` — filter notes by tag.
6. `kb search <kb> "<query>"` — wider net; includes the raw inbox. Use when recall comes up empty or you specifically need raw material.
7. `kb open <kb> <path>` — read a specific file only when you know the path.
8. Direct repo inspection only if the KB is insufficient.

### Search tokenization

Both `kb recall --query` and `kb search` are **lexical** and treat the query as a regex pattern. A quoted multi-word phrase must match the file *exactly* — if a phrase returns zero results, retry with single keywords or two-token slices. Searches default to 20 total results / 3 matches per file.

## Capturing knowledge

There are two write paths into the KB; they go to different places and have different lifecycles.

### `kb remember` — short memories (`notes/`)

```bash
kb remember "<one-sentence fact>"
kb remember "<one-sentence fact>" --tags emma,domain
```

For short project / domain / codebase facts that are expensive to re-derive but too small for a `knowledge/` page. Written to `notes/YYYY/MM/...` with `tags:` and `created_at:` frontmatter. **`notes/` is append-only — `kb-dream` never touches it.**

### `kb stage` — inbox material for `kb-dream`

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

### Which path?

- A fact you'd want to look up later by tag or substring → `kb remember`.
- Material that should be consolidated into a long-form canonical page → `kb stage`.
- An article / file / URL that the next `kb-dream` should ingest → `kb stage --url` / `--file`.

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
