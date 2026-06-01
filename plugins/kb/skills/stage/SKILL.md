---
name: stage
description: This skill should be used when the user asks to "add/document/save/write this up in <kb>", "save this article/URL to <kb>", "stash this for the next dream", "remind me next session about <topic>", "ingest these sources into <kb>", or wants to stage longer notes, text files, URL pointers, directories of files, or follow-up TODOs into a KB's inbox for the next kb-dream pass. For short single-sentence facts use kb:remember.
version: 0.2.0
---

# kb:stage

Stages material into a KB's `inbox/` for the next `kb-dream` consolidation pass. Three shapes — choose by content type.

## Which verb?

| Material | Verb |
|---|---|
| Short single-sentence project fact | `kb remember` (use kb:remember) |
| Longer note / decision worth consolidating | `kb stage --note` |
| A text file to ingest | `kb stage --file` |
| A URL to read and summarise later | `kb stage --url` |
| A follow-up TODO for the next session | `kb stage --kind followup --note "..."` |

## Commands

```bash
kb stage <kb> --note "<text>"                            # agent-written note
kb stage <kb> --kind decision --note "<text>"            # note with explicit kind
kb stage <kb> --kind followup --note "<deferred work>"   # project TODO
kb stage <kb> --file <path>                              # text document, verbatim
kb stage <kb> --url <https://...>                        # URL pointer
kb stage <kb> --url <https://...> --note "<why>"         # URL + description
```

- `--file` is mutex with `--note` and `--url`. `--note` may accompany `--url` as a description body.
- URL pointers must be `http://` or `https://`. They are **not fetched at stage time** — `kb-dream` resolves them during consolidation.
- Note kinds: `decision`, `domain-fact`, `codebase-fact`, `runbook-note`, `retrospective`, `followup`, `raw-note` (default).
- All stages auto-commit to `inbox/`.

Manual drag-and-drop of a Markdown file into `inbox/` produces the same shape as `--file` and is a first-class path.

Full details: `${CLAUDE_PLUGIN_ROOT}/references/commands.md` and `${CLAUDE_PLUGIN_ROOT}/references/kb-contract.md`.
