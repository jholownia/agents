# KB Registry

Claude Code plugin for managing agent-maintained knowledge bases.

## What it does

Gives agents a persistent, scoped, searchable, git-backed place to stage and retrieve synthesized knowledge without polluting project repositories.

## Quick start

```bash
# Bootstrap a new KB
kb bootstrap my-project --path ~/knowledge/my-project-kb

# Stage a discovery
kb stage my-project --kind decision --note "We chose X because Y."

# Search across KBs
kb search "architecture"

# Read a specific file
kb open my-project knowledge/overview.md
```

## Architecture

- **CLI** (`scripts/kb`) — all operations go through the `kb` command.
- **Skill** (`SKILL.md`) — teaches Claude when and how to use KBs.
- **Dream skill** (`skills/kb-dream`) — agent-led inbox consolidation using each KB's local rules.
- **Config** — `~/.config/kb-registry/registry.json` (override with `--config` or `KB_REGISTRY_CONFIG`)
- **Metrics** — `~/.local/state/kb-registry/events.jsonl` (override via `metrics_path` in the config file)

## Progressive disclosure

Agents follow: `list` → `brief` → `search` → `open` → direct inspection.

## v0 scope

Python 3 stdlib only. Lexical search via `rg`. Markdown/Git KBs. No MCP, vector search, or autonomous rewrites.

Inbox consolidation is intentionally skill-led. Agents use `kb-dream` to propose and apply KB-specific canonical updates; the CLI does not impose a global knowledge taxonomy.
