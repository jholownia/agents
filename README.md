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

Codex does not currently use Claude Code marketplaces directly in this repo. The pragmatic path is:

1. Install the plugin with Claude Code.
2. Symlink the installed skill or plugin directory from `~/.claude/` into the matching Codex location under `~/.codex/`.
3. Keep Claude Code as the source of truth for marketplace install/update operations.

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
