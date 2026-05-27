# agents

Personal Claude Code plugin marketplace. See [README.md](README.md) for install
instructions and [plugins/README.md](plugins/README.md) for plugin layout.

## Stance

Skills are tools, not workflows. Keep `SKILL.md` `description:` frontmatter
sharp and trigger-driven; defer detail to per-plugin `references/`. Prefer
guidelines over restrictions, recommendations over prescribed workflows,
flexible primitives over rigid contracts. The `kb` plugin's seeded `AGENTS.md`
is the worked example of the stance applied inside a plugin.

## Working in a plugin

Each plugin is self-contained under `plugins/<name>/`. Read the per-plugin
`README.md` first. Many plugins ship `scripts/test_<name>.sh` — run it before
declaring a change done.

## Versioning

`plugins/<name>/.claude-plugin/plugin.json:version` and the matching entry in
`.claude-plugin/marketplace.json` move in lockstep when cutting a release.
