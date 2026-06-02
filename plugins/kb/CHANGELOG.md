# Changelog

## 0.4.0 — 2026-06-02

### Fixed
- README drift left by the 0.3.0 restructure: the layout block listed a `dream/` skill directory and omitted `commands/` and `agents/`, and the "v0 scope" section still described consolidation as skill-led (`kb:dream`). Both now reflect the `kb-dream` agent. Version bumped so the plugin cache picks up the corrected docs.

## 0.3.0 — 2026-06-02

### Added
- `kb stage --file` / `kb stage --dir` transparently extract `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.epub`, `.html` to Markdown via `markitdown`. Extracted files carry provenance frontmatter (`kind: extracted`, `extracted_from`, `extractor`).
- `--keep-source` flag copies the original binary under `sources/YYYY/MM/`; default drops it.
- `kb-dream` agent (replaces the old in-session `dream` skill).
- Four user-facing slash commands: `/kb:bootstrap`, `/kb:add`, `/kb:status`, `/kb:sync`.
- Hoisted `references/scoping.md` as the canonical three-layer scoping reference.

### Changed
- Skill descriptions rewritten to the third-person `"This skill should be used when…"` template for better triggering.
- All skills carry `version:` frontmatter.
- Scoping reframed around **durable vs ephemeral** facts (was personal vs project).
- Stage command frontmatter tightened to `allowed-tools: Bash(kb:*)` (least-privilege).

### Fixed
- `kb stage --dir --keep-source` no longer overwrites same-basename source files from different directories — `_unique_rel_path()` disambiguates with numeric suffixes.
- Inbox README documents the third "extracted documents" shape; `references/safety.md` and `references/kb-contract.md` updated to match the v0.2 markitdown work.

### Removed
- `kb:dream` skill (consolidation now lives in the `kb-dream` subagent with isolated context).

## 0.2.0 — 2026-05-27

- Initial public version: registry, info, remember, stage, recall, retrospective skills over a shared `kb` CLI.
- `index.json` programmatic manifest alongside hand-curated `INDEX.md`.
- `kb forget` for soft removal via git history.
