"""KB Registry CLI — all subcommands composed here."""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

from . import __version__
from .config import (
    ConfigError,
    add_kb,
    find_kb,
    get_default_kb,
    load_config,
    make_kb_entry,
    remove_kb,
    resolve_config_path,
    resolve_default_kb_name,
    save_config,
)
from .git_ops import (
    git_add_all,
    git_add_files,
    git_add_remote,
    git_clone,
    git_commit,
    git_commit_files,
    git_current_branch,
    git_has_commits,
    git_has_remote,
    git_init,
    git_is_dirty,
    git_is_repo,
    git_log_oneline,
    git_pull_rebase,
    git_push,
    git_remote_url,
    git_status_porcelain,
)
from .kb_template import create_kb, validate_kb_contract
from .metrics import track_command
from .safety import (
    check_binary,
    check_canonical_write,
    check_large_file,
    check_path_traversal,
)
from .search import _extract_title, search_kb

# Exit codes
EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_ARGS = 2
EXIT_SAFETY = 3
EXIT_GIT = 4

# Output limits
DEFAULT_BRIEF_MAX = 12000
DEFAULT_OPEN_MAX = 20000
DEFAULT_SEARCH_MAX = 20

# Suggested values for the `--kind` flag on `kb stage`. The CLI accepts any
# string — these are starting points the consolidation research finds useful,
# not an enum. Agents may invent KB-specific kinds (`hypothesis`,
# `open-question`, `benchmark`, ...) and write them straight into frontmatter.
SUGGESTED_STAGE_KINDS = [
    "decision", "domain-fact", "codebase-fact",
    "runbook-note", "retrospective", "followup", "raw-note",
]


def _output(data, as_json):
    """Print data as JSON or plain text."""
    if as_json:
        print(json.dumps(data, indent=2, default=str))
    elif isinstance(data, str):
        print(data)
    elif isinstance(data, list):
        for item in data:
            print(item)
    elif isinstance(data, dict):
        for k, v in data.items():
            print(f"{k}: {v}")


def _resolve_kb(config, name):
    """Resolve KB by name or fall back to the project/user default.

    Order when name is empty:
      1. $CLAUDE_PLUGIN_OPTION_DEFAULT_KB (project- or user-scope pluginConfigs)
      2. The KB entry marked `"default": true` in the registry.

    Returns (kb_entry, error_msg).
    """
    if name:
        kb = find_kb(config, name)
        if not kb:
            return None, f"KB '{name}' not found in registry."
        return kb, None
    plugin_default = resolve_default_kb_name()
    if plugin_default:
        kb = find_kb(config, plugin_default)
        if not kb:
            return None, (f"KB '{plugin_default}' (from "
                          "CLAUDE_PLUGIN_OPTION_DEFAULT_KB) not found in "
                          "registry.")
        return kb, None
    kb = get_default_kb(config)
    if not kb:
        return None, "No KB specified and no default configured."
    return kb, None


def _slugify(text, max_len=40):
    """Simple slugification."""
    slug = ""
    for ch in text.lower():
        if ch.isalnum():
            slug += ch
        elif ch in " -_/" and slug and slug[-1] != "-":
            slug += "-"
    return slug.strip("-")[:max_len] or "note"


def _url_slug(url):
    """Derive a filename slug from a URL: last path segment, fallback to host."""
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if path:
            return _slugify(path)
        if parsed.netloc:
            return _slugify(parsed.netloc)
    except Exception:
        pass
    return "url"


def _metrics_path(config):
    return config.get("metrics_path",
                      os.path.expanduser(
                          "~/.local/state/kb-registry/events.jsonl"))


def _first_body_line(path):
    """Return the first non-blank line *after* YAML frontmatter, or ''."""
    try:
        with open(path, "r", errors="replace") as f:
            in_fm = False
            seen_open = False
            for raw in f:
                line = raw.rstrip("\n")
                if line.strip() == "---":
                    if not seen_open:
                        in_fm = True
                        seen_open = True
                        continue
                    if in_fm:
                        in_fm = False
                        continue
                if in_fm:
                    continue
                if line.strip():
                    return line.strip()[:200]
    except Exception:
        pass
    return ""


def _read_frontmatter(path):
    """Best-effort YAML-ish frontmatter parse. Returns dict of str values.

    Recognises double-quoted strings (the format kb stage emits). Skips
    `null` / empty values. Stops at the second `---` line.
    """
    out = {}
    try:
        with open(path, "r", errors="replace") as f:
            first = f.readline().rstrip("\n")
            if first.strip() != "---":
                return out
            for line in f:
                line = line.rstrip("\n")
                if line.strip() == "---":
                    break
                if ":" not in line:
                    continue
                k, _, v = line.partition(":")
                k = k.strip()
                v = v.strip()
                if v.startswith('"') and v.endswith('"'):
                    v = v[1:-1].replace('\\"', '"').replace("\\\\", "\\")
                elif v.startswith("'") and v.endswith("'"):
                    v = v[1:-1]
                if v in ("", "null"):
                    continue
                out[k] = v
    except Exception:
        pass
    return out


# --- Subcommands ---


def cmd_bootstrap(args, config, config_path):
    kb_name = args.name
    if find_kb(config, kb_name) and not args.force:
        print(f"Error: KB '{kb_name}' already registered. Use --force.",
              file=sys.stderr)
        return EXIT_ARGS

    # Resolve path
    if args.path:
        kb_path = os.path.abspath(args.path)
    else:
        root = config.get("default_kb_root",
                          os.path.expanduser("~/knowledge"))
        kb_path = os.path.join(root, f"{kb_name}-kb")

    remote = args.remote

    with track_command(_metrics_path(config), "bootstrap", kb=kb_name) as ctx:
        ctx["path"] = kb_path

        # Clone or create
        if remote and (not os.path.exists(kb_path) or
                       not os.listdir(kb_path)):
            # Remote provided and target is missing/empty: clone
            ok, out, rc = git_clone(remote, kb_path)
            if not ok:
                print(f"Error: git clone failed: {out}", file=sys.stderr)
                ctx["success"] = False
                return EXIT_GIT
            # Warn if cloned repo does not satisfy the KB contract.
            missing = validate_kb_contract(kb_path)
            if missing:
                print(f"Warning: cloned KB is missing contract items: "
                      f"{', '.join(missing)}", file=sys.stderr)
        else:
            if os.path.exists(kb_path) and os.listdir(kb_path):
                if not args.force:
                    print(f"Error: '{kb_path}' is not empty. Use --force.",
                          file=sys.stderr)
                    ctx["success"] = False
                    return EXIT_ARGS
            create_kb(kb_path, kb_name)
            # Git init + initial commit
            if not git_is_repo(kb_path):
                git_init(kb_path)
            git_add_all(kb_path)
            ok, out, rc = git_commit(kb_path,
                                     "chore: initialize knowledge base")
            if not ok and "nothing to commit" not in out:
                print(f"Warning: initial commit issue: {out}", file=sys.stderr)

            # Set remote origin if --remote provided on local create
            if remote:
                git_add_remote(kb_path, "origin", remote)
                if args.push:
                    ok, out, rc = git_push(kb_path)
                    if not ok:
                        print(f"Warning: push failed: {out}", file=sys.stderr)

        # Only record remote in registry if git actually has it
        actual_remote = git_remote_url(kb_path) if git_is_repo(kb_path) else None

        # Register
        is_first = len(config.get("kbs", [])) == 0
        if find_kb(config, kb_name):
            remove_kb(config, kb_name)
        entry = make_kb_entry(
            kb_name, kb_path, remote=actual_remote,
            description=args.description or "",
            default=is_first or args.default,
        )
        add_kb(config, entry)
        save_config(config, config_path)

    print(f"Bootstrapped KB '{kb_name}' at {kb_path}")
    if is_first:
        print(f"  (set as default)")
    return EXIT_OK


def cmd_add(args, config, config_path):
    kb_name = args.name
    kb_path = os.path.abspath(args.path)

    with track_command(_metrics_path(config), "add", kb=kb_name) as ctx:
        ctx["path"] = kb_path

        if find_kb(config, kb_name) and not args.force:
            print(f"Error: KB '{kb_name}' already registered. Use --force.",
                  file=sys.stderr)
            ctx["success"] = False
            return EXIT_ARGS

        if not os.path.isdir(kb_path):
            print(f"Error: path does not exist: {kb_path}", file=sys.stderr)
            ctx["success"] = False
            return EXIT_ARGS

        missing = validate_kb_contract(kb_path)
        if missing:
            if not args.force:
                print(f"Error: invalid KB contract — missing: "
                      f"{', '.join(missing)}", file=sys.stderr)
                print("Use --force to register anyway.", file=sys.stderr)
                ctx["success"] = False
                return EXIT_ARGS
            print(f"Warning: missing contract files (--force): "
                  f"{', '.join(missing)}", file=sys.stderr)

        if not git_is_repo(kb_path):
            print(f"Warning: '{kb_path}' is not a git repo.", file=sys.stderr)

        if find_kb(config, kb_name):
            remove_kb(config, kb_name)
        entry = make_kb_entry(
            kb_name, kb_path, remote=args.remote,
            description=args.description or "",
            default=args.default,
        )
        add_kb(config, entry)
        save_config(config, config_path)

    print(f"Added KB '{kb_name}' at {kb_path}")
    return EXIT_OK


def cmd_remove(args, config, config_path):
    kb_name = args.name

    with track_command(_metrics_path(config), "remove", kb=kb_name) as ctx:
        kb = find_kb(config, kb_name)
        if not kb:
            print(f"Error: KB '{kb_name}' not found.", file=sys.stderr)
            ctx["success"] = False
            return EXIT_ARGS

        kb_path = kb["path"]

        if args.delete_local:
            if not args.yes:
                print("Error: --delete-local requires --yes.", file=sys.stderr)
                ctx["success"] = False
                return EXIT_ARGS
            if os.path.isdir(kb_path):
                if git_is_repo(kb_path) and git_is_dirty(kb_path):
                    if not args.force:
                        print(f"Error: KB has uncommitted changes. "
                              f"Use --force.", file=sys.stderr)
                        ctx["success"] = False
                        return EXIT_GIT
                import shutil
                shutil.rmtree(kb_path)
                print(f"Deleted {kb_path}")

        remove_kb(config, kb_name)
        save_config(config, config_path)

    print(f"Removed KB '{kb_name}' from registry.")
    return EXIT_OK


def cmd_list(args, config, config_path):
    with track_command(_metrics_path(config), "list") as ctx:
        kbs = config.get("kbs", [])
        ctx["result_count"] = len(kbs)

        if args.json:
            _output({"kbs": kbs}, True)
            return EXIT_OK

        if not kbs:
            print("No KBs registered.")
            return EXIT_OK

        for kb in kbs:
            default = " (default)" if kb.get("default") else ""
            exists = "OK" if os.path.isdir(kb["path"]) else "MISSING"
            desc = f' — {kb["description"]}' if kb.get("description") else ""
            print(f"  {kb['name']}{default} [{exists}] {kb['path']}{desc}")

    return EXIT_OK


def cmd_status(args, config, config_path):
    names = []
    if args.kb:
        names = [args.kb]
    elif args.all:
        names = [kb["name"] for kb in config.get("kbs", [])]
    else:
        names = [kb["name"] for kb in config.get("kbs", [])]

    results = []
    for name in names:
        kb = find_kb(config, name)
        if not kb:
            results.append({"name": name, "error": "not found"})
            continue

        path = kb["path"]
        info = {
            "name": name,
            "path": path,
            "exists": os.path.isdir(path),
            "remote": kb.get("remote"),
            "default": kb.get("default", False),
        }

        if info["exists"]:
            info["is_git_repo"] = git_is_repo(path)
            if info["is_git_repo"]:
                info["branch"] = git_current_branch(path)
                info["dirty"] = git_is_dirty(path)
                info["remote_url"] = git_remote_url(path)
                info["recent_commits"] = git_log_oneline(path, 3)
            info["missing_contract"] = validate_kb_contract(path)

        results.append(info)

    with track_command(_metrics_path(config), "status",
                       kb=args.kb) as ctx:
        ctx["result_count"] = len(results)

        if args.json:
            _output(results, True)
        else:
            for info in results:
                if "error" in info:
                    print(f"  {info['name']}: {info['error']}")
                    continue
                status_parts = []
                if not info["exists"]:
                    status_parts.append("PATH MISSING")
                else:
                    if info.get("is_git_repo"):
                        branch = info.get("branch", "?")
                        dirty = "dirty" if info.get("dirty") else "clean"
                        status_parts.append(f"git:{branch} ({dirty})")
                        if info.get("remote_url"):
                            status_parts.append(
                                f"remote:{info['remote_url']}")
                    else:
                        status_parts.append("not a git repo")
                    if info.get("missing_contract"):
                        status_parts.append(
                            f"missing: {','.join(info['missing_contract'])}")
                default = " (default)" if info.get("default") else ""
                print(f"  {info['name']}{default}: "
                      f"{' | '.join(status_parts)}")
                print(f"    {info['path']}")

    return EXIT_OK


def cmd_pending(args, config, config_path):
    """List unprocessed inbox material across a KB.

    Walks `<kb>/inbox/`, skipping `inbox/processed/` and `README.md`.
    For each note, reports kind (from frontmatter, falling back to
    'document' for files with no frontmatter) and a display title (from
    frontmatter `title`, first H1, or filename slug).
    """
    kb, err = _resolve_kb(config, args.kb)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return EXIT_ARGS

    inbox_root = os.path.join(kb["path"], "inbox")
    if not os.path.isdir(inbox_root):
        print(f"Error: inbox/ missing under {kb['path']}", file=sys.stderr)
        return EXIT_FAILURE

    items = []
    for dirpath, dirnames, filenames in os.walk(inbox_root):
        rel_dir = os.path.relpath(dirpath, inbox_root)
        if rel_dir == "processed" or rel_dir.startswith(
                "processed" + os.sep):
            dirnames[:] = []
            continue
        for fname in sorted(filenames):
            if not fname.endswith(".md") or fname == "README.md":
                continue
            full = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full, kb["path"])
            meta = _read_frontmatter(full)
            kind = meta.get("kind") or "document"
            title = meta.get("title") or _extract_title(full)
            items.append({
                "path": rel_path,
                "kind": kind,
                "title": title,
                "created_at": meta.get("created_at", ""),
                "url": meta.get("url"),
            })

    # Most recent first; created_at is ISO and sorts lexically.
    items.sort(key=lambda x: x.get("created_at") or x["path"], reverse=True)

    if args.max_results:
        items = items[:args.max_results]

    with track_command(_metrics_path(config), "pending",
                       kb=kb["name"]) as ctx:
        ctx["result_count"] = len(items)

        if args.json:
            _output(items, True)
            return EXIT_OK

        if not items:
            print("No pending inbox material.")
            return EXIT_OK

        for item in items:
            print(f"  [{item['kind']}] {item['title']}")
            print(f"    {item['path']}")
            if item.get("url"):
                print(f"    {item['url']}")

    return EXIT_OK


def cmd_remember(args, config, config_path):
    """Append a short single-paragraph memory to <kb>/notes/.

    Notes are append-only: kb-dream never touches them. Use this for
    project / domain / codebase facts that are expensive to re-derive
    but too small to deserve a canonical page in knowledge/.

    For personal user preferences ("I like X", "I prefer rebase"),
    use Claude's auto-memory instead — the KB is not the right layer.
    """
    kb, err = _resolve_kb(config, args.kb)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return EXIT_ARGS

    kb_path = kb["path"]
    if not os.path.isdir(kb_path):
        print(f"Error: KB path does not exist: {kb_path}", file=sys.stderr)
        return EXIT_FAILURE

    if not args.text:
        print("Error: <text> is required.", file=sys.stderr)
        return EXIT_ARGS

    tags = []
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    with track_command(_metrics_path(config), "remember",
                       kb=kb["name"]) as ctx:
        ctx["tag_count"] = len(tags)

        now = datetime.now(timezone.utc).astimezone()
        date_dir = now.strftime("%Y/%m")
        timestamp_slug = now.strftime("%Y%m%d-%H%M%S")
        slug = _slugify(args.text[:60])
        filename = f"{timestamp_slug}-{slug}.md"
        rel_path = os.path.join("notes", date_dir, filename)

        # notes/ must exist (part of the KB contract).
        notes_root = os.path.join(kb_path, "notes")
        if not os.path.isdir(notes_root):
            print(f"Error: notes/ missing under {kb_path}. Run "
                  f"`mkdir -p {notes_root}` or re-bootstrap.",
                  file=sys.stderr)
            ctx["success"] = False
            return EXIT_FAILURE

        full_path = os.path.join(kb_path, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        def _yaml_str(s):
            return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

        fm_lines = ["---"]
        fm_lines.append(f'created_at: {_yaml_str(now.isoformat())}')
        if tags:
            tags_yaml = ", ".join(_yaml_str(t) for t in tags)
            fm_lines.append(f"tags: [{tags_yaml}]")
        fm_lines.append("---")
        fm_lines.append("")
        content = "\n".join(fm_lines) + args.text
        if not content.endswith("\n"):
            content += "\n"
        with open(full_path, "w") as f:
            f.write(content)

        ctx["path"] = rel_path

        committed = False
        if not args.no_commit and git_is_repo(kb_path):
            git_add_files(kb_path, [rel_path])
            ok, out, rc = git_commit_files(
                kb_path, "kb: remember note", [rel_path]
            )
            committed = ok
            if not ok:
                print(f"Warning: commit failed: {out}", file=sys.stderr)

        if args.json:
            _output({
                "kb": kb["name"],
                "path": rel_path,
                "tags": tags,
                "committed": committed,
            }, True)
        else:
            print(f"Remembered: {rel_path}")

    return EXIT_OK


def _load_index_json(kb_path):
    """Return the parsed `index.json` list for a KB, or None if missing /
    malformed."""
    p = os.path.join(kb_path, INDEX_FILENAME)
    if not os.path.isfile(p):
        return None
    try:
        with open(p, "r", errors="replace") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, list) else None


def _score_index_entry(entry, query_lc):
    """Higher score = stronger match. Title hits dominate tags and summaries."""
    score = 0
    title = (entry.get("title") or "").lower()
    summary = (entry.get("summary") or "").lower()
    tags = [str(t).lower() for t in entry.get("tags") or []]
    if query_lc in title:
        score += 3
    if any(query_lc == t for t in tags):
        score += 2
    elif any(query_lc in t for t in tags):
        score += 1
    if query_lc in summary:
        score += 1
    return score


def _entry_to_result(entry, kb_name, source):
    return {
        "kb": kb_name,
        "path": entry.get("path", ""),
        "title": entry.get("title", ""),
        "tags": entry.get("tags", []) or [],
        "snippet": entry.get("summary", "") or "",
        "source": source,  # "index" or "body"
    }


def _log_append(kb_path, line):
    """Append a single bullet line to LOG.md, ensuring trailing newline."""
    log_path = os.path.join(kb_path, "LOG.md")
    existing = ""
    if os.path.isfile(log_path):
        with open(log_path, "r", errors="replace") as f:
            existing = f.read()
    sep = "" if existing.endswith("\n") or not existing else "\n"
    with open(log_path, "a") as f:
        f.write(sep + line + "\n")


def _index_md_links_path(kb_path, rel_path):
    """True if INDEX.md contains a Markdown link pointing at rel_path."""
    p = os.path.join(kb_path, "INDEX.md")
    if not os.path.isfile(p):
        return False
    try:
        with open(p, "r", errors="replace") as f:
            text = f.read()
    except OSError:
        return False
    # Look for `](<rel_path>` (matches both `(./rel)` after normalisation).
    needle_plain = f"]({rel_path}"
    needle_dot = f"](./{rel_path}"
    return needle_plain in text or needle_dot in text


FORGET_PROTECTED_FILES = {
    "BRIEF.md", "AGENTS.md", "INDEX.md", "LOG.md", "index.json", "README.md",
    ".gitignore",
}


def cmd_forget(args, config, config_path):
    """Remove a single page from an indexable section.

    Git remembers the deletion, so this is a soft forget for retrieval but a
    hard remove for the agent's working surface. Appends a one-line LOG.md
    entry capturing date + optional reason. Index.json is not auto-rebuilt
    (run `kb reindex`).
    """
    kb, err = _resolve_kb(config, args.kb)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return EXIT_ARGS

    kb_path = kb["path"]
    if not os.path.isdir(kb_path):
        print(f"Error: KB path does not exist: {kb_path}", file=sys.stderr)
        return EXIT_FAILURE

    raw_target = args.path
    if not raw_target:
        print("Error: <path> is required.", file=sys.stderr)
        return EXIT_ARGS

    # Normalise to a relative POSIX path; reject absolute and traversal.
    # Note: a literal "./" prefix is stripped, but ".." segments are
    # preserved so check_path_traversal catches them.
    rel = raw_target.replace(os.sep, "/")
    if rel.startswith("./"):
        rel = rel[2:]
    if check_path_traversal(kb_path, rel):
        print(f"Error: path escapes KB root: {raw_target}", file=sys.stderr)
        return EXIT_SAFETY

    # Scope: only auto-discovered indexable sections (anything *not* under
    # inbox/, sources/, tools/, .git/, or a non-section top-level dir).
    # Mirrors what `kb reindex` indexes, so `forget` and the index stay
    # consistent as agents add new top-level dirs.
    allowed_sections = _discover_indexable_sections(kb_path)
    if not any(rel.startswith(section + "/") for section in allowed_sections):
        if allowed_sections:
            hint = " or ".join(allowed_sections)
            print(
                f"Error: kb forget only operates under indexable sections "
                f"({hint}/). Got: {rel}",
                file=sys.stderr,
            )
        else:
            print(
                "Error: KB has no indexable sections — nothing to forget.",
                file=sys.stderr,
            )
        return EXIT_ARGS

    # Defense against forgetting contract files even if they somehow ended up
    # nested (they shouldn't).
    if os.path.basename(rel) in FORGET_PROTECTED_FILES:
        print(f"Error: refusing to forget protected file: {rel}",
              file=sys.stderr)
        return EXIT_SAFETY

    abs_target = os.path.join(kb_path, rel)
    if not os.path.isfile(abs_target):
        print(f"Error: file not found: {rel}", file=sys.stderr)
        return EXIT_FAILURE

    reason = " ".join((args.reason or "").split()) or "(no reason given)"
    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    log_line = f"- {today}: forgot `{rel}` — {reason}"
    indexed_warn = _index_md_links_path(kb_path, rel)

    if args.dry_run:
        if args.json:
            _output({
                "kb": kb["name"],
                "dry_run": True,
                "path": rel,
                "reason": reason,
                "log_line": log_line,
                "index_md_references": indexed_warn,
            }, True)
        else:
            print(f"Would forget {rel}")
            print(f"  LOG.md entry: {log_line}")
            if indexed_warn:
                print(f"  Warning: INDEX.md still references {rel} — edit by hand.")
            print("  index.json will be stale until `kb reindex`.")
        return EXIT_OK

    with track_command(_metrics_path(config), "forget",
                       kb=kb["name"]) as ctx:
        ctx["path"] = rel
        ctx["reason"] = reason
        ctx["index_md_references"] = indexed_warn

        try:
            os.remove(abs_target)
        except OSError as exc:
            print(f"Error: could not remove {rel}: {exc}", file=sys.stderr)
            ctx["success"] = False
            return EXIT_FAILURE

        _log_append(kb_path, log_line)

        committed = False
        if not args.no_commit and git_is_repo(kb_path):
            # `git add` stages deletions in modern git, so this picks up both
            # the LOG.md modification and the removed file.
            git_add_files(kb_path, ["LOG.md", rel])
            ok, out, rc = git_commit_files(
                kb_path, f"kb: forget {rel}", ["LOG.md", rel]
            )
            committed = ok
            if not ok and "nothing to commit" not in out:
                print(f"Warning: commit failed: {out}", file=sys.stderr)

        if args.json:
            _output({
                "kb": kb["name"],
                "path": rel,
                "reason": reason,
                "log_line": log_line,
                "index_md_references": indexed_warn,
                "committed": committed,
            }, True)
        else:
            print(f"Forgot {rel}")
            if indexed_warn:
                print(f"  Warning: INDEX.md still references {rel} — edit by hand.",
                      file=sys.stderr)
            print("  Tip: `kb reindex` to refresh index.json.",
                  file=sys.stderr)

    return EXIT_OK


def cmd_recall(args, config, config_path):
    """Search synthesised material in indexable sections, excluding inbox/.

    Prefers `index.json` (built by `kb reindex`) for fast title/tag/summary
    matches, then merges body-grep hits underneath. Falls back to body grep
    alone when `index.json` is absent — with a nudge to run `kb reindex`.
    """
    if args.kb:
        kb, err = _resolve_kb(config, args.kb)
        if err:
            print(f"Error: {err}", file=sys.stderr)
            return EXIT_ARGS
        targets = [kb]
    else:
        targets = config.get("kbs", [])
        if not targets:
            print("No KBs registered.", file=sys.stderr)
            return EXIT_ARGS

    max_results = args.max_results or DEFAULT_SEARCH_MAX

    if not args.query and not args.tag:
        print("Error: provide --query or --tag.", file=sys.stderr)
        return EXIT_ARGS

    all_results = []
    missing_index_kbs = []
    for kb in targets:
        kb_path = kb["path"]
        if not os.path.isdir(kb_path):
            continue

        index = _load_index_json(kb_path)
        if index is None:
            missing_index_kbs.append(kb["name"])

        # --- Tag path: index.json is authoritative when present. ---
        if args.tag and not args.query:
            tag = args.tag.strip()
            if index is not None:
                for entry in index:
                    tags = [str(t) for t in entry.get("tags") or []]
                    if tag in tags:
                        all_results.append(
                            _entry_to_result(entry, kb["name"], "index")
                        )
                continue
            # Fallback: walk indexable sections and inspect frontmatter.
            for section in _discover_indexable_sections(kb_path):
                section_root = os.path.join(kb_path, section)
                for dp, dns, fns in os.walk(section_root):
                    dns[:] = sorted(d for d in dns if not d.startswith("."))
                    for fname in sorted(fns):
                        if (not fname.endswith(".md") or
                                fname == "README.md" or
                                fname.startswith(".")):
                            continue
                        full = os.path.join(dp, fname)
                        meta = _read_frontmatter(full)
                        raw_tags = meta.get("tags", "")
                        if not raw_tags:
                            continue
                        cleaned = raw_tags.strip().lstrip("[").rstrip("]")
                        file_tags = [
                            t.strip().strip('"').strip("'")
                            for t in cleaned.split(",")
                        ]
                        if tag not in file_tags:
                            continue
                        rel_path = os.path.relpath(full, kb_path)
                        all_results.append({
                            "kb": kb["name"],
                            "path": rel_path,
                            "title": _extract_title(full),
                            "tags": file_tags,
                            "snippet": _first_body_line(full),
                            "source": "fallback",
                        })
            continue

        # --- Query path: rank index hits, then merge body-grep hits. ---
        query = args.query
        query_lc = query.lower()
        seen_paths = set()

        if index is not None:
            scored = []
            for entry in index:
                s = _score_index_entry(entry, query_lc)
                if s > 0:
                    scored.append((s, entry))
            scored.sort(key=lambda x: (-x[0], x[1].get("path", "")))
            for _, entry in scored:
                result = _entry_to_result(entry, kb["name"], "index")
                all_results.append(result)
                seen_paths.add(result["path"])

        # Body grep across indexable sections. Skip paths already surfaced
        # by the index so we don't duplicate rows.
        for sub_dir in _discover_indexable_sections(kb_path):
            scoped_root = os.path.join(kb_path, sub_dir)
            if not os.path.isdir(scoped_root):
                continue
            sub = search_kb(
                scoped_root, query,
                max_results=max_results,
                glob_pattern=None,
                exclude_inbox=False,
            )
            for r in sub:
                r["path"] = os.path.join(sub_dir, r["path"])
                if r["path"] in seen_paths:
                    continue
                r["kb"] = kb["name"]
                r["source"] = "body"
                all_results.append(r)
                seen_paths.add(r["path"])

        if len(all_results) >= max_results:
            break

    all_results = all_results[:max_results]

    with track_command(_metrics_path(config), "recall",
                       kb=args.kb) as ctx:
        ctx["query"] = args.query
        ctx["tag"] = args.tag
        ctx["result_count"] = len(all_results)
        ctx["missing_index"] = bool(missing_index_kbs)

        if args.json:
            _output(all_results, True)
            return EXIT_OK

        if not all_results:
            print("No results.")
            if missing_index_kbs:
                print(
                    f"Tip: `kb reindex {missing_index_kbs[0]}` to enable "
                    f"index-aware matches.", file=sys.stderr,
                )
            return EXIT_OK

        for r in all_results:
            kb_name = r.get("kb", "?")
            tags = r.get("tags")
            tags_str = f" [{', '.join(tags)}]" if tags else ""
            snippet = (r.get("snippet") or "")[:80]
            line = r.get("line")
            loc = f"{r['path']}" + (f":{line}" if line else "")
            marker = "*" if r.get("source") == "index" else " "
            print(f" {marker}[{kb_name}] {loc}{tags_str}  {snippet}")

        if missing_index_kbs:
            print(
                f"Tip: `kb reindex {missing_index_kbs[0]}` to enable "
                f"index-aware matches.", file=sys.stderr,
            )

    return EXIT_OK


def cmd_brief(args, config, config_path):
    kb, err = _resolve_kb(config, args.kb)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return EXIT_ARGS

    brief_path = os.path.join(kb["path"], "BRIEF.md")

    with track_command(_metrics_path(config), "brief",
                       kb=kb["name"]) as ctx:
        if not os.path.isfile(brief_path):
            print(f"Error: BRIEF.md not found at {brief_path}",
                  file=sys.stderr)
            ctx["success"] = False
            return EXIT_FAILURE

        with open(brief_path, "r") as f:
            content = f.read()

        max_chars = args.max_chars or DEFAULT_BRIEF_MAX
        truncated = len(content) > max_chars
        content = content[:max_chars]

        if args.json:
            _output({
                "kb": kb["name"],
                "path": "BRIEF.md",
                "content": content,
                "truncated": truncated,
                "chars": len(content),
            }, True)
        else:
            print(content)
            if truncated:
                print(f"\n[truncated at {max_chars} chars]")

    return EXIT_OK


def cmd_open(args, config, config_path):
    kb, err = _resolve_kb(config, args.kb)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return EXIT_ARGS

    rel_path = args.path
    if os.path.isabs(rel_path):
        print("Error: absolute paths not allowed. Use relative path.",
              file=sys.stderr)
        return EXIT_ARGS

    if check_path_traversal(kb["path"], rel_path):
        print("Error: path traversal detected.", file=sys.stderr)
        return EXIT_SAFETY

    full_path = os.path.join(kb["path"], rel_path)

    with track_command(_metrics_path(config), "open", kb=kb["name"]) as ctx:
        ctx["path"] = rel_path

        if not os.path.isfile(full_path):
            print(f"Error: file not found: {rel_path}", file=sys.stderr)
            ctx["success"] = False
            return EXIT_FAILURE

        with open(full_path, "r", errors="replace") as f:
            content = f.read()

        max_chars = args.max_chars or DEFAULT_OPEN_MAX
        truncated = len(content) > max_chars
        content = content[:max_chars]

        if args.json:
            _output({
                "kb": kb["name"],
                "path": rel_path,
                "content": content,
                "truncated": truncated,
                "chars": len(content),
            }, True)
        else:
            print(content)
            if truncated:
                print(f"\n[truncated at {max_chars} chars]")

    return EXIT_OK


def cmd_search(args, config, config_path):
    query = args.query

    # Determine which KBs to search
    if args.kb:
        kb, err = _resolve_kb(config, args.kb)
        if err:
            print(f"Error: {err}", file=sys.stderr)
            return EXIT_ARGS
        targets = [kb]
    else:
        targets = config.get("kbs", [])
        if not targets:
            print("No KBs registered.", file=sys.stderr)
            return EXIT_ARGS

    max_results = args.max_results or DEFAULT_SEARCH_MAX
    exclude_inbox = args.exclude_inbox

    all_results = []
    for kb in targets:
        if not os.path.isdir(kb["path"]):
            continue
        results = search_kb(
            kb["path"], query, max_results=max_results,
            glob_pattern=args.glob,
            exclude_inbox=exclude_inbox,
        )
        for r in results:
            r["kb"] = kb["name"]
        all_results.extend(results)
        if len(all_results) >= max_results:
            all_results = all_results[:max_results]
            break

    with track_command(_metrics_path(config), "search",
                       kb=args.kb) as ctx:
        ctx["query"] = query
        ctx["result_count"] = len(all_results)

        if args.json:
            _output(all_results, True)
        else:
            if not all_results:
                print(f"No results for '{query}'.")
            else:
                for r in all_results:
                    print(f"  [{r['kb']}] {r['path']}:{r['line']}"
                          f"  {r['snippet'][:80]}")

    return EXIT_OK


def cmd_stage(args, config, config_path):
    """Stage one of:
      - a note   (agent-written text, frontmatter + body) via --note
      - a document (any text file, copied verbatim, no frontmatter) via --file
      - a URL pointer (fetched/summarised later by kb-dream) via --url

    --note may accompany --url to provide a description; otherwise --file,
    --note, and --url are mutually exclusive primary inputs.
    """
    kb, err = _resolve_kb(config, args.kb)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return EXIT_ARGS

    kb_path = kb["path"]
    if not os.path.isdir(kb_path):
        print(f"Error: KB path does not exist: {kb_path}", file=sys.stderr)
        return EXIT_FAILURE

    is_file = bool(args.file)
    is_url = bool(args.url)
    is_note_text = bool(args.note)

    if is_file and (is_note_text or is_url):
        print("Error: --file is mutually exclusive with --note and --url.",
              file=sys.stderr)
        return EXIT_ARGS
    if not (is_file or is_url or is_note_text):
        print("Error: one of --note, --file, --url is required.",
              file=sys.stderr)
        return EXIT_ARGS

    if is_url and not re.match(r"^https?://", args.url):
        print("Error: --url must start with http:// or https://.",
              file=sys.stderr)
        return EXIT_ARGS

    # Resolve content + slug source.
    if is_file:
        src = os.path.abspath(args.file)
        if not os.path.isfile(src):
            print(f"Error: file not found: {src}", file=sys.stderr)
            return EXIT_ARGS
        if check_binary(src):
            print("Error: binary files not supported.", file=sys.stderr)
            return EXIT_ARGS
        if check_large_file(src):
            print("Warning: large file.", file=sys.stderr)
            if not args.force:
                return EXIT_ARGS
        with open(src, "r") as f:
            content = f.read()
        slug_source = os.path.splitext(os.path.basename(src))[0]
        if args.kind or args.title or args.source:
            print("Note: --kind/--title/--source are ignored for --file "
                  "(documents have no frontmatter).", file=sys.stderr)
    elif is_url:
        # Body is the optional --note description; may be empty.
        content = args.note if args.note else ""
        slug_source = _url_slug(args.url)
        if args.kind:
            print("Note: --kind is forced to 'url' for --url stages.",
                  file=sys.stderr)
    else:
        # Plain note.
        content = args.note
        title = args.title or ""
        slug_source = title if title else content[:60]

    if is_file:
        kind = None
    elif is_url:
        kind = "url"
    else:
        kind = args.kind or "raw-note"

    with track_command(_metrics_path(config), "stage", kb=kb["name"]) as ctx:
        if kind is not None:
            ctx["kind"] = kind

        now = datetime.now(timezone.utc).astimezone()
        date_dir = now.strftime("%Y/%m")
        timestamp_slug = now.strftime("%Y%m%d-%H%M%S")
        slug = _slugify(slug_source)
        filename = f"{timestamp_slug}-{slug}.md"
        rel_path = os.path.join("inbox", date_dir, filename)

        # Canonical write guard
        if check_canonical_write(kb_path, rel_path):
            print("Error: v0 does not write to knowledge/.", file=sys.stderr)
            ctx["success"] = False
            return EXIT_SAFETY

        full_path = os.path.join(kb_path, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        def _yaml_str(s):
            return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

        if is_file:
            # Document: verbatim.
            staged_content = content
        else:
            # Note or URL pointer: prepend YAML frontmatter.
            frontmatter = {
                "created_at": now.isoformat(),
                "kind": kind,
            }
            if is_url:
                frontmatter["url"] = args.url
            if args.source:
                frontmatter["source"] = args.source
            if args.title:
                frontmatter["title"] = args.title

            fm_lines = ["---"]
            for k, v in frontmatter.items():
                if v is None:
                    fm_lines.append(f'{k}: null')
                elif isinstance(v, str):
                    fm_lines.append(f'{k}: {_yaml_str(v)}')
                else:
                    fm_lines.append(f'{k}: {v}')
            fm_lines.append("---")
            fm_lines.append("")
            staged_content = "\n".join(fm_lines) + content

        if not staged_content.endswith("\n"):
            staged_content += "\n"

        with open(full_path, "w") as f:
            f.write(staged_content)

        ctx["path"] = rel_path

        # Auto-commit: stage only the new file, not unrelated changes
        committed = False
        if not args.no_commit and git_is_repo(kb_path):
            if is_file:
                commit_msg = f"kb: stage document {os.path.basename(src)}"
            elif is_url:
                commit_msg = f"kb: stage url pointer"
            else:
                commit_msg = f"kb: stage {kind} note"
            git_add_files(kb_path, [rel_path])
            ok, out, rc = git_commit_files(kb_path, commit_msg, [rel_path])
            committed = ok
            if not ok:
                print(f"Warning: commit failed: {out}", file=sys.stderr)

        mode = "document" if is_file else ("url" if is_url else "note")
        if args.json:
            payload = {
                "kb": kb["name"],
                "path": rel_path,
                "mode": mode,
                "committed": committed,
            }
            if is_url:
                payload["url"] = args.url
            if kind is not None:
                payload["kind"] = kind
            _output(payload, True)
        else:
            if is_file:
                print(f"Staged document: {rel_path}")
            elif is_url:
                print(f"Staged URL pointer: {rel_path}")
            else:
                print(f"Staged {kind} note: {rel_path}")

    return EXIT_OK


INDEX_FILENAME = "index.json"
# Top-level dirs that hold staged/raw material or non-content scaffolding,
# and so should not be indexed as canonical sections. Everything else under
# the KB root that contains .md files is auto-discovered as a section, so
# agents can grow `runbooks/`, `decisions/`, `specs/`, etc. without touching
# the CLI.
NON_INDEXED_SECTIONS = frozenset({"inbox", "sources", "tools"})
_INDEX_SUMMARY_MAX = 200


def _strip_frontmatter(content):
    """Return (frontmatter_dict, body) for a file's text content."""
    fm = {}
    body = content
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            block = content[3:end]
            body = content[end + len("\n---"):]
            if body.startswith("\n"):
                body = body[1:]
            for raw in block.splitlines():
                if ":" not in raw:
                    continue
                k, _, v = raw.partition(":")
                k = k.strip()
                v = v.strip()
                if v.startswith("[") and v.endswith("]"):
                    v = [t.strip().strip('"').strip("'")
                         for t in v[1:-1].split(",") if t.strip()]
                else:
                    if v.startswith('"') and v.endswith('"'):
                        v = v[1:-1].replace('\\"', '"').replace("\\\\", "\\")
                    elif v.startswith("'") and v.endswith("'"):
                        v = v[1:-1]
                if v in ("", "null"):
                    continue
                fm[k] = v
    return fm, body


def _summary_from_body(body, max_chars=_INDEX_SUMMARY_MAX):
    """Return the first body paragraph (after any H1), capped."""
    found_h1 = False
    paragraph = []
    for raw in body.splitlines():
        stripped = raw.strip()
        if stripped.startswith("# ") and not found_h1:
            found_h1 = True
            continue
        if not paragraph:
            if not stripped:
                continue
            if stripped.startswith(("##", "```", "---", "|", ">", "- ", "* ")):
                if found_h1:
                    # Treat structural lines as the start of "non-prose";
                    # skip until we either find prose or give up.
                    continue
                continue
            paragraph.append(stripped)
            continue
        if not stripped:
            break
        if stripped.startswith(("##", "```", "---", "|", ">")):
            break
        paragraph.append(stripped)
    text = " ".join(paragraph)
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + "..."
    return text


_WORD_STRIP_CODE = re.compile(r"```[\s\S]*?```")
_WORD_STRIP_INLINE = re.compile(r"`[^`]+`")
_WORD_STRIP_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_WORD_STRIP_MD = re.compile(r"[#*|>=\-]")


def _word_count(body):
    """Approximate word count, stripping common markdown noise."""
    t = _WORD_STRIP_CODE.sub("", body)
    t = _WORD_STRIP_INLINE.sub("", t)
    t = _WORD_STRIP_LINK.sub(r"\1", t)
    t = _WORD_STRIP_MD.sub(" ", t)
    return len(t.split())


def _git_last_modified(kb_path, rel_path):
    """Return ISO timestamp of last commit touching rel_path, or ''."""
    import subprocess
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", rel_path],
            capture_output=True, text=True, cwd=kb_path, check=False,
        )
        return (r.stdout or "").strip()
    except Exception:
        return ""


def _discover_indexable_sections(kb_path):
    """Return sorted top-level dirnames under kb_path that hold canonical
    content. Skips dotfiles, inbox/, sources/, tools/, and any dir whose tree
    contains no .md files. Lets agents grow new top-level sections without
    a CLI change."""
    if not os.path.isdir(kb_path):
        return []
    sections = []
    for entry in sorted(os.listdir(kb_path)):
        if entry.startswith("."):
            continue
        if entry in NON_INDEXED_SECTIONS:
            continue
        full = os.path.join(kb_path, entry)
        if not os.path.isdir(full):
            continue
        # Require at least one .md file in the tree to count as a section.
        has_md = False
        for dirpath, _, filenames in os.walk(full):
            if any(fn.endswith(".md") and fn != "README.md"
                   for fn in filenames):
                has_md = True
                break
        if has_md:
            sections.append(entry)
    return sections


def _collect_index_files(kb_path):
    """Yield (rel_path, section) for every .md file under auto-discovered
    sections, excluding README.md and dotfiles. Walks subdirectories so
    layouts like `notes/YYYY/MM/...` are included."""
    for section in _discover_indexable_sections(kb_path):
        root = os.path.join(kb_path, section)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for fn in sorted(filenames):
                if fn == "README.md" or fn.startswith("."):
                    continue
                if not fn.endswith(".md"):
                    continue
                abs_path = os.path.join(dirpath, fn)
                rel = os.path.relpath(abs_path, kb_path).replace(os.sep, "/")
                yield rel, section


def _build_index_entry(kb_path, rel, section):
    abs_path = os.path.join(kb_path, rel)
    try:
        with open(abs_path, "r", errors="replace") as f:
            content = f.read()
    except OSError:
        return None
    fm, body = _strip_frontmatter(content)
    title = _extract_title(abs_path)
    summary = _summary_from_body(body)
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    if not isinstance(tags, list):
        tags = []
    entry = {
        "path": rel,
        "title": title,
        "section": section,
        "tags": tags,
        "summary": summary,
        "word_count": _word_count(body),
        "last_modified": _git_last_modified(kb_path, rel),
    }
    kind = fm.get("kind")
    if isinstance(kind, str) and kind:
        entry["kind"] = kind
    return entry


def _build_index(kb_path):
    entries = []
    for rel, section in _collect_index_files(kb_path):
        e = _build_index_entry(kb_path, rel, section)
        if e is not None:
            entries.append(e)
    entries.sort(key=lambda x: x["path"])
    return entries


def cmd_reindex(args, config, config_path):
    """Build or refresh `<kb>/index.json`.

    Walks auto-discovered indexable sections and emits a structured
    manifest (path, title, section, tags, summary, word_count,
    last_modified, optional kind) that `kb recall` can consult before
    doing body grep. The agent-curated `INDEX.md` is left untouched.
    """
    kb, err = _resolve_kb(config, args.kb)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return EXIT_ARGS

    kb_path = kb["path"]
    if not os.path.isdir(kb_path):
        print(f"Error: KB path does not exist: {kb_path}", file=sys.stderr)
        return EXIT_FAILURE

    index_path = os.path.join(kb_path, INDEX_FILENAME)

    with track_command(_metrics_path(config), "reindex",
                       kb=kb["name"]) as ctx:
        entries = _build_index(kb_path)
        new_payload = json.dumps(entries, indent=2, ensure_ascii=False) + "\n"

        old_payload = ""
        old_count = 0
        if os.path.isfile(index_path):
            try:
                with open(index_path, "r", errors="replace") as f:
                    old_payload = f.read()
                try:
                    old_entries = json.loads(old_payload)
                    if isinstance(old_entries, list):
                        old_count = len(old_entries)
                except json.JSONDecodeError:
                    old_count = -1  # malformed; treat as a rebuild target
            except OSError:
                pass

        changed = new_payload != old_payload
        ctx["entries"] = len(entries)
        ctx["changed"] = changed
        ctx["dry_run"] = bool(args.dry_run)

        if args.dry_run:
            if args.json:
                _output({
                    "kb": kb["name"],
                    "dry_run": True,
                    "changed": changed,
                    "entries": len(entries),
                    "previous_entries": old_count,
                    "path": INDEX_FILENAME,
                }, True)
            else:
                print(f"Would write {len(entries)} entries to "
                      f"{INDEX_FILENAME} (was {old_count}). "
                      f"Changed: {changed}.")
            return EXIT_OK

        if not changed:
            if args.json:
                _output({
                    "kb": kb["name"],
                    "changed": False,
                    "entries": len(entries),
                    "path": INDEX_FILENAME,
                }, True)
            else:
                print(f"{INDEX_FILENAME} up to date ({len(entries)} entries).")
            return EXIT_OK

        with open(index_path, "w") as f:
            f.write(new_payload)

        committed = False
        if not args.no_commit and git_is_repo(kb_path):
            git_add_files(kb_path, [INDEX_FILENAME])
            ok, out, rc = git_commit_files(
                kb_path, "kb: rebuild index.json", [INDEX_FILENAME]
            )
            committed = ok
            if not ok and "nothing to commit" not in out:
                print(f"Warning: commit failed: {out}", file=sys.stderr)

        if args.json:
            _output({
                "kb": kb["name"],
                "changed": True,
                "entries": len(entries),
                "previous_entries": old_count,
                "path": INDEX_FILENAME,
                "committed": committed,
            }, True)
        else:
            delta = len(entries) - old_count if old_count >= 0 else len(entries)
            sign = "+" if delta >= 0 else ""
            print(f"Rebuilt {INDEX_FILENAME}: {len(entries)} entries "
                  f"({sign}{delta} from previous).")

    return EXIT_OK


def cmd_sync(args, config, config_path):
    if args.all:
        targets = config.get("kbs", [])
    else:
        kb, err = _resolve_kb(config, args.kb)
        if err:
            print(f"Error: {err}", file=sys.stderr)
            return EXIT_ARGS
        targets = [kb]

    exit_code = EXIT_OK
    for kb in targets:
        kb_path = kb["path"]
        name = kb["name"]

        with track_command(_metrics_path(config), "sync",
                           kb=name) as ctx:
            if not os.path.isdir(kb_path):
                print(f"  {name}: path missing ({kb_path})", file=sys.stderr)
                ctx["success"] = False
                exit_code = EXIT_FAILURE
                continue

            if not git_is_repo(kb_path):
                print(f"  {name}: not a git repo.", file=sys.stderr)
                ctx["success"] = False
                exit_code = EXIT_FAILURE
                continue

            if not git_has_remote(kb_path):
                if args.json:
                    _output({"kb": name, "status": "local-only"}, True)
                else:
                    print(f"  {name}: local-only (no remote configured).")
                continue

            # Dirty check — always stop on dirty working tree in v0
            if git_is_dirty(kb_path):
                print(f"  {name}: dirty working tree. "
                      f"Commit or stash changes first.",
                      file=sys.stderr)
                ctx["success"] = False
                exit_code = EXIT_GIT
                continue

            # Pull
            ok, out, rc = git_pull_rebase(kb_path)
            if not ok:
                print(f"  {name}: pull failed: {out}", file=sys.stderr)
                ctx["success"] = False
                exit_code = EXIT_GIT
                continue

            # Push if local commits
            if git_has_commits(kb_path):
                ok, out, rc = git_push(kb_path)
                if not ok:
                    print(f"  {name}: push failed: {out}", file=sys.stderr)
                    ctx["success"] = False
                    exit_code = EXIT_GIT
                    continue

            if args.json:
                _output({"kb": name, "status": "synced"}, True)
            else:
                print(f"  {name}: synced.")

    return exit_code


# --- Argument parser ---


def build_parser():
    # Shared flags inherited by every subcommand
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--config", dest="config_path", default=None,
                        help="Path to registry config file.")
    shared.add_argument("--json", action="store_true", default=False,
                        help="Machine-readable JSON output.")

    parser = argparse.ArgumentParser(
        prog="kb",
        description="kb — manage agent-maintained knowledge bases.",
    )
    parser.add_argument("--version", action="version",
                        version=f"kb {__version__}")
    # Top-level --config/--json for bare "kb --help" or "kb --json list"
    parser.add_argument("--config", dest="config_path", default=None,
                        help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true", default=False,
                        help=argparse.SUPPRESS)

    sub = parser.add_subparsers(dest="command")

    # bootstrap
    p = sub.add_parser("bootstrap", help="Create or clone a KB.",
                       parents=[shared])
    p.add_argument("name")
    p.add_argument("--path")
    p.add_argument("--remote")
    p.add_argument("--description")
    p.add_argument("--default", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--push", action="store_true")

    # add
    p = sub.add_parser("add", help="Register an existing KB.",
                       parents=[shared])
    p.add_argument("name")
    p.add_argument("--path", required=True)
    p.add_argument("--remote")
    p.add_argument("--description")
    p.add_argument("--default", action="store_true")
    p.add_argument("--force", action="store_true")

    # remove
    p = sub.add_parser("remove", help="Remove a KB from the registry.",
                       parents=[shared])
    p.add_argument("name")
    p.add_argument("--delete-local", action="store_true")
    p.add_argument("--yes", action="store_true")
    p.add_argument("--force", action="store_true")

    # list
    sub.add_parser("list", help="List configured KBs.", parents=[shared])

    # status
    p = sub.add_parser("status", help="Show registry and git status.",
                       parents=[shared])
    p.add_argument("kb", nargs="?")
    p.add_argument("--all", action="store_true")
    p.add_argument("--fetch", action="store_true")

    # pending
    p = sub.add_parser(
        "pending",
        help="List unprocessed inbox material (excludes inbox/processed/).",
        parents=[shared],
    )
    p.add_argument("kb", nargs="?")
    p.add_argument("--max-results", type=int)

    # remember
    p = sub.add_parser(
        "remember",
        help="Append a short single-paragraph memory to <kb>/notes/.",
        parents=[shared],
    )
    p.add_argument("text",
                   help="The fact to remember. Should be one sentence.")
    p.add_argument("--kb", dest="kb",
                   help="Target KB (defaults to the default KB).")
    p.add_argument("--tags", help="Comma-separated tag list.")
    p.add_argument("--no-commit", action="store_true")

    # recall
    p = sub.add_parser(
        "recall",
        help="Search synthesised material in indexable sections.",
        parents=[shared],
    )
    p.add_argument("kb", nargs="?")
    p.add_argument("--query", help="Lexical query.")
    p.add_argument("--tag", help="Restrict to notes carrying this tag.")
    p.add_argument("--max-results", type=int)

    # brief
    p = sub.add_parser("brief", help="Print compact KB summary.",
                       parents=[shared])
    p.add_argument("kb", nargs="?")
    p.add_argument("--max-chars", type=int)

    # open
    p = sub.add_parser("open", help="Open a KB file by relative path.",
                       parents=[shared])
    p.add_argument("kb", nargs="?")
    p.add_argument("path")
    p.add_argument("--max-chars", type=int)

    # search
    p = sub.add_parser("search", help="Lexical search across KBs.",
                       parents=[shared])
    p.add_argument("kb", nargs="?")
    p.add_argument("query")
    p.add_argument("--max-results", type=int)
    p.add_argument("--glob")
    p.add_argument("--include-inbox", action="store_true", default=True)
    p.add_argument("--exclude-inbox", action="store_true", default=False)

    # stage
    p = sub.add_parser(
        "stage",
        help="Stage a note (--note), document (--file), or URL pointer (--url).",
        parents=[shared],
    )
    p.add_argument("kb", nargs="?")
    p.add_argument("--note", help="Note body, or description when paired with --url.")
    p.add_argument("--file", help="Path to a text file; staged verbatim.")
    p.add_argument("--url", help="URL pointer; kb-dream fetches/summarises later.")
    p.add_argument(
        "--kind", default=None,
        help=(
            "Free-form kind label written to frontmatter. Suggested values: "
            + ", ".join(SUGGESTED_STAGE_KINDS)
            + ". Any string is accepted. Forced to 'url' with --url."
        ),
    )
    p.add_argument("--title")
    p.add_argument("--source")
    p.add_argument("--no-commit", action="store_true")
    p.add_argument("--force", action="store_true")

    # reindex
    p = sub.add_parser(
        "reindex",
        help="Rebuild the generated index.json manifest.",
        parents=[shared],
    )
    p.add_argument("kb", nargs="?")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would change without writing.")
    p.add_argument("--no-commit", action="store_true")

    # forget
    p = sub.add_parser(
        "forget",
        help="Remove a single page from an indexable section.",
        parents=[shared],
    )
    p.add_argument("kb", nargs="?")
    p.add_argument("path")
    p.add_argument("--reason", help="Short reason recorded in LOG.md.")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would happen without removing anything.")
    p.add_argument("--no-commit", action="store_true")

    # sync
    p = sub.add_parser("sync", help="Synchronize KB git repos.",
                       parents=[shared])
    p.add_argument("kb", nargs="?")
    p.add_argument("--all", action="store_true")

    return parser


def main():
    # Pre-parse --config and --json from anywhere in argv so they work
    # both before and after the subcommand name.
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config", dest="config_path", default=None)
    pre.add_argument("--json", action="store_true", default=False)
    pre_args, remaining = pre.parse_known_args()

    parser = build_parser()
    args = parser.parse_args(remaining)

    # Merge pre-parsed values (top-level position) with subparser values
    if args.config_path is None:
        args.config_path = pre_args.config_path
    if not args.json:
        args.json = pre_args.json

    if not args.command:
        parser.print_help()
        return EXIT_ARGS

    config_path = resolve_config_path(args.config_path)
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ARGS

    dispatch = {
        "bootstrap": cmd_bootstrap,
        "add": cmd_add,
        "remove": cmd_remove,
        "list": cmd_list,
        "status": cmd_status,
        "pending": cmd_pending,
        "remember": cmd_remember,
        "recall": cmd_recall,
        "brief": cmd_brief,
        "open": cmd_open,
        "search": cmd_search,
        "stage": cmd_stage,
        "reindex": cmd_reindex,
        "forget": cmd_forget,
        "sync": cmd_sync,
    }

    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return EXIT_ARGS

    try:
        return handler(args, config, config_path)
    except OSError as exc:
        print(f"Error: filesystem operation failed: {exc}", file=sys.stderr)
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main() or 0)
