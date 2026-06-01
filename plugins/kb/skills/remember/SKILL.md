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

Quick rule: durable single-sentence fact → here. Anything ephemeral, preference-shaped, or workflow-normative belongs elsewhere. The full routing rules (including personal vs project KB selection and the litmus test) live in `${CLAUDE_PLUGIN_ROOT}/references/scoping.md`.

Good examples:

- "The nightly job runs at 02:00 UTC via cron." (project)
- "We abandoned PostgreSQL JSON columns in 2024 — search latency was 3x." (domain)
- "My birthday is 15 November." (personal — goes to a personal `user-kb` if registered)
- "We should look into &lt;library name&gt; next time we work on X feature." (follow-up)

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

Full details: `${CLAUDE_PLUGIN_ROOT}/references/scoping.md` (routing rules), `${CLAUDE_PLUGIN_ROOT}/references/commands.md`, `${CLAUDE_PLUGIN_ROOT}/references/kb-contract.md`.
