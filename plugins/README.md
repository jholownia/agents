# Adding a plugin

Each plugin lives in its own directory under `plugins/` and follows the standard Claude Code plugin layout.

## Directory structure

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest (required)
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md          # Skill definition (required)
│       ├── scripts/          # Executable code (optional)
│       ├── references/       # Reference docs loaded on demand (optional)
│       └── assets/           # Output resources like templates (optional)
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
