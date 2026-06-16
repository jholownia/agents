"""Lexical search: rg-first with Python fallback."""

import fnmatch
import json
import os
import re
import shutil
import subprocess


def _rg_available():
    return shutil.which("rg") is not None


# Default ripgrep matches-per-file. A single hit per file frequently lands
# in frontmatter; 3 lets the agent see body matches too without flooding.
_DEFAULT_MAX_PER_FILE = 3


def _extract_title(abs_path):
    """Derive a result title: first H1 -> first non-blank body line ->
    filename slug. Skips YAML frontmatter."""
    try:
        with open(abs_path, "r", errors="replace") as f:
            in_frontmatter = False
            seen_open_dashes = False
            for raw in f:
                line = raw.rstrip("\n")
                if line.strip() == "---":
                    if not seen_open_dashes:
                        in_frontmatter = True
                        seen_open_dashes = True
                        continue
                    if in_frontmatter:
                        in_frontmatter = False
                        continue
                if in_frontmatter:
                    continue
                if line.startswith("# "):
                    return line[2:].strip()
                if line.strip():
                    return line.strip()[:80]
    except Exception:
        pass
    base = os.path.splitext(os.path.basename(abs_path))[0]
    return base.replace("-", " ").replace("_", " ").title()


def _search_rg(path, query, max_results=20, glob_pattern=None,
               exclude_inbox=False):
    """Search using ripgrep. Returns list of result dicts."""
    # --fixed-strings matches the Python fallback's re.escape semantics;
    # --smart-case mirrors the fallback's re.IGNORECASE (lowercase → case
    # insensitive, mixed-case → case sensitive); rg's default is fully
    # case-sensitive, which diverged from the fallback and missed hits on
    # capitalised titles like "Defensive validation" for a lowercase query.
    # -e keeps dash-prefixed queries from being parsed as rg flags.
    args = [
        "rg", "--json", "--fixed-strings", "--smart-case",
        "--max-count", str(_DEFAULT_MAX_PER_FILE),
        "--glob", "!.git",
        # I-5: .kb-internal/ is plugin-managed, never searched.
        "--glob", "!.kb-internal/",
    ]
    if exclude_inbox:
        args += ["--glob", "!inbox/"]
    if glob_pattern:
        args += ["--glob", glob_pattern]
    args += ["-e", query, path]

    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    results = []
    title_cache = {}
    for line in r.stdout.splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "match":
            continue
        data = obj["data"]
        abs_path = data["path"]["text"]
        rel_path = os.path.relpath(abs_path, path)
        line_number = data["line_number"]
        snippet = data["lines"]["text"].strip()
        if abs_path not in title_cache:
            title_cache[abs_path] = _extract_title(abs_path)
        results.append({
            "path": rel_path,
            "line": line_number,
            "title": title_cache[abs_path],
            "snippet": snippet[:200],
            "match_count": 1,
        })
        if len(results) >= max_results:
            break
    return results


def _search_python(path, query, max_results=20, glob_pattern=None,
                   exclude_inbox=False):
    """Fallback: walk directory and search .md files with re.

    Mirrors rg's `--smart-case`: any uppercase char in the query →
    case-sensitive; all lowercase → case-insensitive. Keeps the rg and
    fallback branches behaviourally identical so environments without rg
    (typical CI runners) see the same hits.
    """
    flags = 0 if any(c.isupper() for c in query) else re.IGNORECASE
    try:
        pattern = re.compile(re.escape(query), flags)
    except re.error:
        return []

    results = []
    title_cache = {}
    for dirpath, dirnames, filenames in os.walk(path):
        # Skip .git
        if ".git" in dirnames:
            dirnames.remove(".git")
        # I-5: .kb-internal/ is plugin-managed, never searched.
        if ".kb-internal" in dirnames:
            dirnames.remove(".kb-internal")
        rel_dir = os.path.relpath(dirpath, path)
        if exclude_inbox and (rel_dir == "inbox" or rel_dir.startswith(
                "inbox" + os.sep)):
            continue
        for fname in filenames:
            if not fname.endswith(".md"):
                continue
            if glob_pattern and not _glob_match(fname, glob_pattern):
                continue
            fpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fpath, path)
            try:
                with open(fpath, "r", errors="replace") as f:
                    matches_in_file = 0
                    for i, line in enumerate(f, 1):
                        if pattern.search(line):
                            if fpath not in title_cache:
                                title_cache[fpath] = _extract_title(fpath)
                            results.append({
                                "path": rel_path,
                                "line": i,
                                "title": title_cache[fpath],
                                "snippet": line.strip()[:200],
                                "match_count": 1,
                            })
                            matches_in_file += 1
                            if matches_in_file >= _DEFAULT_MAX_PER_FILE:
                                break
            except Exception:
                continue
            if len(results) >= max_results:
                return results
    return results


def _glob_match(filename, pattern):
    """Shell-style glob match (e.g. *.md, decision-*.md)."""
    return fnmatch.fnmatch(filename, pattern)


def search_kb(path, query, max_results=20, glob_pattern=None,
              exclude_inbox=False):
    """Search a single KB. Returns list of result dicts."""
    if _rg_available():
        return _search_rg(path, query, max_results, glob_pattern,
                          exclude_inbox)
    return _search_python(path, query, max_results, glob_pattern,
                          exclude_inbox)
