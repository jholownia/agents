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
- staleness markers: stamp `last_reviewed: <ISO date>` in frontmatter every time you touch a canonical page, so `rg 'last_reviewed: 2024'` finds drift later
- when a page replaces material, add `supersedes:` frontmatter listing the prior inbox/knowledge paths

Avoid:

- raw transcript dumps
- "the user said" unless it matters for provenance
- speculative architecture
- duplicating entire inbox notes
- a global taxonomy that conflicts with the KB's local structure
- silent rewrites: every replaced claim deserves a `LOG.md` supersession entry

## Frontmatter conventions

Canonical pages may carry the following optional frontmatter:

```yaml
---
last_reviewed: "2026-05-15"
supersedes:
  - inbox/2026/05/20260512-103000-old-decision.md
  - knowledge/design/old-page.md
---
```

These are conventions, not CLI-enforced fields. `kb-dream` writes them when consolidating; future v0.1 verbs (`kb forget`, `kb supersede`) will consume them.

## Open Questions lifecycle

When a canonical page records uncertainty under an "Open Questions" heading, treat those bullets as work items on the next dream pass. Either answer them (and remove the bullet) or move them to `LOG.md` if they're no longer relevant. Open Questions that survive multiple passes are a signal the page should be retired or split.
