"""Distill ledger storage: append-only typed-finding store under
`.kb-internal/distill/`.

Pure storage and schema primitives. CLI verbs (record/surface/prune) live in
`cli.py` and dispatch into the helpers exported here. Boundaries:

- Identity: hash is `sha256(type + ":" + source)` per D-3/D-10. Statement,
  context, and subkey are human-readable body, not part of the hash.
- Append-only: `append_finding` and `append_tombstone` only ever extend; the
  module exposes no update or in-place mutation API (I-1).
- Reads tolerate corruption: malformed ndjson lines are skipped silently here
  (the surface verb is responsible for any user-facing warning, per design.md
  "Failure modes").
- Plugin-managed namespace: callers always go through `distill_dir` so the
  `.kb-internal/distill/` location stays a single source of truth (I-5, D-4).
"""

import hashlib
import json
import os
import re

# Per D-9: locked v0 vocabulary. Adding new types is a minor version bump;
# removing/renaming is breaking. Ordering here is informational only.
CONVERGENT_TYPES = ("failure-mode", "resolution-path", "heuristic")
DIVERGENT_TYPES = ("open-question", "contradiction", "incomplete")
VALID_TYPES = CONVERGENT_TYPES + DIVERGENT_TYPES

VALID_TRACKS = ("convergent", "divergent")

VALID_SUGGESTED_ACTIONS = (
    "promote-to-claude-md",
    "promote-to-skill",
    "harness-update",
    "needs-clarification",
    "needs-resolution",
    "needs-investigation",
)

REQUIRED_FIELDS = (
    "track",
    "type",
    "source",
    "statement",
    "suggested_action",
    "detected_at",
    "hash",
    "recurrence_after_retention",
)

OPTIONAL_FIELDS = ("subkey", "context")

ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

# ISO 8601 check — `YYYY-MM-DDTHH:MM:SS` with optional fractional seconds
# and a REQUIRED timezone suffix (`Z` or `±HH:MM`). Naive timestamps are
# rejected at the record boundary because `cmd_distill_prune` and
# `cmd_distill_surface`'s `--since` filter compare aware UTC values; allowing
# naive entries through here would surface as a TypeError later. kb-dream
# emits UTC via `date -u +%Y-%m-%dT%H:%M:%SZ`, so this is no constraint on
# real producers — it just hardens the boundary.
_ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})$"
)

# PIPE_BUF guarantee on macOS/Linux for atomic single-write line appends
# (design.md "Failure modes → Two kb-dream passes race").
_MAX_RECORD_BYTES = 4096

# Subdirectory under the KB root that holds plugin-managed maintenance state.
# Reserved namespace — `reindex`, `search`, and kb-dream all skip it (I-5).
_DISTILL_SUBDIR = os.path.join(".kb-internal", "distill")
_FINDINGS_FILE = "findings.ndjson"
_TOMBSTONE_FILE = "pruned-hashes.ndjson"


def slugify(text):
    """Normalise heading text to a GitHub-style anchor slug.

    Deterministic: same input always produces the same output. Lowercases,
    collapses runs of whitespace into a single dash, strips punctuation other
    than dashes and word characters. Used to build the `source` anchor part
    so `(type, source)` hashing is stable across heading-text edits that
    keep the same canonical name.
    """
    if text is None:
        return ""
    s = text.strip().lower()
    # Replace runs of whitespace with a single dash.
    s = re.sub(r"\s+", "-", s)
    # Drop any character that's not a word char or dash.
    s = re.sub(r"[^\w-]", "", s)
    # Collapse runs of dashes that may have resulted from punctuation removal.
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def compute_hash(type_, source):
    """Compute the deterministic finding identity hash.

    Returns the hex digest of `sha256(type + ":" + source)` per D-3/D-10.
    `subkey` is intentionally excluded — agent-generated subkeys would
    reintroduce LLM non-determinism at the identity layer.
    """
    payload = (type_ + ":" + source).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _implied_track(type_):
    """Return the track structurally implied by `type_`, or None if unknown.

    Encodes I-6: failure-mode/resolution-path/heuristic ⇒ convergent;
    open-question/contradiction/incomplete ⇒ divergent.
    """
    if type_ in CONVERGENT_TYPES:
        return "convergent"
    if type_ in DIVERGENT_TYPES:
        return "divergent"
    return None


def validate_finding(record):
    """Validate a finding record against the v0 schema.

    Returns `(True, None)` on success, `(False, "<reason>")` on failure.
    Enforces I-6 (track implied by type), I-7 (unknown type or inconsistent
    track/type pair rejected at the boundary), D-9 vocabulary, presence of
    required fields, no unknown top-level fields, ISO 8601 `detected_at`,
    non-empty `source`, and a known `suggested_action`.
    """
    if not isinstance(record, dict):
        return False, "record must be a JSON object"

    # Reject unknown top-level fields up front so typos surface immediately.
    extras = [k for k in record.keys() if k not in ALL_FIELDS]
    if extras:
        return False, "unknown field(s): " + ", ".join(sorted(extras))

    for field in REQUIRED_FIELDS:
        if field not in record:
            return False, "missing required field: " + field

    type_ = record["type"]
    if type_ not in VALID_TYPES:
        return False, (
            "unknown type: " + repr(type_) + " (expected one of "
            + ", ".join(VALID_TYPES) + ")"
        )

    track = record["track"]
    if track not in VALID_TRACKS:
        return False, (
            "unknown track: " + repr(track) + " (expected one of "
            + ", ".join(VALID_TRACKS) + ")"
        )

    implied = _implied_track(type_)
    if implied is not None and track != implied:
        return False, (
            "track/type mismatch: type " + repr(type_)
            + " implies track " + repr(implied) + ", got " + repr(track)
        )

    source = record["source"]
    if not isinstance(source, str) or not source.strip():
        return False, "source must be a non-empty string"

    action = record["suggested_action"]
    if action not in VALID_SUGGESTED_ACTIONS:
        return False, (
            "unknown suggested_action: " + repr(action)
            + " (expected one of " + ", ".join(VALID_SUGGESTED_ACTIONS) + ")"
        )

    detected_at = record["detected_at"]
    if not isinstance(detected_at, str) or not _ISO8601_RE.match(detected_at):
        return False, (
            "detected_at must be an ISO 8601 timestamp, got "
            + repr(detected_at)
        )

    if not isinstance(record["recurrence_after_retention"], bool):
        return False, "recurrence_after_retention must be a bool"

    if not isinstance(record["statement"], str) or not record["statement"]:
        return False, "statement must be a non-empty string"

    if not isinstance(record["hash"], str) or not record["hash"]:
        return False, "hash must be a non-empty string"

    return True, None


def distill_dir(kb_path):
    """Return the `.kb-internal/distill/` directory path for a KB."""
    return os.path.join(kb_path, _DISTILL_SUBDIR)


def findings_path(kb_path):
    """Return the absolute path to `findings.ndjson` for a KB."""
    return os.path.join(distill_dir(kb_path), _FINDINGS_FILE)


def tombstone_path(kb_path):
    """Return the absolute path to `pruned-hashes.ndjson` for a KB."""
    return os.path.join(distill_dir(kb_path), _TOMBSTONE_FILE)


# Marker line used by the legacy (0.7.0) gitignore self-install. Recognising
# our own marker lets the 0.7.1 self-uninstall be safe — we only remove a file
# we wrote, never a user-authored .gitignore.
_LEGACY_GITIGNORE_MARKER = "# Plugin-managed maintenance state — see kb plugin."


def ensure_distill_dir(kb_path):
    """Create the `.kb-internal/distill/` directory if missing.

    The ledger is durable consolidation output, not local maintenance state —
    it must travel with the KB repo so downstream consumers (WARDEN, other
    clones) see the findings. So nothing is gitignored. If a legacy 0.7.0
    `.kb-internal/.gitignore` exists with our marker line, remove it as a
    one-shot migration; a user-authored gitignore (without the marker) is
    left alone.
    """
    os.makedirs(distill_dir(kb_path), exist_ok=True)
    gitignore_path = os.path.join(kb_path, ".kb-internal", ".gitignore")
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                head = f.readline().rstrip("\n")
        except OSError:
            return
        if head == _LEGACY_GITIGNORE_MARKER:
            try:
                os.remove(gitignore_path)
            except OSError:
                pass


def _serialise_record(record):
    """Return the canonical ndjson serialisation for a record.

    Single-line, no whitespace between separators, UTF-8 preserving. Caller
    is responsible for appending the trailing newline.
    """
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def append_finding(kb_path, record):
    """Append one finding to `findings.ndjson` as a single atomic line write.

    Creates the distill directory if missing. Raises `ValueError` if the
    serialised line would exceed the PIPE_BUF guarantee (4 KB on macOS/Linux);
    this preserves line atomicity under concurrent kb-dream passes (design.md
    "Failure modes → Two kb-dream passes race"). The record is written as-is;
    callers are expected to validate and hash before invoking.
    """
    ensure_distill_dir(kb_path)
    line = _serialise_record(record) + "\n"
    encoded = line.encode("utf-8")
    if len(encoded) > _MAX_RECORD_BYTES:
        raise ValueError("record exceeds 4 KB PIPE_BUF guarantee")
    with open(findings_path(kb_path), "a", encoding="utf-8") as f:
        f.write(line)


def iter_findings(kb_path):
    """Yield parseable finding records from `findings.ndjson`.

    Malformed lines (invalid JSON, non-object payloads) are skipped silently.
    Missing file yields nothing. Caller is responsible for any user-visible
    warning about skipped lines.
    """
    path = findings_path(kb_path)
    if not os.path.isfile(path):
        return
    try:
        f = open(path, "r", encoding="utf-8")
    except OSError:
        return
    with f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                yield obj


def read_live_hashes(kb_path):
    """Return the set of hashes currently in the live ledger.

    Skips malformed lines silently; entries missing a `hash` field are
    skipped too. Missing file returns the empty set.
    """
    hashes = set()
    for record in iter_findings(kb_path):
        h = record.get("hash")
        if isinstance(h, str) and h:
            hashes.add(h)
    return hashes


def read_tombstone_hashes(kb_path):
    """Return the set of pruned-hash tombstone entries.

    Tombstone is hash-per-line ndjson (just the hash string, not a JSON
    object — kept minimal per D-6). Missing file returns the empty set.
    Malformed lines are skipped silently.
    """
    hashes = set()
    path = tombstone_path(kb_path)
    if not os.path.isfile(path):
        return hashes
    try:
        f = open(path, "r", encoding="utf-8")
    except OSError:
        return hashes
    with f:
        for raw in f:
            h = raw.strip()
            if h:
                hashes.add(h)
    return hashes


def append_tombstone(kb_path, hash_):
    """Append one hash to `pruned-hashes.ndjson`.

    Creates the distill directory if missing. The tombstone stores raw hex
    digests one per line — never JSON — so growth stays bounded (D-6).
    """
    ensure_distill_dir(kb_path)
    if not isinstance(hash_, str) or not hash_:
        raise ValueError("hash must be a non-empty string")
    if "\n" in hash_:
        raise ValueError("hash must not contain newlines")
    with open(tombstone_path(kb_path), "a", encoding="utf-8") as f:
        f.write(hash_ + "\n")
