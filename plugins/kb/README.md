# kb

Claude Code plugin for agent-maintained knowledge bases — persistent, scoped, searchable, git-backed memory that survives across sessions and project repositories.

## Design principle

> The CLI offers safe file operations and retrieval aids. The agent decides how this KB organises and evolves its knowledge, guided by the per-KB `AGENTS.md` — which the agent is free to edit.

The seeded directory layout, kind labels, and skill workflows are *defaults* sourced from the consolidation research (Microsoft "AI agent amnesia", Karpathy's LLM-wiki gist). None are enforced — override them per KB by editing `AGENTS.md`.

## What it does

Provides seven scoped skills over a shared `kb` CLI:

| Skill | Purpose |
|---|---|
| `kb:registry` | add / remove / bootstrap / sync / status KBs — lifecycle + state |
| `kb:info` | list KBs, read briefs, carries the three-layer scoping rules |
| `kb:remember` | append short single-paragraph facts to `notes/` |
| `kb:stage` | stage notes / files / URL pointers / follow-ups into `inbox/` |
| `kb:recall` | search indexable KB sections, list pending inbox material |
| `kb:retrospective` | end-of-session capture of expensive-to-derive knowledge |
| `kb-dream` *(agent)* | consolidate `inbox/` into canonical pages, dry-run-first |

Each skill is small and triggered by sharp language patterns (see each `SKILL.md`'s `description:`).

## Three-layer scoping

The KB is *one* of three persistence layers. The axis is **durable fact vs ephemeral state**, not "personal vs project":

| What | Where |
|---|---|
| User preferences about agent behaviour ("address me as bro", "I prefer rebase") | Claude's auto-memory |
| Short-lived project state (current task, last error seen) | Claude's auto-memory |
| Normative workflow rules ("don't push to master") | CLAUDE.md / AGENTS.md |
| Durable facts — project, domain, codebase, **or personal-life** | KB `notes/` via `kb remember` |
| Decisions, runbook material, longer-form facts | KB `inbox/` → canonical pages via `kb stage` + `kb-dream` |
| URL pointers to read later | KB `inbox/` via `kb stage --url` |

**Litmus test:** would re-deriving this fact require meaningful work? Yes → KB. Trivial to re-ask, or only relevant to the current session → auto-memory.

Personal-life facts (birthdays, contacts, addresses, family info) qualify by the litmus test. If you want them in a KB, register a `user-kb` and let durable personal data land there. Project KBs should not hold personal data.

## Quick start

```bash
# Bootstrap a new KB
kb bootstrap my-project --path ~/knowledge/my-project-kb

# Remember a short project fact
kb remember "Customer A12 wants weekly reports on Mondays." --tags my-project,reporting

# Stage a longer note for the next dream pass
kb stage my-project --kind decision --note "We chose X over Y because Z."

# Save a URL to summarise later
kb stage my-project --url "https://example.com/article" --note "Why this matters"

# Recall what we know
kb recall my-project --query "weekly reports"
kb recall my-project --tag reporting
```

## Layout

```text
plugins/kb/
  .claude-plugin/plugin.json
  bin/kb                          # CLI entry (added to PATH on install)
  scripts/
    kb_registry/                  # Python package
    test_kb_registry.sh
  references/                     # shared docs (commands, kb-contract, safety)
  skills/
    registry/ info/ remember/ stage/ recall/ retrospective/ dream/
```

- **Config:** `~/.config/kb-registry/registry.json` (override with `--config`, `KB_REGISTRY_CONFIG`, or the project-scope plugin config below).
- **Metrics:** `~/.local/state/kb-registry/events.jsonl` (configurable).

## Per-repo defaults

The CLI honours Claude Code's standard per-repo plugin config (`pluginConfigs` in `.claude/settings.json`). Two options are exposed via the plugin's `userConfig`:

```json
{
  "enabledPlugins": {"kb@agents": true},
  "pluginConfigs": {
    "kb": {
      "options": {
        "default_kb": "emma",
        "registry_config_path": "/Users/jh/work/registries/emma.json"
      }
    }
  }
}
```

Claude Code exports these as `CLAUDE_PLUGIN_OPTION_DEFAULT_KB` and `CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH` to the CLI's subprocess. Set them at user scope for a global default, at project scope for per-repo behaviour.

Resolution order (highest precedence first):

| Config | Order |
|---|---|
| Registry path | `--config <path>` > `KB_REGISTRY_CONFIG` > `CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH` > `~/.config/kb-registry/registry.json` |
| Default KB (when no positional/--kb given) | explicit positional/--kb > `CLAUDE_PLUGIN_OPTION_DEFAULT_KB` > registry entry marked `"default": true` |

## v0 scope

Python 3 stdlib only. Lexical search via `rg`. Markdown/Git KBs. No MCP, vector search, or autonomous rewrites.

Inbox consolidation is intentionally skill-led: `kb:dream` runs only when the user invokes it, produces a dry-run plan first, and writes canonical pages directly. The CLI guards against accidental canonical writes.

## Known gaps (not in v0)

These are real gaps the subagent dogfood pass surfaced; deferred to v0.1+:

- **Mutation of existing notes beyond deletion** — `kb forget` removes a page from the working surface, but there is no CLI verb for "edit this note's text" or "retag this page". Workaround: edit the file/frontmatter directly and commit.
- **Re-tagging existing notes** — same: edit frontmatter directly. Tag mutations are append-only-from-the-CLI today.
- **Dream-history queries beyond `kb open <kb> LOG.md`** — there's no CLI verb to filter LOG entries by date, kind, or supersession. `kb open` is sufficient for v0.
- **Documents staged via `--file` cannot carry kind/title/source metadata** — by design (documents have no frontmatter), but means a longer retrospective file has to be staged via `--note "$(cat file.md)"` to get the `kind: retrospective` label.
- **`bin/kb` PATH injection** depends on the plugin being installed via Claude Code. Local development uses `plugins/kb/bin/kb` explicitly.

Resolved in v0.2 (originally listed here):

- ~~Plugin-config to CLI bridge for per-repo defaults~~ — now reads `CLAUDE_PLUGIN_OPTION_*` env vars exposed by Claude Code from `pluginConfigs.kb.options` in `.claude/settings.json` (see "Per-repo defaults" above).
