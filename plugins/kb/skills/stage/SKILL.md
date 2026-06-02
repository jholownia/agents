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
| A text file to ingest | `kb stage --file <path>` |
| A directory of mixed sources | `kb stage --dir <path>` |
| A PDF / DOCX / PPTX / XLSX / EPUB / HTML | `kb stage --file <path>` (auto-extracts) |
| A URL to read and summarise later | `kb stage --url` |
| A follow-up TODO for the next session | `kb stage --kind followup --note "..."` |

## Commands

```bash
kb stage <kb> --note "<text>"                            # agent-written note
kb stage <kb> --kind decision --note "<text>"            # note with explicit kind
kb stage <kb> --kind followup --note "<deferred work>"   # project TODO
kb stage <kb> --file <path>                              # text or extractable file
kb stage <kb> --file <path.pdf> --keep-source            # also copy original to sources/
kb stage <kb> --dir <path>                               # bulk-stage a directory
kb stage <kb> --url <https://...>                        # URL pointer
kb stage <kb> --url <https://...> --note "<why>"         # URL + description
```

- `--file`, `--dir`, and `--url` are mutex with each other. `--note` may accompany `--url` as a description body.
- URL pointers must be `http://` or `https://`. They are **not fetched at stage time** — `kb-dream` resolves them during consolidation.
- Note kinds: free-form. Suggested: `decision`, `domain-fact`, `codebase-fact`, `runbook-note`, `retrospective`, `followup`, `raw-note` (default).
- All stages auto-commit to `inbox/`.

## Binary documents (PDFs, Office, EPUB, HTML)

When given a PDF (or `.docx` / `.pptx` / `.xlsx` / `.epub` / `.html`), extract to Markdown if available, stage the extracted text, preserve provenance, and only keep the binary when explicitly useful.

- **Default**: `kb stage --file foo.pdf` runs `markitdown foo.pdf`, writes the extracted text into `inbox/...md` with `extracted_from`, `extractor`, and `kind: extracted` frontmatter, **drops the binary**. KB stays git-friendly. Same for `--dir`: every extractable file in the tree converts in-place; verbatim copies handle the `.md`/`.txt` peers.
- **Opt-in `--keep-source`**: also copies the original to `sources/<YYYY>/<MM>/<basename>.pdf` and adds a `source:` pointer in the extracted file's frontmatter. Use when the source matters: visual layout (slides, diagrams), reference docs you may re-extract with a better tool, scanned PDFs you may OCR later.
- **No markitdown installed**: `kb stage --file foo.pdf` errors with an install hint (`pip install markitdown`). `kb stage --dir <path>` skips extractable files with the same hint and surfaces a count in the summary; the text files in the tree still ingest normally.

When **not** to keep the source:
- Chat exports, blog post PDFs, plain prose reports — the extracted text *is* the content.

When to keep the source:
- Books or technical docs with figures/tables markitdown can't perfectly render.
- Materials you might want to re-extract with a better tool later.
- Anything you'd manually want to open in its original form.

Manual drag-and-drop of a Markdown file into `inbox/` still produces the same shape as `--file` and is a first-class path.

Full details: `${CLAUDE_PLUGIN_ROOT}/references/commands.md` and `${CLAUDE_PLUGIN_ROOT}/references/kb-contract.md`.
