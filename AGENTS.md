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

Bump the plugin version on any commit that changes user-visible surface:
skills, commands, agents, CLI behavior, error messages, or the descriptions
shown in the slash-command menu. Tests-only, refactor-only, or repo-meta
changes don't need a bump.

`plugins/<name>/.claude-plugin/plugin.json:version` and the matching entry in
`.claude-plugin/marketplace.json` move in lockstep. Add a CHANGELOG entry to
the plugin's `CHANGELOG.md` for every bump.

**Why this matters:** Claude Code caches each installed plugin under
`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` and serves slash
commands, skills, and agents from that snapshot — NOT from the live source
tree. The marketplace update check compares the declared `version` against
the cached version; if equal, no refetch. So an unbumped commit ships
silently from the dev tree but never reaches anyone's runtime.

## Fresh machine setup

[.claude/settings.json](.claude/settings.json) declares the `agents`
marketplace and enables `kb@agents` + `plugin-dev@claude-plugins-official`,
so Claude Code will offer to install both on first session in this repo.

To use `kb` against the dogfooding KB, clone and register it once:

```bash
git clone git@github.com:jholownia/test-kb.git ~/Code/test-kb
kb add test \
  --path ~/Code/test-kb \
  --remote git@github.com:jholownia/test-kb.git \
  --description "Self-referential KB used to dogfood the kb plugin." \
  --default
```

The repo's `pluginConfigs.kb.options.default_kb = "test"` then routes bare
`kb` commands here to that KB.
