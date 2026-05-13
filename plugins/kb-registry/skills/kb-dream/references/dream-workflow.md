# KB Dream Workflow

## Mental model

Inbox material is source code. Canonical `knowledge/` pages are the compiled artifact.

The agent's job is not to mirror inbox files into `knowledge/`. It is to read staged material once, identify durable facts and decisions, and maintain the KB as a compact agent-readable wiki.

## KB-specific structure

Each KB may organize itself differently. Before changing canonical knowledge, read:

- `AGENTS.md` for local rules and schema hints
- `BRIEF.md` for scope and retrieval guidance
- `INDEX.md` for navigation
- existing files under `knowledge/`
- `LOG.md` for prior maintenance decisions

If these disagree, prefer `AGENTS.md` and the existing `knowledge/` structure. Surface the mismatch in the dry-run plan.

## Dry-run output shape

Use this structure:

```markdown
## Dream Plan

### Inbox Notes

- `inbox/2026/05/example.md` — consume into `knowledge/design/example.md`
- `inbox/2026/05/noise.md` — leave in inbox; too raw

### Canonical Changes

- Create `knowledge/design/example.md`
- Update `INDEX.md`
- Append `LOG.md`

### Provenance

- Canonical page will cite consumed inbox note paths.

### Open Questions

- Decide whether command semantics belong under `knowledge/design/` or `knowledge/reference/`.
```

## Apply output shape

After applying, report:

- files created
- files updated
- inbox notes moved or marked processed
- validation commands run
- residual risks

## Canonical page style

Prefer:

- short headings
- explicit claims
- links to related pages
- provenance section
- "Open Questions" when uncertain

Avoid:

- raw transcript dumps
- "the user said" unless it matters for provenance
- speculative architecture
- duplicating entire inbox notes
- a global taxonomy that conflicts with the KB's local structure
