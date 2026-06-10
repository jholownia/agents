<!-- markdownlint-disable MD024 MD032 -->

# Changelog

## 0.1.2 — 2026-06-10

### Fixed

- `references/scaffolding.md` used an undefined `<skill-path>` placeholder in the template-copy commands; now uses `${CLAUDE_PLUGIN_ROOT}/skills/spec-driven-execution/...` (same portable-path fix as kb 0.5.0).
- The scaffolded `.changes/CLAUDE.md` template numbered its per-change workflow 0–5 while SKILL.md detects phases 0–6; the template now carries an explicit mapping note so an agent reading both sees one scheme.
- SKILL.md `version:` frontmatter aligned with the plugin version (was stuck at 0.1.0).
- Plugin README layout block now lists `CHANGELOG.md` and `scripts/`.

## 0.1.1 — 2026-06-02

### Changed

- Retroactive entry (reconstructed from git history; this file did not exist at release time): applied plugin-dev audit findings, added the plugin README, swept doc drift.

## 0.1.0 — 2026-05-27

- Initial release: `spec-driven-execution` skill with a seven-phase per-change workflow, `references/` (framing, scaffolding, failure-modes), `assets/templates/` for the `.changes/` workspace, and a structural test script.
