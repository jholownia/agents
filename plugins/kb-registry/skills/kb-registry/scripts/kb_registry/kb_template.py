"""KB template: file contents and contract validation for knowledge bases."""

import os

# --- Template file contents ---

AGENTS_MD = """\
# Agent Rules

- Stage raw or uncertain material in `inbox/`.
- Do not rewrite canonical knowledge casually.
- Preserve provenance when adding facts.
- Prefer concise, durable notes over transcripts.
- Do not store secrets, credentials, tokens, or private personal data.
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

## Retrieval Guidance

Start with `BRIEF.md`, search before opening broad files, and prefer scoped context.
"""

INDEX_MD = """\
# Index

Navigational index for this knowledge base.
"""

INBOX_README = """\
# Inbox

Staging area for raw or uncertain material.

Files here are individual Markdown notes with metadata frontmatter,
awaiting review and consolidation into `knowledge/`.
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
CONTRACT_FILES = ["AGENTS.md", "BRIEF.md", "INDEX.md"]
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
