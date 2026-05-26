---
name: info
description: >
  Quick orientation in a session that might touch a KB. Lists
  registered KBs, reads their compact briefs, and explains how to use
  the KB. Carries the three-layer scoping rules (auto-memory vs
  CLAUDE.md vs KB). Triggers: "what KBs do I have", "brief me on <kb>",
  "list KBs", "how do I use the KB", any reference to a *-kb name.
---

# kb:info

The **first** skill to reach for in a session that might touch a KB. Cheap, read-only, and carries the routing rules that decide whether a fact even belongs in the KB at all.

## Sibling skills — where else to go

- **Git / contract / clean-dirty state of a KB** → kb:registry (`kb status`).
- **"What's in the inbox" / content search / "what did we decide about X"** → kb:recall.
- **End-of-session capture** → kb:retrospective.

## Three-layer scoping — where does this fact go?

| Fact | Layer |
|---|---|
| Personal user preferences ("I prefer rebase", "I like X") | Claude's **auto-memory** — NOT the KB |
| Normative workflow rules ("don't push to master") | **CLAUDE.md** / **AGENTS.md** — NOT the KB |
| Short project / domain / codebase facts ("EMMA's nightly job runs at 02:00 UTC") | KB `notes/` via `kb remember` |
| Decisions, runbook material, longer-form facts | KB `inbox/` via `kb stage`, consolidated to `knowledge/` by `kb-dream` |
| URL pointers to read later | KB `inbox/` via `kb stage --url` |
| Project TODOs that should survive sessions | KB `inbox/` via `kb stage --kind followup` |

**Litmus test:** would re-deriving this fact require meaningful work (grep, ask the user, synthesise across sources)? Yes → KB. Could just re-ask the user trivially → auto-memory.

**Anti-duplication rule.** If you came here via an auto-memory cue ("remember that <project fact>"), the fact goes to the KB *only* — do not also write it to auto-memory. One source of truth per fact; pointers from auto-memory to KB content create drift.

## Commands

```bash
kb list                     # all registered KBs
kb brief <kb>               # compact summary (BRIEF.md)
```

- `kb list` is cheap; run it first when a KB might exist for the user's domain.
- `kb brief` is the progressive-disclosure entrypoint — read it before searching.

If the user names something ending in `-kb` (e.g. `emma-kb`, `hydra-kb`), it is a knowledge base — start with `kb list`.

Full flag reference: `${CLAUDE_PLUGIN_ROOT}/references/commands.md`.
