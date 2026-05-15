"""Safety checks: path traversal, secret scanning, canonical write guard."""

import os
import re

# Patterns that indicate likely secrets
SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"(?i)aws_secret_access_key\s*[=:]\s*\S+", "AWS secret key"),
    (r"-----BEGIN\s+(RSA\s+|DSA\s+|EC\s+|OPENSSH\s+|PGP\s+)?PRIVATE KEY-----",
     "Private key"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub personal access token"),
    (r"gho_[A-Za-z0-9]{36}", "GitHub OAuth token"),
    (r"ghs_[A-Za-z0-9]{36}", "GitHub app token"),
    (r"github_pat_[A-Za-z0-9_]{22,}", "GitHub fine-grained PAT"),
    (r"sk-[A-Za-z0-9]{20,}", "OpenAI/Anthropic API key"),
    (r"sk-ant-[A-Za-z0-9\-]{20,}", "Anthropic API key"),
    (r"(?i)(?:password|passwd|token|secret|api_key)\s*[=:]\s*\S+",
     "Generic credential"),
]

_compiled = [(re.compile(p), desc) for p, desc in SECRET_PATTERNS]


def check_path_traversal(kb_root, target_path):
    """Return True if target_path escapes kb_root after symlink resolution.

    Also rejects absolute target paths.
    """
    if os.path.isabs(target_path):
        return True
    root = os.path.realpath(kb_root)
    resolved = os.path.realpath(os.path.join(root, target_path))
    # Must be inside root (equal or child)
    return not (resolved == root or resolved.startswith(root + os.sep))


def scan_secrets(text):
    """Scan text for likely secrets. Returns list of matched descriptions."""
    matches = []
    for pattern, desc in _compiled:
        if pattern.search(text):
            matches.append(desc)
    return matches


def check_canonical_write(kb_root, target_path):
    """Return True if target_path would write into knowledge/ (forbidden in v0)."""
    root = os.path.realpath(kb_root)
    resolved = os.path.realpath(os.path.join(root, target_path))
    knowledge_dir = os.path.join(root, "knowledge")
    return resolved == knowledge_dir or resolved.startswith(
        knowledge_dir + os.sep
    )


def check_binary(filepath):
    """Return True if file appears to be binary (has null bytes in first 8KB)."""
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(8192)
        return b"\x00" in chunk
    except Exception:
        return False


def check_large_file(filepath, max_bytes=1_000_000):
    """Return True if file exceeds max_bytes."""
    try:
        return os.path.getsize(filepath) > max_bytes
    except Exception:
        return False
