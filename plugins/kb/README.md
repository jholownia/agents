# kb

Claude Code plugin for agent-maintained knowledge bases — persistent, scoped, searchable, git-backed memory that survives across sessions and project repositories.

## Design principle

> The CLI offers safe file operations and retrieval aids. The agent decides how this KB organises and evolves its knowledge, guided by the per-KB `AGENTS.md` — which the agent is free to edit.

The seeded directory layout, kind labels, and skill workflows are *defaults* sourced from the consolidation research (Microsoft "AI agent amnesia", Karpathy's LLM-wiki gist). None are enforced — override them per KB by editing `AGENTS.md`.

## What it does

Three Claude Code surfaces over a shared `kb` CLI:

**Skills** (Claude auto-triggers on description match):

| Skill | Purpose |
|---|---|
| `kb:registry` | add / remove / bootstrap / sync / status KBs — lifecycle + state |
| `kb:info` | list KBs, read briefs, points at the three-layer scoping rules |
| `kb:remember` | append short single-paragraph facts to `notes/` |
| `kb:stage` | stage notes / files / URL pointers / directories into `inbox/` |
| `kb:recall` | search indexable KB sections, list pending inbox material |
| `kb:retrospective` | end-of-session capture of expensive-to-derive knowledge |

**Slash commands** (user-typed; deterministic CLI passthroughs):

| Command | Wraps |
|---|---|
| `/kb:bootstrap <name> [--path ...]` | `${CLAUDE_PLUGIN_ROOT}/bin/kb bootstrap` |
| `/kb:add <name> --path ... [--remote ...]` | `${CLAUDE_PLUGIN_ROOT}/bin/kb add` |
| `/kb:status [<kb>] [--all]` | `${CLAUDE_PLUGIN_ROOT}/bin/kb status` |
| `/kb:sync [<kb>] [--all]` | `${CLAUDE_PLUGIN_ROOT}/bin/kb sync` |

**Agent**:

| Agent | Purpose |
|---|---|
| `kb-dream` | consolidate a KB's `inbox/` into canonical pages — dry-run plan, then apply on approval. Multi-step autonomous workflow with its own tool budget. |

Skills are auto-triggered by sharp language patterns (see each `SKILL.md`'s `description:`). Commands give the user explicit `/`-typed entry points for the registry lifecycle. The agent handles consolidation because it's a multi-step judgment workflow, not a one-shot operation.

## Distill

`kb distill` is a typed-finding primitive emitted by `kb-dream` during consolidation, designed to compound accumulated knowledge into actionable improvements. The plugin owns detection at consolidation time, an immutable append-only ledger, hash-based dedup, and TTL-based retention (default 90 days). It deliberately does not track "addressed" state — consumers (WARDEN, humans, future plugins) read the ledger via `kb distill surface`, route findings downstream (file issues, draft skills, propose `CLAUDE.md` nudges), and track their own progress. Storage lives under `.kb-internal/distill/` — a plugin-reserved namespace excluded from `kb reindex`, `kb search`, and `kb recall`. Six v0 finding types span two tracks: convergent (`failure-mode`, `resolution-path`, `heuristic` — candidates for procedural artifacts) and divergent (`open-question`, `contradiction`, `incomplete` — candidates for follow-up).

## Three-layer scoping

The KB is *one* of three persistence layers — alongside Claude's auto-memory and project `CLAUDE.md` / `AGENTS.md`. The axis is **durable fact vs ephemeral state**, not "personal vs project". Quick summary:

- **Durable facts** (project, domain, codebase, or personal-life) → KB.
- **User preferences about agent behaviour** and **short-lived project state** → auto-memory.
- **Normative workflow rules** → `CLAUDE.md` / `AGENTS.md`.

Personal-life facts qualify if you have a personal `user-kb`; otherwise prefer auto-memory rather than misfiling into a project KB. Full routing rules, examples, and the litmus test: [references/scoping.md](references/scoping.md).

## Quick start

```bash
# Bootstrap a new KB
${CLAUDE_PLUGIN_ROOT}/bin/kb bootstrap my-project --path ~/knowledge/my-project-kb

# Remember a short project fact
${CLAUDE_PLUGIN_ROOT}/bin/kb remember "Customer A12 wants weekly reports on Mondays." --tags my-project,reporting

# Stage a longer note for the next dream pass
${CLAUDE_PLUGIN_ROOT}/bin/kb stage my-project --kind decision --note "We chose X over Y because Z."

# Save a URL to summarise later
${CLAUDE_PLUGIN_ROOT}/bin/kb stage my-project --url "https://example.com/article" --note "Why this matters"

# Recall what we know
${CLAUDE_PLUGIN_ROOT}/bin/kb recall my-project --query "weekly reports"
${CLAUDE_PLUGIN_ROOT}/bin/kb recall my-project --tag reporting
```

## Layout

```text
plugins/kb/
  .claude-plugin/plugin.json
  bin/kb                          # CLI entry — invoked as ${CLAUDE_PLUGIN_ROOT}/bin/kb (not on PATH)
  scripts/
    kb_registry/                  # Python package
    test_kb_registry.sh
  references/                     # shared docs (commands, kb-contract, safety, scoping)
  skills/
    registry/ info/ remember/ stage/ recall/ retrospective/
  commands/                       # /kb:bootstrap /kb:add /kb:status /kb:sync
  agents/
    kb-dream.md                   # inbox -> canonical consolidation (dry-run first)
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

Set these at user scope (`~/.claude/settings.json`) for a global default, or at project scope (`<repo>/.claude/settings.json`) for per-repo behaviour.

Claude Code exposes configured options as `CLAUDE_PLUGIN_OPTION_*` env vars, but **only inside plugin-managed subprocesses** (hooks, MCP/LSP servers, monitors) — *not* inside the generic Bash-tool subprocess the kb skills use to invoke this CLI. So the CLI does not rely on the env var alone: when it is absent, the CLI reads the `pluginConfigs.kb.options` block straight from the `.claude/settings.json` cascade (the same files Claude Code would merge). The env var still takes precedence when present.

Resolution order (highest precedence first):

| Config | Order |
|---|---|
| Registry path | `--config <path>` > `KB_REGISTRY_CONFIG` > `CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH` > `registry_config_path` in the `.claude/settings.json` cascade > `~/.config/kb-registry/registry.json` |
| Default KB (when no positional/--kb given) | explicit positional/--kb > `CLAUDE_PLUGIN_OPTION_DEFAULT_KB` > `default_kb` in the `.claude/settings.json` cascade (project `settings.local.json` > project `settings.json` > user) > registry entry marked `"default": true` |

## v0 scope

Python 3 stdlib only. Lexical search via `rg`. Markdown/Git KBs. No MCP, vector search, or autonomous rewrites.

Inbox consolidation is intentionally agent-led: the `kb-dream` agent runs only when the user invokes it, produces a dry-run plan first, and writes canonical pages on approval. The CLI guards against accidental canonical writes.

## Known gaps (not in v0)

These are real gaps the subagent dogfood pass surfaced; deferred to v0.1+:

- **Mutation of existing notes beyond deletion** — `${CLAUDE_PLUGIN_ROOT}/bin/kb forget` removes a page from the working surface, but there is no CLI verb for "edit this note's text" or "retag this page". Workaround: edit the file/frontmatter directly and commit.
- **Re-tagging existing notes** — same: edit frontmatter directly. Tag mutations are append-only-from-the-CLI today.
- **Dream-history queries beyond `${CLAUDE_PLUGIN_ROOT}/bin/kb open <kb> LOG.md`** — there's no CLI verb to filter LOG entries by date, kind, or supersession. `${CLAUDE_PLUGIN_ROOT}/bin/kb open` is sufficient for v0.
- **Text documents staged via `--file` cannot carry user-supplied kind/title/source metadata** — by design, verbatim documents have no frontmatter. Extracted files carry automatic provenance frontmatter. A longer retrospective file still has to be staged via `--note "$(cat file.md)"` to get `kind: retrospective`.
- **No PATH injection for `bin/kb`** — Claude Code does not put plugin `bin/` directories on PATH; all agent-facing invocations use `${CLAUDE_PLUGIN_ROOT}/bin/kb`, and local development uses `plugins/kb/bin/kb` explicitly. Humans wanting a short `kb` alias can symlink the script into `~/.local/bin`.

Resolved in v0.2 (originally listed here):

- ~~Plugin-config to CLI bridge for per-repo defaults~~ — now reads `CLAUDE_PLUGIN_OPTION_*` env vars exposed by Claude Code from `pluginConfigs.kb.options` in `.claude/settings.json` (see "Per-repo defaults" above).
