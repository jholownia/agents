# agents

Personal plugin marketplace — a collection of skills and plugins for Claude Code and Codex.

## Installation

Register this repository as a marketplace, then install individual plugins.

### Claude Code

```bash
# Register the marketplace
claude plugin marketplace add jholownia/agents

# List available plugins
claude plugin marketplace list

# Install a plugin (user scope)
claude plugin install <plugin-name>@agents
```

### Manual registration

Add to `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "agents": {
      "source": {
        "source": "github",
        "repo": "jholownia/agents"
      }
    }
  }
}
```

### Codex

Codex does not consume Claude Code marketplaces. It discovers skills as
self-contained folders under `$CODEX_HOME/skills/<name>/` (default `~/.codex/skills`)
and follows symlinks — so the single-source-of-truth path is to symlink a skill's
directory into the Codex skills dir. Two cases:

- **Standalone skills** (self-contained, skill-relative paths) symlink directly:
  `ln -sfn <skill-dir> ~/.codex/skills/<name>`.
- **Plugin skills that resolve paths through `${CLAUDE_PLUGIN_ROOT}`** (like `kb`)
  also need that variable exported to Codex's shells — Codex, unlike Claude Code,
  does not set it. Add it once to `~/.codex/config.toml`:

  ```toml
  [shell_environment_policy.set]
  CLAUDE_PLUGIN_ROOT = "/abs/path/to/plugins/<name>"
  ```

  This is a global Codex setting and `CLAUDE_PLUGIN_ROOT` is per-plugin, so it cleanly
  serves only one such plugin at a time; expose a second one only by making its skills
  self-contained.

For `kb`, both steps are automated — run
[`plugins/kb/scripts/link-codex-skills.sh`](plugins/kb/scripts/link-codex-skills.sh),
add the config snippet it prints, and restart Codex. See the plugin's
[README](plugins/kb/README.md#using-kb-from-codex) for details.

Claude Code stays the source of truth for marketplace install/update; the Codex
symlinks track the live plugin tree.

## Repository structure

```text
agents/
├── .claude-plugin/
│   └── marketplace.json      # Marketplace manifest
├── .github/workflows/ci.yml  # Runs each plugin's test script + version lockstep check
├── AGENTS.md                 # Repo conventions (versioning, plugin cache gotcha)
├── plugins/                  # One directory per plugin
│   └── <plugin-name>/
│       ├── .claude-plugin/plugin.json
│       ├── CHANGELOG.md
│       ├── skills/ commands/ agents/ references/ bin/   # whichever apply
│       └── scripts/test_<plugin-name>.sh
└── README.md
```

See [`plugins/README.md`](plugins/README.md) for the authoritative per-plugin layout.

## Adding a plugin

See [`plugins/README.md`](plugins/README.md) for the full guide on creating and registering plugins.
