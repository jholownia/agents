# Impact — {N-slug}

<!--
  Write impact.md when the change reaches across modules, schemas, or infra.
  Bullet list of affected surfaces. design.md almost always implies this file.
-->

## Files added

- `<path>` — <one-line purpose>

## Files affected

- `<path>:<line>` — <what changes and why>

## Schema / data

<!--
  Tables, columns, indexes touched. Migrations applied.
-->

- `<migration file>` — <one-line description>
- `<schema.table.column>` — <added / modified / removed>

## Tests

<!--
  Test files added, modified, or deleted. Fixtures touched.
-->

## Tooling / infra

<!--
  CI, CDK, lambdas, dashboards, anything outside the main codebase that needs
  updating in coordination with this change.
-->

## Dependencies on other changes

<!--
  Other change folders this one depends on (must land first) or unblocks (will
  land after).
-->

- **Depends on:** `<change-id>` — <why>
- **Unblocks:** `<change-id>` — <why>

## Risk

<!--
  Honest assessment of what could go wrong. Don't write "low risk" without
  saying why.
-->

## Rollback plan

<!--
  Only if the change is hard to reverse (schema changes, data migrations,
  config changes that affect prod). Omit for code-only changes that can be
  reverted by reverting the commit.
-->
