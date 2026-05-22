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
from .search import search_kb

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

STAGE_KINDS = [
    "decision", "domain-fact", "codebase-fact",
    "runbook-note", "retrospective", "raw-note",
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
    """Resolve KB by name or default. Returns (kb_entry, error_msg)."""
    if name:
        kb = find_kb(config, name)
        if not kb:
            return None, f"KB '{name}' not found in registry."
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
        description="KB Registry — manage agent-maintained knowledge bases.",
    )
    parser.add_argument("--version", action="version",
                        version=f"kb-registry {__version__}")
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

    # brief
    p = sub.add_parser("brief", help="Print compact KB summary.",
                       parents=[shared])
    p.add_argument("kb")
    p.add_argument("--max-chars", type=int)

    # open
    p = sub.add_parser("open", help="Open a KB file by relative path.",
                       parents=[shared])
    p.add_argument("kb")
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
    p.add_argument("kb")
    p.add_argument("--note", help="Note body, or description when paired with --url.")
    p.add_argument("--file", help="Path to a text file; staged verbatim.")
    p.add_argument("--url", help="URL pointer; kb-dream fetches/summarises later.")
    p.add_argument("--kind", choices=STAGE_KINDS, default=None,
                   help="Note kind (notes only). Forced to 'url' with --url.")
    p.add_argument("--title")
    p.add_argument("--source")
    p.add_argument("--no-commit", action="store_true")
    p.add_argument("--force", action="store_true")

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
        "brief": cmd_brief,
        "open": cmd_open,
        "search": cmd_search,
        "stage": cmd_stage,
        "sync": cmd_sync,
    }

    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return EXIT_ARGS

    return handler(args, config, config_path)


if __name__ == "__main__":
    sys.exit(main() or 0)
