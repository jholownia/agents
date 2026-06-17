# Change Protocol

Structured workflow for proposing, validating, and archiving non-trivial
changes for this batch of work. Loosely modelled on OpenSpec.

This directory may be gitignored (personal working space) or committed (team
audit trail) — see `PROJECT.md` for which.

Each change folder is **self-contained**: a fresh agent dispatched against
`active/{change-id}/` should be able to pick it up cold. Framing files carry
their own pointers to source material.

Umbrella context for the current batch of work (what we're building, which
issue, where the specs live) is in [`PROJECT.md`](PROJECT.md). Read that before
entering a specific change folder.

## Directory structure

```
active/
└── {N-slug}/            # In-flight changes
    ├── description.md   # REQUIRED — task statement + context pointers
    ├── validation.md    # REQUIRED — scope, locked decisions, checks, success criteria
    ├── tasks.md         # REQUIRED — implementation checklist (not validation)
    ├── proposal.md      # OPTIONAL — see matrix below
    ├── design.md        # OPTIONAL
    └── impact.md        # OPTIONAL

archive/
└── {N-slug}/            # Completed changes — frozen, the decision record
```

## Change ID format

Short, grep-friendly slug prefixed with a local ordering number: `1-schema-migration`,
`2-service-rewrite`, …

Numbering is local to this branch only — collisions across branches are
resolved manually on merge.

## Workflow

The steps below are **per-change**. (If the `spec-driven-execution` skill is
driving, its phase table also covers scaffolding, decomposition, and the
upfront architecture pass: skill Phase 3 = steps 0–1 here, Phases 4–7 =
steps 2–5. Phase 2 (architecture pass) is per-batch, not per-change — its
output lives in `PROJECT.md`'s Architecture section (or a sibling
`ARCHITECTURE.md`) and the per-change `validation.md` references its
`A-N` decisions.)

0. **Context** — before framing, gather enough ground to know what "done" looks
   like. Read the source issue and any linked subissues. Read the relevant
   specs sections (with file paths). Inspect the current state of the code or
   schema being changed. Identify the delta between current and target.
   Surface open decisions and a recommended default for each; do not lock
   decisions silently.
1. **Frame** — write `description.md` (task statement + context pointers from
   step 0) and `validation.md` (scope, locked decisions after the user
   confirms defaults, then tests / manual checks / success criteria). Do this
   *before* writing any production code.
2. **Plan** — fill in `tasks.md` with implementation steps only. Add
   `proposal.md` / `design.md` / `impact.md` per the matrix below if the change
   warrants them.
3. **Execute** — work the checklist; update it in place as understanding shifts.
   Update `validation.md` if scope or decisions genuinely change (not routinely).
4. **Validate** — run the checks in `validation.md`. For each sub-item in
   `description.md`, name it and state explicitly whether it landed, landed
   differently, or was deferred. Don't let mid-flight reframing absorb sub-items
   silently.
5. **Archive** — move `active/{change-id}/` → `archive/{change-id}/`. The
   archived folder becomes the frozen decision record.

## File contents

### `description.md` (required)

Two sections:

- **Task** — the statement verbatim from the issue/subissue. Include the issue
  reference (e.g. `Source: #290`). Do not paraphrase unless the original is
  ambiguous (and then quote it, with your interpretation as a separate
  sub-bullet).
- **Context** — bullet pointers a fresh agent needs to pick this up cold:
  - Source issue URL and any linked subissues
  - Relevant specs paths and sections
  - Key files in the current codebase that will be read or changed (full paths)
  - Related changes in `active/` or `archive/` (by ID)

### `validation.md` (required)

The contract the change must satisfy. Sections, in order:

- **Scope** — what's in, what's out. Explicit exclusions matter as much as
  inclusions. Name the *specific* thing excluded; "out of scope" lines are
  load-bearing and must not silently cover sub-items that should be in scope.
- **Decisions (locked)** — non-obvious calls made during Context/Frame, with
  the reasoning in one line each. Numbered as **D-1, D-2, …** for stable
  reference from elsewhere in the spec, from code (`# implements D-3`),
  and from tests (`test_d3_*`). If rationale is long, put it in
  `impact.md` or `design.md` and link. Invariants in `design.md` follow
  the same convention with **I-N**. If the batch has an Architecture
  section in `PROJECT.md`, reference its decisions as `per A-N` or record
  deviations explicitly (`deviates from A-2 because …`) — silent drift is
  the failure mode.
- **Tests** — automated checks (new or modified). One line per test, named.
  Before locking the list, scan it for the test-proliferation antipatterns
  (see the anti-patterns section below).
- **Manual checks** — commands to run, diffs to eyeball, data to verify. Numbered.
- **Success criteria** — what must be true for the change to count as done.

`tasks.md` does not duplicate these checks; it references this file.

### `tasks.md` (required)

Flat checklist of **implementation** steps only — files to write, files to
edit, commands to run that produce artefacts. Checkbox format, imperative mood.
Add or remove items as understanding evolves. This is the persistent version
of `TodoWrite` across sessions.

### Optional files — when to add each

- `proposal.md` — solution is non-obvious. One paragraph on approach, one on
  why (alternatives ruled out).
- `design.md` — change has architectural weight (new modules, schema redesigns,
  protocol changes). Covers shape, key tradeoffs, rejected alternatives.
- `impact.md` — change reaches across modules / schemas / infra. Bullet list of
  affected code, schemas, tests, tooling, plus dependencies on/from other changes.

`design.md` almost always implies `impact.md`. Skip all three for mechanical
changes.

## Conventions

- Keep each file tight — this is a working document, not a spec deliverable.
- Update files in place; do not accumulate stale drafts.
- Reference issue numbers and spec paths liberally — they are the
  authoritative sources.
- Never lock a non-obvious decision without surfacing it to the user first
  with a recommended default.
- If a change grows beyond its original scope, split it into a new numbered
  folder rather than ballooning the existing one.
- Split compound bullets at framing time. Two distinct sub-tasks get two
  bullets — never one. The pattern "A *or* B" / "A *and* B" almost always
  signals two items.
- Quote user clarifications with their exact scope. Don't paraphrase "out of
  scope per user" without naming *what specifically* is excluded.
- For any "behavior unchanged" claim in `validation.md`, add an assertion that
  proves it.

## Anti-patterns

- Two sub-items hiding under one bullet — see the conflation failure mode.
- Reframing scope mid-flight without re-enumerating the original sub-items.
- Paraphrasing user clarifications instead of quoting them with exact scope.
- "Behavior unchanged" claims with no assertion behind them.
- Writing framing files after the code already exists.
- Editing archived changes — they're frozen. Write a new change instead.
- One folder growing past ~30 tasks or ~150 lines of description — split.
- **Copy-the-previous-change drift** — framing reading "like change N-1 but …".
  Stop and extract the abstraction (the skill's Phase 2 / `PROJECT.md`
  Architecture section) instead of copy-pasting and diverging silently.
- **Test proliferation.** Three shapes that look like coverage but are
  drift: (1) `assert "..." in <doc/config/prompt>` (string-grep on
  artefacts — passes even when the artefact is broken), (2) `assert
  CONSTANT == "literal"` (re-asserts what `import` already enforces),
  (3) N tests asserting which mock was called for N branches (the
  contract is the action, not the dispatch — parametrise over
  `(input, expected_action)` instead). Before locking the Tests list,
  ask: would deleting this test leave any locked decision unverified?
  Does it pin behaviour at a boundary, or a value in production code?
  Could N of these collapse into one parametrised case?
