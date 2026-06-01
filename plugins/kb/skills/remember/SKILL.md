---
name: remember
description: This skill should be used when the user asks to "remember that X", "note that X", or wants to save a short durable one-sentence fact (project, domain, codebase, or personal-life) to a KB. Routes by the target KB's stated purpose — project KBs hold project facts, a personal user-kb holds personal-life facts. Explicit invocation overrides the heuristic. Ephemeral user preferences and short-lived project state belong in auto-memory; normative workflow rules belong in CLAUDE.md/AGENTS.md.
version: 0.2.0
---

# kb:remember

Append a one-paragraph fact to a KB's `notes/` directory. Notes are append-only — `kb-dream` never consolidates them.

## Remember vs stage — the functional distinction

The boundary is **lifecycle**, not length:

- **`kb remember`** — atomic facts queryable as-is. They stand alone, never need synthesising into something bigger. Once written, they're final.
- **`kb stage`** — raw material that should be folded into a larger canonical page by `kb-dream`. The note alone isn't the deliverable; the eventual `knowledge/` page is.

If you're stating a single fact you'd want to look up later by tag or substring → `remember`. If you're producing input for a synthesis step → `stage`.

## When to use vs other layers

| Fact | Layer |
|---|---|
| Ephemeral user preferences | Claude's auto-memory — NOT the KB |
| Normative workflow rules | CLAUDE.md / AGENTS.md — NOT the KB |
| **Short project / domain / codebase facts** | **`kb remember`** (this skill) → KB `notes/` |
| Longer-form decisions / runbook material | `kb stage` → KB `inbox/` |

**Litmus test:** would re-deriving this fact require meaningful work? Yes → KB. Trivial to re-ask → auto-memory.

Good examples:

- "The nightly job runs at 02:00 UTC via cron."
- "We abandoned PostgreSQL JSON columns in 2024 — search latency was 3x."
- "We should look into <library name> library next time we work on X feature."

## Command

```bash
kb remember "<one-sentence fact>"
kb remember "<one-sentence fact>" --tags emma,domain
kb remember "<one-sentence fact>" --kb <kb>
```

- Writes to `notes/YYYY/MM/<timestamp>-<slug>.md` with `created_at` + `tags` frontmatter.
- Body is the text, verbatim — no auto-heading.
- Falls back to the default KB if `--kb` is omitted.

Do not also write the same fact to auto-memory. One source of truth per fact.

Full details: `${CLAUDE_PLUGIN_ROOT}/references/commands.md` and `${CLAUDE_PLUGIN_ROOT}/references/kb-contract.md`.
