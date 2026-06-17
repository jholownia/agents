<!-- markdownlint-disable MD033 -->

# Validation — {N-slug}

## Scope

**In scope:**
<!--
  Specific deliverables. Files, migrations, test additions. Each bullet is one
  concrete artefact or behavioural change.
-->

- <deliverable 1>
- <deliverable 2>

**Out of scope:**
<!--
  Explicit exclusions. Name the SPECIFIC thing excluded, not a category.
  "Out of scope" lines are load-bearing — they must not silently absorb
  sub-items that should be in scope.

  Bad:  - "<table> is out of scope"
  Good: - "DDL changes to <table> — populating existing columns is in scope, schema changes are not"
-->

- <exclusion 1, with the specific thing named>
- <exclusion 2>

**Removed:**
<!--
  OPTIONAL. For changes that delete things, enumerate them explicitly:
  one line per deletion with a reason. Mirrors "Out of scope" but for
  things that existed and now don't. Catches deletion intent the diff
  alone doesn't justify. Skip this subsection if nothing is being removed.
-->

- <what's being deleted>: <one-line reason>

## Decisions (locked)

<!--
  Non-obvious calls made during framing. Numbered as D-N so they can be
  referenced from elsewhere (`per D-3`), from code (`# implements D-3`),
  and from tests (`test_d3_*`). The number stays stable even if other
  items renumber.

  One line of rationale each. If rationale is long, put it in impact.md
  or design.md and link from here.

  A locked decision is a commitment. If it starts to look wrong during
  execution, surface it to the user — don't flip silently.

  If PROJECT.md has an Architecture section, reference its A-N decisions
  explicitly: `per A-2` for in-shape choices, or `deviates from A-2
  because …` for explicit deviation. Silent drift is the failure mode
  the architecture pass exists to prevent.

  For design.md-grade changes, see references/framing.md for the optional
  3-column table form.
-->

- **D-1** — <decision>. <one-line rationale>
- **D-2** — <decision>. <one-line rationale>

## Tests (automated)

<!--
  One line per test, naming the file and the invariant it asserts.

  Before locking this list, scan it through the three-question checklist
  in references/failure-modes.md → Test proliferation. A change with 5
  contract-pinning tests + 1 integration smoke is healthier than 15 tests
  across the antipatterns named there (string-grep on artefacts,
  shape-of-constant echoes, branching-by-mock-choreography).
-->

- `T1` — `<file>::<test>` — <invariant being asserted>
- `T2` — ...

## Manual checks

<!--
  Commands to run, queries to eyeball, data shapes to verify. Numbered.

  For changes that materially alter database writes, include a post-deploy
  data-shape check (M*) that inspects the resulting state. Cheap and catches
  blind spots within a day of deploy.
-->

- `M1` — <command or query>
- `M2` — ...

## Success criteria

<!--
  What must be true for the change to count as done. Each criterion must be
  checkable against the artifacts the change produced. Avoid criteria that
  rely on opinion ("the code is clean") or trust ("user is happy").

  For any "behavior unchanged" claim here, an assertion in Tests should
  prove it.
-->

- <criterion 1>
- <criterion 2>
