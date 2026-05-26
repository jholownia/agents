"""JSONL metrics: append-only event logging for all CLI commands."""

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone


def _now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()


def emit_event(metrics_path, event):
    """Append a single JSON event to the metrics file. Fails silently."""
    try:
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        with open(metrics_path, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")
    except Exception:
        pass  # metrics must never break commands


@contextmanager
def track_command(metrics_path, command, kb=None, cwd=None, strict=False,
                  **extra):
    """Context manager that emits a JSONL event on exit.

    Usage:
        with track_command(path, "search", kb="emma") as ctx:
            ctx["result_count"] = 4
    """
    ctx = {
        "timestamp": _now_iso(),
        "command": command,
        "kb": kb,
        "cwd": cwd or os.getcwd(),
        "agent": "claude-code",
        "success": True,
        "duration_ms": 0,
        "error": None,
        "safety_rejected": False,
    }
    ctx.update(extra)
    start = time.monotonic()
    try:
        yield ctx
    except Exception as exc:
        ctx["success"] = False
        ctx["error"] = str(exc)
        raise
    finally:
        ctx["duration_ms"] = int((time.monotonic() - start) * 1000)
        try:
            emit_event(metrics_path, ctx)
        except Exception:
            if strict:
                raise
