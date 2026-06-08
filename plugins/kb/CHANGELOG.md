<!-- markdownlint-disable MD024 MD032 -->

# Changelog

## 0.5.0 — 2026-06-08

### Fixed
- All agent-facing CLI invocations now use `${CLAUDE_PLUGIN_ROOT}/bin/kb` instead of bare `kb`, per Anthropic's plugin guidance (`plugin-dev/skills/plugin-structure/SKILL.md` — Portable Path References). Bare `kb` was functionally a relative-to-PATH reference and broke in headless containers where Claude Code doesn't inject the plugin's `bin/` onto PATH (discovered during WARDEN v1 in the emma repo, which had to add a Dockerfile symlink workaround). Updated across `skills/`, `commands/`, `agents/`, `references/`, and `README.md`. Slash-command `allowed-tools` scoped to `Bash(${CLAUDE_PLUGIN_ROOT}/bin/kb:*)` to match the new invocation form. The `bin/kb` docstring no longer claims PATH injection; humans wanting a short alias can symlink `${CLAUDE_PLUGIN_ROOT}/bin/kb` onto `~/.local/bin` themselves.

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
