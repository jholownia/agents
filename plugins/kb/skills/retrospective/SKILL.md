---
name: retrospective
description: >
  Save expensive-to-derive knowledge from the current session into a KB
  — research findings, debugging gotchas, workflow pitfalls, specs/plans
  to continue. Use on explicit request ("session retrospective", "save
  what we learned") OR auto-trigger when significant session-acquired
  knowledge would otherwise be lost on session end.
---

# kb:retrospective

End-of-session capture of knowledge that took meaningful work to derive and would be costly to rediscover. This skill **does not introduce new CLI verbs** — it teaches *when* and *what* to capture using the existing `kb remember` and `kb stage` verbs.

## When to use

### Explicit triggers

- "save what we learned this session"
- "session retrospective"
- "capture session findings"
- "stash what we figured out"

### Auto-trigger heuristic — invoke without being asked when:

- The session produced **research synthesis** that wasn't in any source file (cross-referencing multiple specs, reading code paths to understand behaviour, comparing alternatives).
- A **workflow pitfall** was discovered that another agent might trip over.
- A **high-level spec or plan** emerged that should continue across sessions.
- A **debugging gotcha** would save real time if found again.
- Significant time was spent on something the user is now about to wrap up.

### Timing — batch, don't fire on each finding

`kb:retrospective` is **end-of-session**, not real-time. Prefer to wait for a natural pause or topic shift before capturing rather than firing immediately on each discovery. Mid-session, hand individual single-sentence facts to `kb:remember` as you encounter them; let `kb:retrospective` handle the unsorted residue at the end.

Wrap-up signals that should trigger a capture pass:

- "ok that's it" / "let's wrap up" / "we're done here"
- "moving on to <something else>" / "different topic now"
- Implicit: the user has visibly finished a task and switched register (committing, asking what's next, saying thanks for the work).

### Do NOT auto-capture

- Trivial conversation state.
- Material already in CLAUDE.md / AGENTS.md / the project repo.
- Material better suited to an issue or PR description.
- Personal user preferences — those go to auto-memory.

## Triage — pick high-value items only

Don't dump everything from the session. For each candidate ask:

1. Did it take meaningful work to derive (≥5 minutes of thought, or required reading multiple files)?
2. Would it be expensive to rediscover next session?
3. Is it not already captured elsewhere?

If any answer is "no", skip it. If unsure on a large body of material, ask the user before staging.

## What goes where

| Category | Verb | Notes |
|---|---|---|
| Short factual finding | `kb remember "<text>" --tags ...` | One sentence, queryable by tag |
| Workflow pitfall, debugging gotcha | `kb stage <kb> --kind retrospective --note "..."` | Inbox material, dream consolidates later |
| Research synthesis worth a canonical page | `kb stage <kb> --kind retrospective --note "..."` | Same — dream picks shape |
| Specs / plans / TODOs for next session | `kb stage <kb> --kind followup --note "..."` | Surfaces in `kb pending` |
| URL discovered during research | `kb stage <kb> --url <url>` | Dream fetches and summarises |

If the user has multiple registered KBs, ask which one (or default to the project's KB if the session's work was clearly scoped to one project).

Full details: `${CLAUDE_PLUGIN_ROOT}/references/commands.md` and `${CLAUDE_PLUGIN_ROOT}/references/kb-contract.md`.
