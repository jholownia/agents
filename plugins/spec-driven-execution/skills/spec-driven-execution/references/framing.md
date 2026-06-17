# Framing a change

How to write `description.md`, `validation.md`, and `tasks.md` for a single
change folder. Plus when to add the optional files.

## `description.md` (required)

Two sections.

### Task

The statement verbatim from the source — issue subitem, user request,
clarification. Include the reference (`Source: #291`, or
`Source: conversation 2026-05-14`).

**Rule:** do not paraphrase. Paraphrasing silently loses scope. If the original
is ambiguous, quote it *and* add your interpretation as a separate "Interpretation"
sub-bullet, so the gap is visible.

### Context

Bullet pointers a fresh agent needs to pick this up cold:

- Source issue URL and any linked subissues.
- Relevant specs paths and section numbers.
- Key files in the current codebase that will be read or changed (full paths).
- Related changes in `.changes/active/` or `.changes/archive/` (by ID).
- Schema or data shape that's load-bearing for the change.

This section is for orientation, not narrative. If a bullet needs more than
two sentences, it probably belongs in `design.md`.

## `validation.md` (required)

The contract the change must satisfy. Written during framing, updated only when
scope or decisions genuinely change.

Sections, in order:

### Scope

- **In scope:** specific deliverables. Files, migrations, test additions.
- **Out of scope:** explicit exclusions. Adjacent things that look like they
  should be in scope but aren't.

**Rule:** explicit exclusions matter as much as inclusions. "Out of scope" lines
prevent silent scope creep. They also prevent the inverse — silent under-delivery
where a sub-item gets conflated with an exclusion.

When excluding something, name the *specific* thing excluded. Not "`<table>`
is out of scope" — say "*DDL changes* to `<table>` are out of scope;
*populating existing columns* is not."

### Decisions (locked)

Non-obvious calls made during framing, each with a one-line rationale.

- Number them as **D-1, D-2, …** so they can be referenced from elsewhere
  (`per D-3`), from code (`# implements D-3`), and from tests
  (`test_d3_*`). The number stays stable even if other items renumber.
- One line of rationale per decision. If the reasoning is long, put it in
  `impact.md` or `design.md` and link from here.
- A locked decision is a commitment to a specific reading. If it starts to
  look wrong during execution, surface it to the user — don't flip silently.
- If the batch has an Architecture section in `PROJECT.md`, reference its
  decisions explicitly: `per A-2` for in-shape changes, or
  `deviates from A-2 because …` for explicit deviation. Silent drift is
  the failure mode that the architecture pass exists to prevent — see
  [architecture.md](architecture.md) and `failure-modes.md` →
  *Copy-the-previous-change drift*.

For changes with `design.md` (architectural weight), consider the 3-column
table form — it forces resolution and rationale apart, makes each decision
visible at a glance, and lets you mark "needs external input" directly in
the Resolution cell:

```markdown
|#|Decision|Resolution|Rationale|
|---|---|---|---|
|D-1|Notification↔incident mult.|1:N, enforced by PK|No concrete N:M scenario exists.|
|D-2|Equality predicate on relabel|Two-pass: same-label, then any|Recording old → new is better audit.|
```

Bullet form remains the lightweight default — use the table when the change
already has enough weight to justify `design.md`.

### Tests (automated)

One line per test, naming the file and the invariant.

```
- T1 — tests/integration/foo.py::test_bar — asserts X under condition Y.
```

### Manual checks

Commands to run, queries to eyeball, data shapes to verify. Numbered (`M1`,
`M2`…) so they can be referenced in close-out.

### Success criteria

What must be true for the change to count as done. Each criterion should be
checkable against the artifacts the change produced.

## `tasks.md` (required)

Flat implementation checklist. Checkbox format, imperative mood. Implementation
only — checks live in `validation.md`.

```markdown
- [ ] Write migration 015_backfill_x.sql
- [ ] Update src/services/y.py to pass `new_column` through
- [ ] Update fixtures in tests/integration/test_y.py
- [ ] Run all checks in validation.md
```

This is the persistent version of `TodoWrite` across sessions. Update in place
as understanding shifts. Don't backfill checked items that landed differently —
edit the item to match what actually happened, then check it.

## Optional files

When to add each:

| File | When |
|---|---|
| `proposal.md` | The solution is non-obvious or contested. One paragraph on approach, one on why (with alternatives explicitly ruled out). |
| `design.md` | The change has architectural weight — new modules, schema redesigns, protocol changes. Covers shape, key tradeoffs, rejected alternatives. |
| `impact.md` | The change reaches across modules / schemas / infra. Bullet list of affected code, schemas, tests, tooling, plus dependencies on/from other changes. |

`design.md` almost always implies `impact.md`. Skip all three for mechanical
changes (a deletion, a one-file rename, a config bump).

## Conventions

- Reference issue numbers and spec paths liberally — they're the authoritative
  sources, your files are the working notes.
- Update files in place. Don't accumulate stale drafts.
- Never lock a non-obvious decision without surfacing it to the user first with
  a recommended default.
- If a change grows beyond its original scope, split into a sibling folder
  rather than ballooning the existing one.
- Don't write code before `description.md` and `validation.md` exist. Framing
  written after the fact is rationalization.

## Worked example

Once you have changes archived under `.changes/archive/`, those folders are
your canonical examples — especially any change that went through mid-flight
reframing. Read `validation.md` in those to see how scope and locked decisions
interact in practice.
