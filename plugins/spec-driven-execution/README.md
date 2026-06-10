# spec-driven-execution

Claude Code plugin that runs non-trivial work through a per-change mini-spec discipline: every change is framed (description + validation) before any code, lives in a self-contained folder, and becomes a frozen decision record once archived.

## Design principle

> Frame → Plan → Execute, in that order. The contract has to predate the work; framing written from existing code is rationalization, not framing.

The change folder is the durable unit across sessions. A fresh agent dispatched against `active/{N-slug}/` should be able to pick it up cold from the framing files alone — no chat history required.

## What it does

Provides one skill, `spec-driven-execution`, with a seven-phase workflow (0–6):

| Phase | What |
|---|---|
| 0 — Scaffold | Bootstrap `.changes/` and copy the protocol templates |
| 1 — Frame umbrella | Write `PROJECT.md` for the batch |
| 2 — Frame change | Write `description.md` + `validation.md` per change |
| 3 — Plan | Fill `tasks.md`; add `proposal` / `design` / `impact` if warranted |
| 4 — Execute | Work the checklist; update in place |
| 5 — Validate | Run every check; resolve each sub-item explicitly |
| 6 — Archive | Freeze the folder as the decision record |

Phase is detected from `.changes/` state — the skill picks up wherever the workspace already is.

## When to use it

Skip it for single-commit work or anything you'd reasonably finish in one sitting. Reach for it when:

- The work has more than ~3 distinct sub-tasks
- It will span multiple sessions
- Multiple people / agents may touch it
- It crosses module, schema, or service boundaries

## Layout

```text
plugins/spec-driven-execution/
  .claude-plugin/plugin.json
  CHANGELOG.md
  scripts/
    test_spec_driven_execution.sh   # structural smoke check
  skills/spec-driven-execution/
    SKILL.md
    references/         # framing.md, scaffolding.md, failure-modes.md
    assets/templates/   # CLAUDE.md, PROJECT.md + per-change file templates
```

At runtime the skill writes into your project's `.changes/` directory — gitignored by default; commit it explicitly for a team-wide audit trail.

See [SKILL.md](skills/spec-driven-execution/SKILL.md) for the full workflow and [references/failure-modes.md](skills/spec-driven-execution/references/failure-modes.md) for the lessons that motivated the rules.
