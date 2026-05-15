"""Lexical search: rg-first with Python fallback."""

import fnmatch
import json
import os
import re
import shutil
import subprocess


def _rg_available():
    return shutil.which("rg") is not None


def _search_rg(path, query, max_results=20, glob_pattern=None,
               exclude_inbox=False):
    """Search using ripgrep. Returns list of result dicts."""
    args = [
        "rg", "--json", "--max-count", "1",
        "--glob", "!.git",
    ]
    if exclude_inbox:
        args += ["--glob", "!inbox/"]
    if glob_pattern:
        args += ["--glob", glob_pattern]
    args += [query, path]

    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    results = []
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
        # Derive a title from the filename
        title = os.path.splitext(os.path.basename(rel_path))[0].replace(
            "-", " "
        ).replace("_", " ").title()
        results.append({
            "path": rel_path,
            "line": line_number,
            "title": title,
            "snippet": snippet[:200],
            "match_count": 1,
        })
        if len(results) >= max_results:
            break
    return results


def _search_python(path, query, max_results=20, glob_pattern=None,
                   exclude_inbox=False):
    """Fallback: walk directory and search .md files with re."""
    try:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
    except re.error:
        return []

    results = []
    for dirpath, dirnames, filenames in os.walk(path):
        # Skip .git
        if ".git" in dirnames:
            dirnames.remove(".git")
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
                    for i, line in enumerate(f, 1):
                        if pattern.search(line):
                            title = os.path.splitext(fname)[0].replace(
                                "-", " "
                            ).replace("_", " ").title()
                            results.append({
                                "path": rel_path,
                                "line": i,
                                "title": title,
                                "snippet": line.strip()[:200],
                                "match_count": 1,
                            })
                            break  # one match per file
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
