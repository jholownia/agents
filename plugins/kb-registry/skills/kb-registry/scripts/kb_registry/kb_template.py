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

INBOX_README = """\
# Inbox

Staging area for raw or uncertain material.

Files here are individual Markdown notes with metadata frontmatter,
awaiting review and consolidation into `knowledge/`.

Processed notes may be moved under `inbox/processed/` after their durable
content is synthesized into canonical knowledge.
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
CONTRACT_DIRS = ["inbox", "knowledge", "sources", "tools"]


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
