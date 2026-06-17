<!-- markdownlint-disable MD024 MD032 -->

# Changelog

## 0.3.0 — 2026-06-17

### Added

- **Phase 2 — Architecture pass.** When the decomposition names 3+ items of plausibly-similar shape, the protocol now requires an explicit pattern survey + proposed default shape + numbered `A-N` decisions, captured in a new `## Architecture` section in `PROJECT.md` (or sibling `ARCHITECTURE.md` for heavier batches). Per-change `validation.md` references `A-N` or records deviations explicitly. Sourced from a WARDEN-workflow batch retrospective where copy-paste from change N-1 propagated incidental choices as if load-bearing (#362). Deliberately framed as a grounding document, not a binding spec — the deviation contract gives it teeth without ossifying.
- `references/architecture.md` — output shape, deviation contract, worked example, Architect subagent prompt.
- `references/patterns.md` — short opinionated pattern vocabulary (Strategy, Command, Policy, Pipeline, State machine, DI, Ports & adapters, Shared skeleton + hooks).
- *Copy-the-previous-change drift* failure mode in `references/failure-modes.md`. The tell — *"like change N-1 but …"* — plus the symmetric premature-abstraction warning.

### Changed

- Phase numbering in `SKILL.md`: 0–6 → 0–7. Per-change template steps in `assets/templates/CLAUDE.md` remain 0–5; mapping note updated accordingly.
- Phase detection table reads top-down, first match wins, and Phase 2 is detected by the *presence* of a `## Architecture` section (filled or skip-marker) — the scaffolded `PROJECT.md` no longer pre-installs the heading, so the detector fires correctly on fresh scaffolds.
- `assets/templates/validation.md`, `references/framing.md`, `assets/templates/CLAUDE.md`: change-level decisions instruct framings to reference `A-N` or record deviations explicitly.

## 0.2.0 — 2026-06-11

### Added

- **Test proliferation antipatterns** section in `references/failure-modes.md`: three shapes that look like coverage but pin implementation rather than behaviour (string-grep on artefacts, shape-of-constant echoes, branching-by-mock-choreography), plus two smaller patterns and a three-question checklist for Phase 5. Sourced from a WARDEN test suite audit where ~11% of 317 tests retired without losing coverage of any locked decision. `SKILL.md` Phase 5 and `assets/templates/CLAUDE.md`'s anti-patterns list both point at it — the heavy reference lives in `failure-modes.md`, subagents get a tight bullet in the auto-loaded `.changes/CLAUDE.md`.
- **Forward compatibility** section in `assets/templates/design.md`: one paragraph naming the next-likely future work the design intends to survive and what would have to change if it shifts. Catches "we'd lock ourselves out of X" before it bites.
- **Phase summary** table in `assets/templates/design.md` (optional, for changes with a multi-phase rollout/migration): Phase / Deploys / Reversible by / Gate to proceed.
- **Removed** subsection under Scope in `assets/templates/validation.md` (optional, for changes that delete things): mirrors "Out of scope" but for things that existed and now don't.

### Changed

- **Decisions in `validation.md` now numbered as D-1, D-2, …** (was unprefixed `1.`, `2.`). Mirrors the existing I-N invariants convention so both can be referenced uniformly from code (`# implements D-3`) and tests (`test_d3_*`). The number stays stable even if other items renumber.
- **Invariants in `design.md` now explicitly numbered as I-1, I-2, …** in the template comment (the section already existed; numbering was implicit).
- `references/framing.md` notes the optional 3-column decisions table form (Decision / Resolution / Rationale) for `design.md`-grade changes — bullet form remains the lightweight default.

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
