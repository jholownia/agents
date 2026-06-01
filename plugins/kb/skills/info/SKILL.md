---
name: info
description: This skill should be used when the user asks "what KBs do I have", "brief me on <kb>", "list KBs", "how do I use the KB", references a *-kb name, or needs quick orientation in a session that touches a KB. Lists registered KBs, reads their compact briefs, and carries the three-layer scoping rules (durable facts → KB; user preferences and ephemeral state → auto-memory; workflow rules → CLAUDE.md/AGENTS.md).
version: 0.2.0
---

# kb:info

The **first** skill to reach for in a session that might touch a KB. Cheap, read-only, and carries the routing rules that decide whether a fact even belongs in the KB at all.

## Sibling skills — where else to go

- **Git / contract / clean-dirty state of a KB** → kb:registry (`kb status`).
- **"What's in the inbox" / content search / "what did we decide about X"** → kb:recall.
- **End-of-session capture** → kb:retrospective.

## Three-layer scoping — where does this fact go?

Three layers exist: Claude's auto-memory, project `CLAUDE.md`/`AGENTS.md`, and the KB. The axis is **durable fact vs ephemeral state**, not "personal vs project". Full routing rules, examples, and the litmus test live in `${CLAUDE_PLUGIN_ROOT}/references/scoping.md`.

Quick summary:

- **Durable facts** (project, domain, codebase, **or personal-life**) → KB via `kb remember` / `kb stage`.
- **User preferences about agent behaviour** (`"address me as bro"`, `"I prefer rebase"`) and **short-lived project state** → auto-memory.
- **Normative workflow rules** (`"don't push to master"`) → `CLAUDE.md` / `AGENTS.md`.

**Anti-duplication rule.** One source of truth per fact. Don't mirror a KB fact into auto-memory or vice versa — it creates drift.

## Commands

```bash
kb list                     # all registered KBs
kb brief <kb>               # compact summary (BRIEF.md)
```

- `kb list` is cheap; run it first when a KB might exist for the user's domain.
- `kb brief` is the progressive-disclosure entrypoint — read it before searching.

If the user names something ending in `-kb` (e.g. `emma-kb`, `hydra-kb`), it is a knowledge base — start with `kb list`.

Full routing rules: `${CLAUDE_PLUGIN_ROOT}/references/scoping.md`. Flag reference: `${CLAUDE_PLUGIN_ROOT}/references/commands.md`.
