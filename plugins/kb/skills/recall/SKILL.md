---
name: recall
description: >
  Retrieve facts, decisions, or knowledge from a registered KB, or
  list what's still pending consolidation. Triggers: "what did we
  decide about X", "what do we know about Y", "last session we
  discussed Z", "what's pending in <kb>", "what's in <kb>'s inbox",
  "show me the dream log".
---

# kb:recall

The primary skill for "what do we know about X" questions, plus the inspection verb for what's still sitting in the inbox.

## Retrieval order (progressive disclosure)

1. `kb list` *(via kb:info)* — discover which KBs exist.
2. `kb brief <kb>` *(via kb:info)* — read scope before searching.
3. `kb pending [<kb>]` — what's unprocessed in the inbox (useful when picking up a session).
4. `kb recall [<kb>] --query "<text>"` — search synthesised material (`notes/` + `knowledge/`).
5. `kb recall [<kb>] --tag <tag>` — list notes carrying a tag.
6. `kb search <kb> "<query>"` — widen to include raw `inbox/`.
7. `kb open <kb> <path>` — read a specific file once you know the path.
8. Direct repo inspection only if the KB is insufficient.

## Search tokenization

`kb recall --query` and `kb search` are **lexical** (`rg`-backed) and treat the query as a regex pattern. A quoted multi-word phrase must match exactly — if a phrase returns zero results, retry with single keywords or two-token slices. Defaults: 20 total results / 3 matches per file.

## Commands

```bash
kb recall [<kb>] --query "<text>" [--max-results N]
kb recall [<kb>] --tag <tag>
kb pending [<kb>]                    # unprocessed inbox material
kb search <kb> "<query>"             # wider net (includes inbox)
kb open <kb> <relative/path>
```

`recall` searches `notes/` and `knowledge/`, excluding the raw `inbox/`. Use `search` when you specifically need raw material. Use `pending` to see what's queued for the next dream pass.

### Looking at consolidation history

`kb-dream` records each pass in `LOG.md` at the KB root. To see what was consolidated when, what was superseded, and open follow-up questions:

```bash
kb open <kb> LOG.md
```

Full flag reference: `${CLAUDE_PLUGIN_ROOT}/references/commands.md`.
