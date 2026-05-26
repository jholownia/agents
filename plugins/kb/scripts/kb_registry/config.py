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


def resolve_config_path(explicit=None):
    """Resolve config path.

    Order (highest precedence first):
      1. explicit --config flag
      2. $KB_REGISTRY_CONFIG
      3. $CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH (set by Claude Code from
         the project- or user-scope pluginConfigs.kb.options block)
      4. ~/.config/kb-registry/registry.json
    """
    if explicit:
        return explicit
    env = os.environ.get("KB_REGISTRY_CONFIG")
    if env:
        return env
    plugin_env = os.environ.get("CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH")
    if plugin_env:
        return plugin_env
    return DEFAULT_CONFIG_PATH


def resolve_default_kb_name():
    """Return the plugin-config-supplied default KB name, or None.

    Set per-repo via pluginConfigs.kb.options.default_kb in
    .claude/settings.json; Claude Code exports it as
    CLAUDE_PLUGIN_OPTION_DEFAULT_KB.
    """
    name = os.environ.get("CLAUDE_PLUGIN_OPTION_DEFAULT_KB", "").strip()
    return name or None


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
