# kb

Claude Code plugin for agent-maintained knowledge bases — persistent, scoped, searchable, git-backed memory that survives across sessions and project repositories.

## What it does

Provides seven scoped skills over a shared `kb` CLI:

| Skill | Purpose |
|---|---|
| `kb:registry` | add / remove / bootstrap / sync / status KBs — lifecycle + state |
| `kb:info` | list KBs, read briefs, carries the three-layer scoping rules |
| `kb:remember` | append short single-paragraph facts to `notes/` |
| `kb:stage` | stage notes / files / URL pointers / follow-ups into `inbox/` |
| `kb:recall` | search `notes/` + `knowledge/`, list pending inbox material |
| `kb:retrospective` | end-of-session capture of expensive-to-derive knowledge |
| `kb:dream` | consolidate `inbox/` → `knowledge/`, dry-run-first |

Each skill is small and triggered by sharp language patterns (see each `SKILL.md`'s `description:`).

## Three-layer scoping

The KB is *one* of three persistence layers — use the right one:

| Fact | Layer |
|---|---|
| Personal user preferences ("I prefer rebase") | Claude's auto-memory — NOT the KB |
| Normative workflow rules ("don't push to master") | CLAUDE.md / AGENTS.md — NOT the KB |
| Short project / domain / codebase facts | KB `notes/` via `kb remember` |
| Decisions, runbook material, longer-form facts | KB `inbox/` → `knowledge/` via `kb stage` + `kb-dream` |
| URL pointers to read later | KB `inbox/` via `kb stage --url` |

**Litmus test:** would re-deriving this fact require meaningful work? Yes → KB. Trivial to re-ask → auto-memory.

## Quick start

```bash
# Bootstrap a new KB
kb bootstrap my-project --path ~/knowledge/my-project-kb

# Remember a short project fact
kb remember "Customer A12 wants weekly reports on Mondays." --tags my-project,reporting

# Stage a longer note for the next dream pass
kb stage my-project --kind decision --note "We chose X over Y because Z."

# Save a URL to summarise later
kb stage my-project --url "https://example.com/article" --note "Why this matters"

# Recall what we know
kb recall my-project --query "weekly reports"
kb recall my-project --tag reporting
```

## Layout

```text
plugins/kb/
  .claude-plugin/plugin.json
  bin/kb                          # CLI entry (added to PATH on install)
  scripts/
    kb_registry/                  # Python package
    test_kb_registry.sh
  references/                     # shared docs (commands, kb-contract, safety)
  skills/
    registry/ info/ remember/ stage/ recall/ dream/
```

- **Config:** `~/.config/kb-registry/registry.json` (override with `--config` or `KB_REGISTRY_CONFIG`).
- **Metrics:** `~/.local/state/kb-registry/events.jsonl` (configurable).

## v0 scope

Python 3 stdlib only. Lexical search via `rg`. Markdown/Git KBs. No MCP, vector search, or autonomous rewrites.

Inbox consolidation is intentionally skill-led: `kb:dream` runs only when the user invokes it, produces a dry-run plan first, and writes to `knowledge/` directly. The CLI guards against accidental canonical writes.

## Known gaps (not in v0)

These are real gaps the subagent dogfood pass surfaced; deferred to v0.1+:

- **Mutation of existing notes** — no skill owns "forget that we said X" / "remove the note about Y" / "fix the X note". Workaround: edit the file directly in `notes/` or `inbox/` and commit. Mass mutation would benefit from a `kb forget` / `kb supersede` verb (already on the v0.1+ list).
- **Re-tagging existing notes** — same: edit frontmatter directly. Tag mutations are append-only-from-the-CLI today.
- **Dream-history queries beyond `kb open <kb> LOG.md`** — there's no CLI verb to filter LOG entries by date, kind, or supersession. `kb open` is sufficient for v0.
- **Documents staged via `--file` cannot carry kind/title/source metadata** — by design (documents have no frontmatter), but means a longer retrospective file has to be staged via `--note "$(cat file.md)"` to get the `kind: retrospective` label.
- **`bin/kb` PATH injection** depends on the plugin being installed via Claude Code. Local development uses `plugins/kb/bin/kb` explicitly.
