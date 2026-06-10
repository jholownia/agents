<!-- markdownlint-disable MD024 MD032 -->

# Changelog

## 0.6.0 — 2026-06-10

### Added
- `kb-dream` agent now runs a temporal revision pass during planning: scans canonical pages for future-tense claims whose dates have passed and proposes past-tense revisions (or unverified flags) in the dry-run plan's new "Temporal Revisions" section. Rides the existing dry-run gate — never auto-applied.
- Version lockstep check in the test suite: `plugin.json`, the marketplace entry, and `kb_registry.__version__` must agree.
- Regression tests for the fixes below (155 checks total).

### Fixed
- `remember`/`stage` no longer silently overwrite an existing note when two calls land in the same second with the same slug — collisions get numbered suffixes via `_unique_rel_path()`.
- `stage --file` on a non-UTF8 text file no longer crashes with a traceback; undecodable bytes are replaced, matching `--dir` behaviour.
- `search` treats the query as a literal string in both backends (rg now runs with `--fixed-strings -e`; previously rg interpreted regex metacharacters while the Python fallback escaped them) and dash-prefixed queries are no longer parsed as rg flags.
- `recall` with both `--query` and `--tag` now errors instead of silently ignoring `--tag`.
- `status` on an empty registry prints the bootstrap/add hint that `commands/status.md` promised.
- `kb_registry.__version__` was stuck at 0.2.0; now matches the plugin version.
- README no longer claims `bin/kb` is added to PATH on install (contradicted the 0.5.0 entry).

### Removed
- `status --fetch` (documented but never implemented) and `search --include-inbox` (no-op; inbox is included by default, use `--exclude-inbox` to opt out).

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
