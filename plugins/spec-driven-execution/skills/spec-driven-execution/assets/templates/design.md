<!-- markdownlint-disable MD033 -->

# Design — {N-slug}

<!--
  Write design.md when the change has architectural weight: new modules,
  schema redesigns, protocol changes, cross-service contracts.

  This is the deeper technical design, not the framing. Framing lives in
  description.md and validation.md.

  design.md almost always implies impact.md.
-->

## Shape

<!--
  The high-level shape of the design. Data flow, module boundaries, transaction
  boundaries, state machines. Diagrams or pseudocode welcome.
-->

## Key tradeoffs

<!--
  The decisions that shaped the design. For each, name the alternative, the
  chosen path, and the reasoning.

  ### <decision area>

  - Considered: <option A>, <option B>, <option C>
  - Chose: <option B>
  - Why: <one-paragraph reasoning>
-->

## Invariants

<!--
  Invariants the design preserves or establishes. Numbered as I-N so they
  can be referenced from code (`# enforces I-3`) and tests
  (`test_i3_active_incidents_dont_overlap`). The numbering stays stable;
  retire an invariant by striking through, not renumbering.

  Each invariant should be assertable — ideally backed by a test in
  validation.md.
-->

- **I-1** — <invariant>.
- **I-2** — <invariant>.

## Forward compatibility

<!--
  OPTIONAL. One paragraph. What's the next-likely future work this design
  needs to survive? Where would it break under that next step? What does
  it cost to keep that option open today?

  The test for a design is whether the next anticipated extension requires
  significant rework. If yes, name what would have to change. Surfaces
  "we'd lock ourselves out of X" before it becomes a problem.
-->

## Failure modes

<!--
  Known ways this design could fail, and how it handles them.
-->

## Phase summary

<!--
  OPTIONAL. Only for changes that include a multi-phase rollout or
  migration plan. Compact, scan-friendly, makes rollback strategy
  explicit per phase.

  |Phase|Deploys|Reversible by|Gate to proceed|
  |---|---|---|---|
  |1|<what ships>|<rollback mechanism>|<what must be true to move to phase 2>|
  |2|...|...|...|
-->

## Rejected alternatives

<!--
  Approaches that were considered and ruled out. One paragraph each. Future
  readers will appreciate knowing this work was done.
-->
