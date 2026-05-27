# Failure modes

Observed ways this protocol breaks, with the practice that prevents each.

## Compound sub-items hiding under one bullet

The most common failure.

### What happens

A framing bullet contains two semantically distinct sub-tasks joined by "and"
or "or":

> "Decide per-table: rename `old_column` → `new_column` (cleanest, follow-up
> migration) **or** leave the column and make sure every caller treats it as a
> `new_column`."

The thread's scope reframes mid-flight (the live audit premise turns out wrong,
say). The close-out resolves the *new* deliverable — but the original bullet
gets ticked off as a single unit, even though only one of the two sub-tasks
actually landed. The other silently falls off.

A worked case: the rename is correctly deemed unnecessary, and the close-out
records *"both legacy and out-of-scope per user clarification"*. But the
writer-side audit ("make every caller treat it as a `new_column`") was never
executed. New rows continue being written with `old_column=0` post-deploy,
exactly as before — because the conflation swept the writer audit under the
same "out of scope" flag that legitimately covered only the rename.

### How to prevent it

1. **At framing time:** split compound bullets. Two distinct sub-tasks get
   two bullets. The pattern "A *or* B" almost always indicates two items;
   "A *and* B" almost always indicates two items. Make them visible.
2. **At reframing time:** when a thread's scope changes mid-flight, re-enumerate
   the *original* sub-items against the *new* deliverable. Don't let a
   reframing absorb sub-items wholesale.
3. **At close-out time:** the close-out reviewer pattern in `SKILL.md`. For
   each original sub-item, state explicitly whether it landed, landed
   differently, or was deferred. A "deferred" sub-item is recorded as such; it
   doesn't disappear into the archived `validation.md`.

## Paraphrased user clarifications

### What happens

A clarification gets recorded as "out of scope per user" or "confirmed by user"
without the exact scope of the clarification. Later readers (often the same
agent in a different session) interpret the recorded paraphrase more broadly
than the user intended.

Continuing the example above: the user clarifies that the legacy interface
tables won't get a schema rename. This gets recorded as *"legacy interface
tables out-of-scope per user clarification"* — which the next reader
interprets as "don't touch those tables at all", including the writer paths.

### How to prevent it

Quote clarifications. Include the exact scope.

- Bad: *"out of scope per user clarification"*
- Better: *"user clarified: no schema rename on legacy interface tables"*
- Best: *"user clarified: 'we don't need a rename migration, the writer side is
  the part that matters' (scope: column rename only; writer audit remains in scope)"*

The third form survives reinterpretation across sessions because the scope is
explicit, not inferred from the surrounding paragraph.

## No assertion behind a "behavior unchanged" claim

### What happens

A change claims to leave some behavior unchanged ("the writer already produces
the right value", "this is a pure refactor"). Nothing in the codebase actually
asserts that the unchanged behavior holds. The claim is process discipline, not
test discipline. Process discipline degrades; test discipline doesn't.

### How to prevent it

For any "intended behavior unchanged" claim in `validation.md`, add an
assertion that proves it.

- "Column X must remain populated with the intended value for all new writes" →
  integration test that asserts the value, not just the column shape.
- "Refactor preserves the public API" → golden file diff over a real call set.

This is the symmetric form of the rule that says "for any code path you change,
write the test that proves the new behavior". Both halves matter — invariants
deserve assertions as much as changes do.

## Post-deploy data-shape blind spot

### What happens

A change lands. Tests pass. Deploy succeeds. The actual *data* — what got
written, what got migrated, what stayed at default values — is never inspected.
Months later someone notices an entire column is structurally a default value.

The gap is specifically between **what tests cover** and **what production
produces**. Tests seed their own data and assert against shapes the author
already had in mind. They don't catch the case where production is missing a
data shape the author never considered (a writer that's still pinned to
zero, a migration that found ten thousand more eligible rows than the
test fixture had, a default value that the seed never exercised).

### When to add a post-deploy data-shape check

Add an `M*` check to `validation.md` whenever any of these are true:

- A column the change is supposed to populate has a default value that would
  also be a *plausible* legitimate value (`0`, `NULL`, `false`, `''`). Default-
  collision is the failure mode that hides longest.
- The change includes a backfill migration. Backfills should be verifiable by
  count, not just by spot-checking.
- The change is a writer rewire where the old writer and the new writer can
  produce the same shape under different code paths (the "writer pinned to
  zero" case). A green test suite proves the new code path *can* produce the
  intended value; only production proves it *does* produce it for every row.
- The change alters what a downstream system reads (downstream contract).
  Production data is the only place the contract is actually exercised.

Skip the check for pure refactors with no write semantics, for read-only
changes, or for changes where the column being written has a value that
couldn't plausibly collide with any default (UUIDs, timestamps, free text).

### What the check should look like

A single SQL query you can paste into the `/db-query` skill or a database
console. Two parts: a count, and an expectation tied to the change's scope.

```
- M5 — post-deploy: SELECT COUNT(*) FROM <table> WHERE <new_column> = 0
  AND created_at > '<deploy-timestamp>';
  Expected: 0 for rows that match the change's primary scope; non-zero only
  for the explicitly excluded cases (per decision #N).
```

The expectation must reference the change's scope — "expected 0 unless"
forces the reviewer to think about which exclusions in `validation.md` would
explain a non-zero result, and surfaces drift if a new exclusion appeared
mid-flight that the check doesn't account for.

### When to run it

Within 24 hours of deploy is the sweet spot. Late enough that real production
traffic has generated meaningful row counts, early enough that a rollback is
still cheap if the check fails.

Don't defer this check to "the next time someone happens to look at the
table". The whole point of the failure mode is that nobody ever happens to
look. Put a calendar reminder on it.

### Why this fails the natural way

Without the check, the failure mode is silent for as long as nobody happens
to query the column with a `WHERE column != <default>` filter. In a real
case this skill was built from, a column stayed structurally zero for two
years before anyone noticed. Tests passed every CI run. Deploys succeeded
every release. The data was wrong the entire time.

The check is cheap, takes seconds, and would have caught that case within a
day of the first deploy that was supposed to populate the column — including
the original integration that introduced the placeholder.

## Skipping framing

### What happens

Code gets written, then `description.md` and `validation.md` are written
*from* the code. The contract is rationalization, not framing. Decisions that
should have been surfaced to the user get locked silently because they're
already implemented.

### How to prevent it

The protocol's order is load-bearing: Frame → Plan → Execute, not Execute →
Frame. If you find yourself writing framing files after the code exists, treat
the framing as a *review* rather than a contract: be explicit that the
decisions documented in it are post-hoc, and re-surface any non-obvious ones to
the user as "I made this call already — is that OK?"

## Editing archived changes

### What happens

A reader discovers an archived change had a flawed decision. They edit the
archived `validation.md` to "fix" it. The audit trail now lies about what was
decided when.

### How to prevent it

Archived changes are frozen. If the world moved, write a *new* change that
references the archived one and either supersedes a decision or extends the
work. The archive is the decision history; tampering with history is the failure.

## One huge change folder

### What happens

A folder's `tasks.md` grows past ~30 items. `description.md` past ~150 lines.
The scope expanded; the framing didn't split. The folder is now too big to
review as one unit and too coupled to halt cleanly mid-flight.

### How to prevent it

When `tasks.md` crosses ~20 items, ask: is this still one change, or did it
become two? Split into sibling folders (`5a-foo`, `5b-bar`, or just `6-bar`).
The original folder retains its identity; the new sibling captures the
overflow.
