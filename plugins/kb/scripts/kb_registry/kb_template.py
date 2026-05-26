"""KB template: file contents and contract validation for knowledge bases."""

import os

# --- Template file contents ---

AGENTS_MD = """\
# Agent Rules

This KB owns its internal organization. Use these rules and the existing
`knowledge/` structure before inventing new categories.

## Capture

- Stage raw or uncertain material in `inbox/`.
- Preserve provenance when adding facts.
- Prefer concise, durable notes over transcripts.
- Do not store secrets, credentials, tokens, or private personal data.

## Consolidation

- Treat `inbox/` as source material and `knowledge/` as synthesized output.
- Read `BRIEF.md`, `INDEX.md`, `LOG.md`, and existing `knowledge/` pages before canonical edits.
- Propose a dry-run plan before rewriting canonical knowledge unless explicitly told to apply.
- Update existing pages when they are the natural home.
- Create new pages only when the existing structure has no good fit.
- Preserve consumed inbox/source paths in canonical pages or `LOG.md`.
- Mark consumed inbox notes processed; do not delete them in v0.
- Use git history for auditability.
"""

BRIEF_TEMPLATE = """\
# {name} KB Brief

## Purpose

Short description of what this KB contains and when agents should use it.

## Scope

- Included:
- Excluded:

## Key Areas

- `knowledge/` - synthesized durable knowledge
- `inbox/` - staged notes awaiting consolidation
- `sources/` - optional source material or pointers
- `tools/` - reserved for future reusable diagnostics
- `LOG.md` - maintenance and consolidation journal

## Retrieval Guidance

Start with `BRIEF.md`, search before opening broad files, and prefer scoped context.
"""

INDEX_MD = """\
# Index

Navigational index for this knowledge base.

## Canonical Knowledge

- [Knowledge README](knowledge/README.md)

## Staging

- [Inbox README](inbox/README.md)

## Sources

- [Sources README](sources/README.md)

## Maintenance

- [Maintenance Log](LOG.md)
- [Tools README](tools/README.md)
"""

LOG_MD = """\
# Maintenance Log

Append short entries when inbox notes are consolidated into canonical knowledge.

Each entry should include:

- date
- agent/tool identity when useful
- inbox/source paths consumed
- canonical pages created or updated
- unresolved questions or follow-up work
"""

NOTES_README = """\
# Notes

Short, single-paragraph project / domain / codebase facts that are expensive
to re-derive but too small to deserve a canonical page in `knowledge/`.

Examples of what belongs here:

- "EMMA's nightly job runs at 02:00 UTC via cron."
- "The `analyze_meter_drift` function returns null when input has <30 days
  of data."
- "We tried PostgreSQL JSON columns in 2024 and abandoned them — search
  latency was 3x."

Format: one Markdown file per note at
`notes/<YYYY>/<MM>/<timestamp>-<slug>.md`, with `tags:` and `created_at:`
frontmatter and the fact as the body.

This directory is **append-only**: `kb-dream` never touches it. Notes here
are final, not raw material.

What does NOT belong here:

- Personal user preferences ("I like X", "I prefer rebase over merge") —
  use Claude's auto-memory, not the KB.
- Normative workflow rules ("don't push to master") — use CLAUDE.md or
  AGENTS.md.
- Long-form synthesised knowledge — write to `knowledge/` via `kb-dream`.
- Material that needs further processing — stage to `inbox/` instead.
"""

INBOX_README = """\
# Inbox

Staging area for raw or uncertain material, awaiting consolidation into
`knowledge/`.

Three shapes of material live here:

- **Notes** — agent-written, semi-structured. Produced by
  `kb stage --note ...`. YAML frontmatter at top (`kind`, `created_at`,
  optional `source`/`title`). The note owns its heading.
- **Documents** — any text file copied verbatim. Produced by
  `kb stage --file <path>` or by dropping a Markdown file directly into
  this directory. No frontmatter, no auto-heading. Provenance lives in
  the git commit message.
- **URL pointers** — produced by `kb stage --url <url>`. Frontmatter has
  `kind: url` and `url: <url>`; the next `kb-dream` pass fetches and
  summarises the link.

Processed material may be moved under `inbox/processed/` after its
durable content is synthesized into canonical knowledge.
"""

KNOWLEDGE_README = """\
# Knowledge

Canonical synthesized knowledge. Treat as durable reference.
"""

SOURCES_README = """\
# Sources

Optional source material, links, or pointers to external references.
"""

TOOLS_README = """\
# Tools

Reserved for future reusable scripts and diagnostics. Not executed in v0.
"""

GITIGNORE = """\
# OS
.DS_Store
Thumbs.db

# Editor
*.swp
*.swo
*~

# Secrets — never commit
.env
*.pem
*.key
"""

# Required contract files/dirs
CONTRACT_FILES = ["AGENTS.md", "BRIEF.md", "INDEX.md", "LOG.md"]
CONTRACT_DIRS = ["inbox", "knowledge", "notes", "sources", "tools"]


def create_kb(path, name):
    """Create a KB from template at the given path. Path must not exist or be
    empty (caller checks)."""
    os.makedirs(path, exist_ok=True)

    def _write(relpath, content):
        full = os.path.join(path, relpath)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(content)

    _write("AGENTS.md", AGENTS_MD)
    _write("BRIEF.md", BRIEF_TEMPLATE.format(name=name))
    _write("INDEX.md", INDEX_MD)
    _write("LOG.md", LOG_MD)
    _write("inbox/README.md", INBOX_README)
    _write("knowledge/README.md", KNOWLEDGE_README)
    _write("notes/README.md", NOTES_README)
    _write("sources/README.md", SOURCES_README)
    _write("tools/README.md", TOOLS_README)
    _write(".gitignore", GITIGNORE)


def validate_kb_contract(path):
    """Check for missing contract files/dirs. Returns list of missing items."""
    missing = []
    for f in CONTRACT_FILES:
        if not os.path.isfile(os.path.join(path, f)):
            missing.append(f)
    for d in CONTRACT_DIRS:
        if not os.path.isdir(os.path.join(path, d)):
            missing.append(d + "/")
    return missing
