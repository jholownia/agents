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

```
agents/
├── .claude-plugin/
│   └── marketplace.json      # Marketplace manifest
├── context/                  # Design research and reference docs
├── plugins/                  # Plugin directory
│   └── <plugin-name>/        # One directory per plugin
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── <skill-name>/
│               └── SKILL.md
└── README.md
```

## Adding a plugin

See [`plugins/README.md`](plugins/README.md) for the full guide on creating and registering plugins.
