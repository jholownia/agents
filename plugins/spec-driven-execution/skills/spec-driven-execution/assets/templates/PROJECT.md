# Project context

<!--
  Umbrella context for this batch of work. Fill in the sections below; omit
  any that are empty for your project. Aim for ~50–150 lines total — anything
  longer probably belongs in a specific change's description.md.
-->

## Source

<!--
  Verbatim source of the work. If it's a GitHub issue:
    - Issue URL
    - Issue title
    - Issue body (raw — don't paraphrase)
  If it's a freeform request:
    - The restated goal you confirmed with the user
    - Date of the conversation
-->

## Authoritative external context

<!--
  Pointers to the load-bearing external documents that govern this work.
  Examples:
    - Spec repo paths (with section numbers)
    - Design docs (with links)
    - Architecture overviews
    - Slack threads or meeting notes that contain locked decisions
-->

## Active changes and their mapping

<!--
  Table mapping change folders to subissues or sub-tasks.

| folder | issue / sub-task | linked | status |
| --- | --- | --- | --- |
| `active/1-foo` | Subtask A | #N | in progress |
| `active/2-bar` | Subtask B | #M | not started |
| `archive/0-pre-protocol-work` | initial spike | — | archived |
-->

## Scope boundaries

<!--
  Quoted clarifications from the user / issue / external context. What's in
  this batch, what's adjacent but explicitly excluded.

  - "user clarified: <quoted clarification with exact scope>"
  - <what's in> — <which folders cover it>
  - <what's adjacent but out> — <one-line reason>
-->

## What's left

<!--
  Status snapshot of the batch as a whole. Updated as folders archive.

  - **#N (1-foo)** — archived. <one-line outcome>
  - **#M (2-bar)** — in progress. <one-line state>
  - **#K (3-baz)** — not started.
-->

## For dispatched agents

When picking up a change, read in order:

1. `.changes/CLAUDE.md` — the workflow protocol
2. `.changes/PROJECT.md` — this file
3. `.changes/active/{change-id}/description.md` — task + context pointers
4. `.changes/active/{change-id}/validation.md` — scope, locked decisions, checks
5. The specs paths and codebase files listed in the change's Context section

Open decisions in a change's `validation.md` are load-bearing — do not
re-litigate silently. If a decision looks wrong, surface it to the user rather
than flipping it.
