---
name: spec-driven-execution
description: This skill should be used when the user asks to "start a spec", "create a spec for X", "set up a spec folder", "plan this properly before coding", "break this work into changes", "archive this spec", "what's in active changes", or works on non-trivial tasks (architectural changes, cross-module refactors, GitHub issues with subtasks, work that spans multiple sessions) that benefit from durable explicit planning, design, and validation steps. Each change is captured in a self-contained folder with a mini-spec (description + validation + tasks) written before any code; archived folders double as the decision record. Skip for single-commit work or focused bug fixes.
version: 0.1.0
---

# Spec-Driven Execution

A protocol for breaking a larger piece of work into a sequence of small, individually
validated changes. The "spec" is per-change, not project-wide: every change has a
description (what + why) and a validation contract (scope + decisions + checks)
written *before* any code is touched. The change folder is the durable record
across sessions; archived, it is the decision trail.

## When to use it

Use it when **any** of these are true:

- The work has more than ~3 logically distinct sub-tasks.
- It will take more than one session to finish.
- Multiple people / agents may touch it across that time.
- It crosses module boundaries, schema boundaries, or service boundaries.
- The user has already broken the work into subitems (numbered list, subissues, a checklist).

Skip it for single-commit work, focused bug fixes, or anything you'd reasonably finish
in one sitting without needing a checklist to survive context compaction.

## Where the workspace lives

```
.changes/
├── CLAUDE.md         # The workflow protocol — copy from assets/templates
├── PROJECT.md        # Umbrella context for this batch of work
├── active/           # In-flight changes
│   └── {N-slug}/
│       ├── description.md   # REQUIRED — task + context pointers
│       ├── validation.md    # REQUIRED — scope, locked decisions, checks
│       ├── tasks.md         # REQUIRED — implementation checklist
│       ├── proposal.md      # OPTIONAL — see the optionals matrix
│       ├── design.md        # OPTIONAL
│       └── impact.md        # OPTIONAL
└── archive/          # Completed changes — the decision record
```

`.changes/` is **gitignored by default**. It's a personal working space. If the
team wants the audit trail to be durable across the org rather than the
individual, commit it explicitly — but then keep the content tight, because it
becomes a maintenance surface.

Change IDs are `N-slug` where `N` is a local ordering number (1, 2, 3…) reflecting
execution order, and `slug` is grep-friendly kebab-case. Numbering is local to the
branch — collisions across branches resolve manually on merge.

## Phase detection

Determine the current phase by inspecting the workspace:

| Condition | Phase |
|---|---|
| No `.changes/` directory | **Phase 0** — Scaffold |
| `.changes/` exists, no `PROJECT.md` | **Phase 0** — Frame the umbrella |
| `PROJECT.md` exists, no `active/` folders yet | **Phase 1** — Decompose into changes |
| One or more `active/{N-slug}/` exists, missing `description.md` or `validation.md` | **Phase 2** — Frame the change |
| `description.md` + `validation.md` exist, no/empty `tasks.md` | **Phase 3** — Plan |
| `tasks.md` populated with unchecked boxes | **Phase 4** — Execute |
| `tasks.md` all checked, validation not yet run | **Phase 5** — Validate |
| Validation green, folder still in `active/` | **Phase 6** — Archive |

State the detected phase to the user before proceeding.

## Workflow

### Phase 0 — Scaffold

If `.changes/` doesn't exist, bootstrap it. See
[references/scaffolding.md](references/scaffolding.md) for how to start from a
GitHub issue, a freeform prompt, or an already-running piece of work.

Minimum scaffold:

1. `mkdir -p .changes/active .changes/archive`
2. Copy [assets/templates/CLAUDE.md](assets/templates/CLAUDE.md) → `.changes/CLAUDE.md`
3. Copy [assets/templates/PROJECT.md](assets/templates/PROJECT.md) → `.changes/PROJECT.md`
4. Decide whether to gitignore `.changes/` (default) or commit it (team-wide audit trail)

The `.changes/CLAUDE.md` is the protocol file — agents working in any subfolder
will load it as a `CLAUDE.md` and follow the conventions without needing this
skill loaded.

### Phase 1 — Frame the umbrella

Write `PROJECT.md`. It is the stable context for *this batch of work* across
sessions:

- The source issue / prompt verbatim (don't paraphrase — paraphrasing loses scope nuance)
- Where the authoritative external context lives (spec repos, design docs, Slack threads)
- The candidate decomposition into changes — a numbered list mapping subitems → change IDs
- Scope boundaries — what's in this batch, what's adjacent but excluded

`PROJECT.md` is short. ~50–100 lines. Anything longer probably belongs in a
specific change's `description.md` or in an external doc you link from here.

### Phase 2 — Frame the change

For each change you're about to start: create `active/{N-slug}/`, write
`description.md` and `validation.md`, **before any code**.

See [references/framing.md](references/framing.md) for the structure of each file
and the rules for locking decisions.

The single most load-bearing rule: **enumerate sub-items as separate bullets in
both `description.md` and `validation.md`.** Two ideas hidden under one bullet
silently resolve together when only one of them was actually addressed. This is
the most common failure mode of this protocol — see
[references/failure-modes.md](references/failure-modes.md) for the worked example
that motivated the rule.

### Phase 3 — Plan

Fill in `tasks.md`. Flat checklist of *implementation* steps. Checks live in
`validation.md`; `tasks.md` references them but doesn't duplicate. The checklist
is the persistent version of `TodoWrite` across sessions.

Add `proposal.md` / `design.md` / `impact.md` per the matrix in
[references/framing.md](references/framing.md). Skip all three for mechanical
changes.

### Phase 4 — Execute

Work the checklist. Update `tasks.md` in place as understanding shifts. Only
update `validation.md` if scope or locked decisions genuinely change — not for
routine task-list churn.

If a locked decision starts to look wrong: **surface it to the user**, don't flip
it silently. Locked decisions are commitments to a specific reading of the
problem; renegotiating them is in scope, doing so without saying so isn't.

### Phase 5 — Validate

Run every check in `validation.md`. Resolve each sub-item from `description.md`
explicitly — name it, then either tick it or note that it landed differently
than framed (and why).

If scope reframed mid-flight (it often does), **re-enumerate the original
sub-items against the new deliverable**. Don't let a reframing absorb sub-items
without naming each one. The conflation failure mode in
[references/failure-modes.md](references/failure-modes.md) is exactly this.

### Phase 6 — Archive

Move `active/{N-slug}/` → `archive/{N-slug}/`. The archived folder is now the
decision record. Don't edit archived changes — if something needs updating,
create a new change that references the archived one.

## Bootstrapping from a GitHub issue

When the work originates from a GitHub issue:

1. `gh issue view <N>` — fetch the issue body and any linked subissues.
2. Read the issue carefully, including linked spec / design references.
3. Draft a candidate decomposition: subissues map to change IDs, otherwise carve
   along natural module / phase boundaries.
4. Surface the decomposition to the user before scaffolding. Ask once, then
   commit.
5. Scaffold `.changes/` as in Phase 0.
6. Capture the issue body verbatim under "Source" in `PROJECT.md`.

See [references/scaffolding.md](references/scaffolding.md) for the templates.

## Bootstrapping from a freeform prompt

When there's no issue, just a conversation:

1. Restate the goal back to the user in domain terms. Confirm.
2. Probe for the things that *aren't* obvious from the prompt: deadline,
   stakeholders, constraints, scope boundaries the user is implicit about.
3. Draft a candidate decomposition; surface; commit.
4. Scaffold as in Phase 0. Capture the restated goal in `PROJECT.md`.

If after probing the work turns out to be small enough for a single sitting,
skip the protocol entirely — it has overhead, and overhead on a small change
is waste.

## Anti-patterns

- **Two sub-items hiding under one bullet.** A bullet joined by "A *and* B" or
  "A *or* B" almost always hides two distinct sub-tasks. Split them. See
  [references/failure-modes.md](references/failure-modes.md).
- **Reframing without re-enumerating.** When a thread's premise turns out wrong
  mid-flight, the close-out resolves the *new* deliverable. Sub-items from the
  *original* framing then silently fall off. Re-enumerate.
- **Paraphrased user clarifications.** "Out of scope per user clarification" is
  doing load-bearing work. Quote the clarification with its exact scope:
  *"user said: no schema rename on `{schema}` tables"* not *"user said:
  leave `{schema}` tables alone"*.
- **No assertion behind a "behavior unchanged" claim.** If the change is meant
  to leave a behavior unchanged, write the assertion that proves it. The
  symmetric form of "for any code path you change, write the test that proves
  the new behavior".
- **Skipping framing.** `description.md` + `validation.md` written *after* code
  exists is rationalization, not framing. The contract has to predate the work.
- **Inflated `tasks.md`.** It's a flat checklist, not a doc. If a task needs
  prose, that prose belongs in `description.md` or `design.md`.
- **Editing archived changes.** Archived = frozen. If the world moved, write a
  new change.
- **One huge change folder.** If `tasks.md` is growing past ~30 items or
  `description.md` past ~150 lines, split. The scope grew; the folder should
  too, into siblings.

## Subagent patterns

When delegating per-change work:

**Framing reviewer** — spawn before execution begins:
> "Read `.changes/active/{N-slug}/description.md` and `validation.md`. For each
> sub-item in description.md, locate where validation.md addresses it
> (scope, decisions, tests, or success criteria). Return a list of sub-items
> that aren't explicitly covered. Don't propose fixes — just identify gaps."

**Close-out reviewer** — spawn at Phase 5:
> "Read `.changes/active/{N-slug}/`. For each sub-item in the original
> description.md, state whether it landed, landed differently, or was deferred.
> Cross-reference against tasks.md and any commits made since framing. Flag
> any sub-item that resolved silently — i.e. is checked off in tasks.md
> without being named in the validation pass."

**Decomposer** — spawn at Phase 1:
> "Read the GitHub issue at {url} (or the conversation in
> `.changes/PROJECT.md` "Source"). Propose a decomposition into 3–7 change
> folders. For each, suggest: ID slug, one-sentence task, the natural
> boundaries (module, phase, schema) that justify it as its own change. Don't
> write the change folders themselves — just the decomposition."
