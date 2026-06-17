---
name: spec-driven-execution
description: This skill should be used when the user asks to "start a spec", "create a spec for X", "set up a spec folder", "plan this properly before coding", "break this work into changes", "design the architecture for this batch", "find the common shape across these changes", "archive this spec", "what's in active changes", or works on non-trivial tasks (architectural changes, cross-module refactors, GitHub issues with subtasks, batches of plausibly-similar work, work that spans multiple sessions). Skip for single-commit work or focused bug fixes.
version: 0.3.0
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
- The roadmap names **3+ items of plausibly-similar shape** (workflows, services,
  parsers, forms, scrapers, …). This is also the strongest signal to run the
  upfront *architecture pass* — see Phase 2.

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

Rows are evaluated top-down; **first match wins**.

| Condition | Phase |
|---|---|
| No `.changes/` directory | **Phase 0** — Scaffold |
| `.changes/` exists, no `PROJECT.md` | **Phase 0** — Frame the umbrella |
| `PROJECT.md` exists, decomposition empty / unfilled placeholder | **Phase 1** — Decompose into changes |
| Decomposition filled, no Architecture heading in `PROJECT.md` (a real `^## Architecture$` heading line, not the marker inside the scaffold's comment) | **Phase 2** — Architecture pass |
| Architecture heading present, no `active/{N-slug}/` folder yet | **Phase 3** — Frame the change (create the first `active/{N-slug}/`) |
| One or more `active/{N-slug}/` exists, missing `description.md` or `validation.md` | **Phase 3** — Frame the change |
| `description.md` + `validation.md` exist, no/empty `tasks.md` | **Phase 4** — Plan |
| `tasks.md` populated with unchecked boxes | **Phase 5** — Execute |
| `tasks.md` all checked, validation not yet run | **Phase 6** — Validate |
| Validation green, folder still in `active/` | **Phase 7** — Archive |

The Architecture heading's *presence* — not its contents — is the Phase 2
cue. When the pass is skipped because changes are heterogeneous, the
section body is a single line: *"No common shape — N independent changes."*
Either way the heading appears once the pass has been considered. Match it
as a real heading line (`^## Architecture$`), not as a substring — the
scaffold's comment block intentionally avoids the literal `## Architecture`
form so cheap text-greps don't false-positive.

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

### Phase 2 — Architecture pass

**Trigger:** decomposition names 3+ items of plausibly-similar shape, or any
change would naturally be framed *"like {N-1} but …"*.

**Output:** a `## Architecture` section in `PROJECT.md` (or sibling
`.changes/ARCHITECTURE.md` for heavyweight batches) — pattern survey,
proposed default shape, numbered `A-N` decisions. Per-change `validation.md`
references `A-N` (`per A-2`) or records deviations explicitly (`deviates
from A-2 because …`).

**Escape hatch:** when changes are genuinely heterogeneous, the section is a
single line — *"No common shape — N independent changes."* Manufacturing an
engine for work that doesn't have one is the inverse failure.

See [references/architecture.md](references/architecture.md) for the full
shape and deviation contract; [references/patterns.md](references/patterns.md)
for the starter pattern vocabulary.

### Phase 3 — Frame the change

For each change you're about to start: create `active/{N-slug}/`, write
`description.md` and `validation.md`, **before any code**.

See [references/framing.md](references/framing.md) for the structure of each file
and the rules for locking decisions. If Phase 2 produced architecture
decisions, locked decisions in this change should reference them (`per A-N`)
or call out deviations explicitly.

The single most load-bearing rule: **enumerate sub-items as separate bullets in
both `description.md` and `validation.md`.** Two ideas hidden under one bullet
silently resolve together when only one of them was actually addressed. This is
the most common failure mode of this protocol — see
[references/failure-modes.md](references/failure-modes.md) for the worked example
that motivated the rule.

### Phase 4 — Plan

Fill in `tasks.md`. Flat checklist of *implementation* steps. Checks live in
`validation.md`; `tasks.md` references them but doesn't duplicate. The checklist
is the persistent version of `TodoWrite` across sessions.

Add `proposal.md` / `design.md` / `impact.md` per the matrix in
[references/framing.md](references/framing.md). Skip all three for mechanical
changes.

### Phase 5 — Execute

Work the checklist. Update `tasks.md` in place as understanding shifts. Only
update `validation.md` if scope or locked decisions genuinely change — not for
routine task-list churn.

If a locked decision starts to look wrong: **surface it to the user**, don't flip
it silently. Locked decisions are commitments to a specific reading of the
problem; renegotiating them is in scope, doing so without saying so isn't.

The same rule applies to architecture decisions (`A-N`): if the proposed
default shape starts to fight the actual work, surface it and revise the
Architecture section explicitly rather than silently going off-shape.

### Phase 6 — Validate

Run every check in `validation.md`. Resolve each sub-item from `description.md`
explicitly — name it, then either tick it or note that it landed differently
than framed (and why).

If scope reframed mid-flight (it often does), **re-enumerate the original
sub-items against the new deliverable**. Don't let a reframing absorb sub-items
without naming each one. The conflation failure mode in
[references/failure-modes.md](references/failure-modes.md) is exactly this.

Before locking the tests list, also scan it through the three-question
checklist in [references/failure-modes.md](references/failure-modes.md) →
**Test proliferation**. Subagents authoring tests under tight scopes often
produce substring-greps on artefacts, constant echoes that pin what `import`
already enforces, or branching-by-mock-choreography — all of which look
like coverage but pin implementation, not behaviour.

### Phase 7 — Archive

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
- **Test proliferation.** Substring-greps on artefacts, constant echoes,
  and branching-by-mock-choreography — the three shapes catalogued in
  [references/failure-modes.md](references/failure-modes.md). Catch them
  at Phase 6 before they enter the archived audit trail.
- **Copy-the-previous-change drift.** Change N's framing reads "like change
  N-1 but …". That phrasing is the cue to stop and extract an abstraction
  (Phase 2) instead of copying. N-1's incidental choices propagate silently
  otherwise. See [references/failure-modes.md](references/failure-modes.md).
- **Manufactured architecture (Phase 2).** The inverse failure: inventing
  an engine for genuinely independent changes. "No common shape — N
  independent changes" is a valid Phase 2 output. Premature abstraction
  costs more than copy-paste with eyes open.

## Subagent patterns

When delegating per-change work:

**Decomposer** — Phase 1:
> "Read the source at {url} (or `.changes/PROJECT.md` "Source"). Propose 3–7
> change folders; for each: ID slug, one-sentence task, the boundary
> (module/phase/schema) that justifies it as its own change. Don't write the
> folders."

**Architect** — Phase 2:
> "Read `.changes/PROJECT.md`. Propose: 2–4 patterns from
> `references/patterns.md` with one-line fit each; a default shape (engine /
> pipeline / state machine / …) with concrete extension points; numbered
> `A-N` decisions. If shapes don't converge, return *'no common shape'* —
> don't manufacture an engine."

**Framing reviewer** — before execution:
> "Read `.changes/active/{N-slug}/description.md` and `validation.md`. For
> each description sub-item, identify where validation covers it. If
> `PROJECT.md` has an Architecture section, also flag locked decisions that
> neither reference an `A-N` nor record an explicit deviation. List gaps,
> don't fix them."

**Close-out reviewer** — Phase 6:
> "Read `.changes/active/{N-slug}/`. For each original description sub-item,
> state: landed / landed differently / deferred. Flag sub-items checked off
> in tasks.md but unaddressed in the validation pass, and any `A-N` the
> change went off-shape from without recording the deviation."
