"""Safety checks: path traversal, canonical write guard, binary/large guards."""

import os


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
