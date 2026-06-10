# Adding a plugin

Each plugin lives in its own directory under `plugins/` and follows the standard Claude Code plugin layout.

## Directory structure

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest (required)
├── CHANGELOG.md              # One entry per version bump (required once bumped)
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md          # Skill definition (required)
│       ├── scripts/          # Executable code (optional)
│       ├── references/       # Reference docs loaded on demand (optional)
│       └── assets/           # Output resources like templates (optional)
├── commands/                 # Slash commands, one .md per command (optional)
├── agents/                   # Subagent definitions (optional)
├── references/               # Docs shared across skills/commands (optional)
├── bin/                      # CLI entry points — invoke via ${CLAUDE_PLUGIN_ROOT}/bin/<name>,
│                             # Claude Code does NOT add bin/ to PATH (optional)
├── scripts/
│   └── test_<plugin-name>.sh # Self-contained test script; CI runs it (recommended)
└── README.md                 # Per-plugin documentation (optional)
```

## Required files

### `plugin.json`

```json
{
  "name": "my-plugin",
  "description": "What this plugin does",
  "version": "0.1.0",
  "author": {
    "name": "Your Name"
  }
}
```

### `SKILL.md`

Every skill needs a `SKILL.md` with YAML frontmatter:

```yaml
---
name: my-skill
description: >
  When and why Claude should use this skill.
  This description drives automatic invocation — make it specific.
---

# My Skill

Instructions Claude follows when this skill is active.
```

Key guidelines for skill content:
- Focus on non-obvious, project-specific knowledge — not things the model already knows.
- Lead with gotchas and real failure modes.
- Keep `SKILL.md` under ~500 lines; split large reference material into `references/`.
- Use `scripts/` for deterministic, reusable operations.

## Registering the plugin

After creating the plugin directory, add an entry to the root marketplace manifest at `.claude-plugin/marketplace.json`:

```json
{
  "name": "my-plugin",
  "description": "What this plugin does",
  "source": "./plugins/my-plugin",
  "version": "0.1.0"
}
```

Append this object to the `plugins` array.

## Versioning

Claude Code serves installed plugins from a cached snapshot keyed by `version` — an unbumped change never reaches anyone's runtime. The rules (see the repo [AGENTS.md](../AGENTS.md) for the full rationale):

- Bump `plugin.json:version` on any commit that changes user-visible surface (skills, commands, agents, CLI behavior, error messages, menu descriptions).
- Keep the matching entry in `.claude-plugin/marketplace.json` in lockstep — CI fails on drift.
- Add a `CHANGELOG.md` entry for every bump.
- If the plugin ships runtime code with its own version constant (like kb's `kb_registry.__version__`), keep that in lockstep too and assert it in the plugin's test script.
