"""Git operations: thin subprocess wrappers for KB git management."""

import subprocess


def _run(args, cwd=None):
    """Run a git command, return (success, stdout, returncode)."""
    try:
        r = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=60
        )
        return (r.returncode == 0, r.stdout.strip(), r.returncode)
    except FileNotFoundError:
        return (False, "git not found", 127)
    except subprocess.TimeoutExpired:
        return (False, "git command timed out", 124)


def git_init(cwd):
    return _run(["git", "init"], cwd=cwd)


def git_clone(url, dest):
    return _run(["git", "clone", url, dest])


def git_add_all(cwd):
    return _run(["git", "add", "-A"], cwd=cwd)


def git_add_files(cwd, paths):
    """Stage specific files only."""
    return _run(["git", "add", "--"] + list(paths), cwd=cwd)


def git_add_remote(cwd, name, url):
    return _run(["git", "remote", "add", name, url], cwd=cwd)


def git_commit(cwd, message):
    return _run(["git", "commit", "-m", message], cwd=cwd)


def git_commit_files(cwd, message, paths):
    """Commit specific files only, leaving other staged entries alone."""
    return _run(["git", "commit", "-m", message, "--"] + list(paths), cwd=cwd)


def git_is_repo(path):
    ok, _, _ = _run(["git", "rev-parse", "--git-dir"], cwd=path)
    return ok


def git_is_dirty(cwd):
    """True if working tree has uncommitted changes."""
    ok, out, _ = _run(["git", "status", "--porcelain"], cwd=cwd)
    return bool(out)


def git_current_branch(cwd):
    ok, out, _ = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    return out if ok else None


def git_has_remote(cwd):
    ok, out, _ = _run(["git", "remote"], cwd=cwd)
    return ok and bool(out)


def git_remote_url(cwd, name="origin"):
    ok, out, _ = _run(["git", "remote", "get-url", name], cwd=cwd)
    return out if ok else None


def git_pull_rebase(cwd):
    return _run(["git", "pull", "--rebase"], cwd=cwd)


def git_push(cwd):
    return _run(["git", "push"], cwd=cwd)


def git_log_oneline(cwd, n=5):
    ok, out, _ = _run(
        ["git", "log", "--oneline", "-n", str(n)], cwd=cwd
    )
    return out if ok else ""


def git_has_commits(cwd):
    ok, _, _ = _run(["git", "rev-parse", "HEAD"], cwd=cwd)
    return ok
