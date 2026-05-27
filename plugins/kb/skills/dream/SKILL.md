---
name: dream
description: >
  Consolidate a KB's inbox into canonical knowledge/ pages. Dry-run-
  first: produces a plan before any apply. Triggers: "consolidate <kb>",
  "compile the inbox for <kb>", "organise <kb>", "dream pass on <kb>".
---

# kb:dream

## Purpose

Consolidate staged inbox material into durable canonical knowledge.

This is an agent judgment workflow, not a deterministic file-moving script. The
registry supplies safe access and staging commands; the KB owns its internal
organization.

## When to use

- The user asks to dream, consolidate, organize, compile, or maintain a KB.
- Inbox notes have accumulated and should be turned into canonical knowledge.
- A KB's `BRIEF.md`, `INDEX.md`, or `knowledge/` structure needs updating after staged discoveries.

## Operating rules

1. Read the KB's local rules first: `AGENTS.md`, `BRIEF.md`, `INDEX.md`, and `LOG.md` if present.
2. Inspect the existing `knowledge/` structure before proposing new files.
3. Treat `inbox/` as source material, not as final knowledge.
4. Preserve provenance by linking or naming consumed inbox/source files in canonical pages or `LOG.md`.
5. Keep canonical pages concise, synthesized, and durable.
6. Do not import transcripts, duplicate raw notes, secrets, or one-off noise.
7. Prefer the KB's existing organization over a generic taxonomy.
8. **Prefer updating an existing canonical page over creating a new one.** Duplication is the primary failure mode this workflow exists to prevent — search the KB before creating.
9. **Replace, don't accrete.** When a new note contradicts an existing canonical claim, replace the old claim and append a supersession entry to `LOG.md` referencing both paths. Use `supersedes:` frontmatter on the rewritten page when the prior version lived in `knowledge/`.
10. Present a dry-run plan before canonical edits unless the user explicitly asked to apply.

## Workflow

### 1. Orient

Use the CLI and direct KB file reads sparingly:

```bash
kb list
kb brief <kb>
kb status <kb>
```

Then inspect:

```text
AGENTS.md
INDEX.md
LOG.md
knowledge/
inbox/
```

### 2. Select inbox material

Identify candidate inbox notes. Prefer recent unprocessed material and notes with durable kinds:

- `decision`
- `domain-fact`
- `codebase-fact`
- `runbook-note`
- `retrospective`
- `url` — see step 2a

Ignore notes that are redundant, too raw, unsafe, or not worth preserving.

### 2a. Resolve URL pointers

For notes with `kind: url` (frontmatter contains `url: <https://...>`):

1. Fetch the URL. Prefer the `defuddle` skill for HTML articles (returns clean Markdown); fall back to WebFetch for everything else.
2. If the fetch fails (404, paywall, dead link), record the failure in `LOG.md` and leave the pointer in the inbox; do not delete it.
3. Synthesise the fetched content into a canonical page under `knowledge/` like any other source. Cite the URL in the page's provenance section.
4. Once consolidated, mark the URL note processed (move to `inbox/processed/` per the default convention) and reference the resulting canonical page in `LOG.md`.

Treat any agent-supplied description body on a URL pointer as a hint about why the link was saved — useful for choosing the canonical page's framing.

### 3. Search for existing coverage

Before creating or changing canonical pages, search the KB:

```bash
kb search <kb> "<topic>"
```

Update existing pages when they are the natural home. Create new pages only when the knowledge has no good home.

### 4. Propose a dry run

Summarize:

- inbox notes to consume
- canonical pages to create or update
- `INDEX.md`, `BRIEF.md`, or `LOG.md` changes
- unresolved questions
- material intentionally left in inbox

Stop here unless the user asked to apply directly.

### 5. Apply

When approved, edit the KB directly:

- write synthesized pages under `knowledge/`
- update `INDEX.md` by hand when navigation changes (semantic groupings are a curation task, not a generation task)
- run `kb reindex <kb> --dry-run` after the writing cluster to check the generated manifest before committing canonical changes; rebuild with plain `kb reindex <kb>` once the content changes are settled
- update `BRIEF.md` only when scope/key areas changed
- stamp `last_reviewed: <ISO date>` in the frontmatter of any canonical page you touched
- when a new note contradicts an existing canonical claim, **replace the old claim** and append a supersession entry to `LOG.md` listing both the consumed inbox note and the prior canonical claim (interference, not silent rewrite)
- append a short entry to `LOG.md` summarising what was consumed
- mark consumed inbox notes as processed or move them under `inbox/processed/`

Use the KB's own conventions if they differ from this default.

### 6. Validate

Run:

```bash
kb status <kb>
kb reindex <kb> --dry-run
kb search <kb> "<representative topic>"
git -C <kb-path> diff --stat
git -C <kb-path> diff
```

`kb reindex --dry-run` reports how many entries would land in `index.json` and whether anything changed. Run plain `kb reindex <kb>` once the canonical pages are settled, so downstream recall can use the refreshed manifest.

Review the diff for overbroad rewrites, invented facts, lost provenance, and accidental raw transcript import.

### 7. Commit

If the KB is cleanly updated and the user wants the change kept, commit in the KB repo:

```bash
git -C <kb-path> add -A
git -C <kb-path> commit -m "kb: dream inbox notes"
```

Do not push unless asked or the KB workflow says to sync.

## Default processed-note handling

If the KB has no stronger convention:

- move consumed notes to `inbox/processed/YYYY/MM/`
- preserve filenames
- append a `Processed` section to each note before moving:
  - date
  - canonical page path(s)
  - brief consolidation summary

Do not delete inbox notes in v0.
