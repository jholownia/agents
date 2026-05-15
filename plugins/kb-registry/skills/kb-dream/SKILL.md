---
name: kb-dream
description: >
  Use when asked to consolidate, organize, compile, dream over, or maintain a
  kb-registry knowledge base. Turns staged inbox notes into KB-specific
  canonical knowledge using the KB's own AGENTS.md, BRIEF.md, INDEX.md, and
  existing structure instead of imposing a global taxonomy.
---

# KB Dream

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

Ignore notes that are redundant, too raw, unsafe, or not worth preserving.

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
- update `INDEX.md` when navigation changes
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
kb search <kb> "<representative topic>"
git -C <kb-path> diff --stat
git -C <kb-path> diff
```

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
