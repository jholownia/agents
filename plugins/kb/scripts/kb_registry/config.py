"""Registry configuration: load, save, resolve, and KB entry CRUD."""

import json
import os
from pathlib import Path

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/kb-registry/registry.json")
DEFAULT_KB_ROOT = os.path.expanduser("~/knowledge")
DEFAULT_METRICS_PATH = os.path.expanduser(
    "~/.local/state/kb-registry/events.jsonl"
)

EMPTY_CONFIG = {
    "version": 1,
    "default_kb_root": DEFAULT_KB_ROOT,
    "metrics_path": DEFAULT_METRICS_PATH,
    "kbs": [],
}


def _iter_settings_files():
    """Yield Claude Code settings.json paths in precedence order (highest first).

    Mirrors Claude Code's scope precedence for a CLI launched from inside a
    project tree:
      1. <project>/.claude/settings.local.json   (personal project overrides)
      2. <project>/.claude/settings.json          (shared project)
      3. ~/.claude/settings.json                  (user scope)
    where <project> is the nearest ancestor of the cwd that has a .claude/
    directory (without crossing into $HOME). Enterprise and command-line
    scopes are not reachable from here.
    """
    try:
        cur = Path.cwd().resolve()
    except OSError:
        cur = None
    home = Path(os.path.expanduser("~")).resolve()
    if cur is not None:
        for d in (cur, *cur.parents):
            if d == home:
                break  # ~/.claude is user scope, yielded separately below
            claude_dir = d / ".claude"
            if claude_dir.is_dir():
                yield claude_dir / "settings.local.json"
                yield claude_dir / "settings.json"
                break  # nearest project .claude/ wins
    yield home / ".claude" / "settings.json"


def _plugin_option_from_settings(option):
    """Return pluginConfigs.kb.options.<option> from the settings cascade, or None.

    Claude Code exports configured plugin options as CLAUDE_PLUGIN_OPTION_*
    only into plugin-managed subprocesses (hooks, MCP/LSP servers, monitors) —
    NOT into the generic Bash-tool subprocess the kb skills use to invoke this
    CLI. So the env var never arrives, and we read the same settings.json
    cascade Claude Code would have merged. First non-empty value wins;
    unreadable or malformed files are skipped (resolving a default must never
    hard-fail the CLI).
    """
    for path in _iter_settings_files():
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        plugin_configs = data.get("pluginConfigs")
        if not isinstance(plugin_configs, dict):
            continue
        # Accept the bare plugin id and the id@marketplace form.
        for key in ("kb", "kb@agents"):
            block = plugin_configs.get(key)
            if isinstance(block, dict):
                options = block.get("options")
                if isinstance(options, dict):
                    value = options.get(option)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
    return None


def resolve_config_path(explicit=None):
    """Resolve config path.

    Order (highest precedence first):
      1. explicit --config flag
      2. $KB_REGISTRY_CONFIG
      3. $CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH (exported by Claude Code
         into plugin-managed subprocesses)
      4. pluginConfigs.kb.options.registry_config_path read directly from the
         settings cascade (fallback for Bash-tool invocations, where the env
         var above is not exported)
      5. ~/.config/kb-registry/registry.json
    """
    if explicit:
        return explicit
    env = os.environ.get("KB_REGISTRY_CONFIG")
    if env:
        return env
    plugin_env = os.environ.get("CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH")
    if plugin_env:
        return plugin_env
    settings_value = _plugin_option_from_settings("registry_config_path")
    if settings_value:
        return os.path.expanduser(settings_value)
    return DEFAULT_CONFIG_PATH


def resolve_default_kb_name():
    """Return the configured default KB name, or None.

    Order (highest precedence first):
      1. $CLAUDE_PLUGIN_OPTION_DEFAULT_KB (exported by Claude Code into
         plugin-managed subprocesses)
      2. pluginConfigs.kb.options.default_kb read directly from the settings
         cascade (fallback for Bash-tool invocations, where the env var is not
         exported — which is how the kb skills shell out to this CLI)

    Set per-repo via pluginConfigs.kb.options.default_kb in a project-scope
    .claude/settings.json, or globally in ~/.claude/settings.json.
    """
    name = os.environ.get("CLAUDE_PLUGIN_OPTION_DEFAULT_KB", "").strip()
    if name:
        return name
    return _plugin_option_from_settings("default_kb")


def ensure_parent(path):
    """Create parent directories for path if they don't exist."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)


class ConfigError(Exception):
    """Raised when the config file is unreadable or malformed."""


def load_config(path):
    """Load config from JSON file. Returns empty config if file missing.

    Raises ConfigError with a friendly message on malformed JSON or I/O errors.
    """
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        return dict(EMPTY_CONFIG, **{"kbs": []})
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"Config file {path} is not valid JSON: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})"
        ) from exc
    except OSError as exc:
        raise ConfigError(f"Cannot read config file {path}: {exc}") from exc


def save_config(config, path):
    """Save config to JSON file, creating parent dirs."""
    path = os.path.expanduser(path)
    ensure_parent(path)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def find_kb(config, name):
    """Find a KB entry by name. Returns dict or None."""
    for kb in config.get("kbs", []):
        if kb["name"] == name:
            return kb
    return None


def get_default_kb(config):
    """Return the default KB entry, or None."""
    for kb in config.get("kbs", []):
        if kb.get("default"):
            return kb
    return None


def add_kb(config, entry):
    """Add a KB entry to config. Does not check for duplicates.

    If the new entry is marked default, clear the default flag on every
    other entry so the single-default invariant holds.
    """
    kbs = config.setdefault("kbs", [])
    if entry.get("default"):
        for existing in kbs:
            existing["default"] = False
    kbs.append(entry)


def remove_kb(config, name):
    """Remove a KB entry by name. Returns the removed entry or None."""
    kbs = config.get("kbs", [])
    for i, kb in enumerate(kbs):
        if kb["name"] == name:
            return kbs.pop(i)
    return None


def make_kb_entry(name, path, remote=None, description=None, default=False):
    """Create a KB entry dict."""
    entry = {"name": name, "path": os.path.abspath(path)}
    entry["remote"] = remote
    entry["description"] = description or ""
    entry["default"] = default
    return entry
