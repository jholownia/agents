#!/usr/bin/env bash
# Lightweight repeatable validation for the kb plugin.
# Run from the agents repo root:  bash plugins/kb/scripts/test_kb_registry.sh
#
# Uses a temporary config and a temporary KB by default.
# Set KB_REGISTRY_TEST_KB=../test-kb to validate against a chosen path.
# Existing test KB paths are not deleted unless KB_REGISTRY_TEST_RESET=1.

set -euo pipefail

KB="python3 plugins/kb/bin/kb"
TMPDIR=$(mktemp -d)
CONFIG="$TMPDIR/registry.json"
METRICS="$TMPDIR/events.jsonl"
TEST_KB="${KB_REGISTRY_TEST_KB:-$TMPDIR/test-kb}"
PASS=0
FAIL=0

cleanup() {
    rm -rf "$TMPDIR"
}
trap cleanup EXIT

run() {
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then
        PASS=$((PASS+1))
        echo "  PASS  $desc"
    else
        FAIL=$((FAIL+1))
        echo "  FAIL  $desc"
    fi
}

run_fail() {
    local expected_exit="$1"; local desc="$2"; shift 2
    local rc=0
    "$@" >/dev/null 2>&1 || rc=$?
    if [ "$rc" -eq "$expected_exit" ]; then
        PASS=$((PASS+1))
        echo "  PASS  $desc (exit $rc)"
    else
        FAIL=$((FAIL+1))
        echo "  FAIL  $desc (expected exit $expected_exit, got $rc)"
    fi
}

echo "=== KB Registry Validation ==="
echo ""

# --- Setup: prepare test KB path safely ---
if [ -e "$TEST_KB" ]; then
    if [ "${KB_REGISTRY_TEST_RESET:-0}" = "1" ]; then
        rm -rf "$TEST_KB"
    else
        echo "Test KB path already exists: $TEST_KB"
        echo "Set KB_REGISTRY_TEST_RESET=1 to delete/recreate it, or set KB_REGISTRY_TEST_KB to a different path."
        exit 2
    fi
fi

# Prepare config pointing metrics to temp
cat > "$CONFIG" <<JSON
{
  "version": 1,
  "default_kb_root": "$TMPDIR/knowledge",
  "metrics_path": "$METRICS",
  "kbs": []
}
JSON

echo "--- 1. Help ---"
run "kb --help" $KB --config "$CONFIG" --help
run "kb bootstrap --help" $KB --config "$CONFIG" bootstrap --help

echo ""
echo "--- 2. Bootstrap ---"
run "bootstrap test" $KB --config "$CONFIG" bootstrap test --path "$TEST_KB"
run "test-kb exists" test -d "$TEST_KB"
run "BRIEF.md exists" test -f "$TEST_KB/BRIEF.md"
run "AGENTS.md exists" test -f "$TEST_KB/AGENTS.md"
run "LOG.md exists" test -f "$TEST_KB/LOG.md"
run "inbox/ exists" test -d "$TEST_KB/inbox"
run "knowledge/ exists" test -d "$TEST_KB/knowledge"
run "notes/ exists" test -d "$TEST_KB/notes"
run "notes/README.md exists" test -f "$TEST_KB/notes/README.md"
run "git repo init" git -C "$TEST_KB" rev-parse --git-dir

echo ""
echo "--- 3. List + Status ---"
run "list" $KB --config "$CONFIG" list
run "list --json" $KB --config "$CONFIG" list --json
run "status test" $KB --config "$CONFIG" status test

# Empty registry: status prints the bootstrap/add hint promised by
# commands/status.md.
EMPTY_CONFIG="$TMPDIR/empty-registry.json"
cat > "$EMPTY_CONFIG" <<JSON
{"version": 1, "metrics_path": "$METRICS", "kbs": []}
JSON
EMPTY_STATUS=$($KB --config "$EMPTY_CONFIG" status 2>&1)
if echo "$EMPTY_STATUS" | grep -q "No KBs registered"; then
    PASS=$((PASS+1))
    echo "  PASS  status on empty registry prints hint"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  status on empty registry printed: $EMPTY_STATUS"
fi

echo ""
echo "--- 4. Brief ---"
run "brief test" $KB --config "$CONFIG" brief test
run "brief --json" $KB --config "$CONFIG" brief test --json
run "brief --max-chars" $KB --config "$CONFIG" brief test --max-chars 100

echo ""
echo "--- 5. Stage ---"
run "stage decision" $KB --config "$CONFIG" stage test --kind decision --note "Test decision note."
run "stage raw-note" $KB --config "$CONFIG" stage test --kind raw-note --note "Test raw note."

# Non-UTF8 text files must stage without a traceback (bytes are replaced).
printf 'latin1 probe: caf\xe9\n' > "$TMPDIR/latin1.txt"
run "stage non-UTF8 file" $KB --config "$CONFIG" stage test --file "$TMPDIR/latin1.txt"

# Verify only staged files are committed (not unrelated changes)
echo "untracked" > "$TEST_KB/untracked.txt"
run "stage with untracked present" $KB --config "$CONFIG" stage test --note "Another note."
# untracked.txt should NOT be committed
# git log exits 0 with empty output if file was never committed — check output
UNTRACKED_LOG=$(git -C "$TEST_KB" log --oneline -- untracked.txt 2>&1)
if [ -z "$UNTRACKED_LOG" ]; then
    PASS=$((PASS+1))
    echo "  PASS  untracked file not committed"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  untracked file was committed: $UNTRACKED_LOG"
fi
rm -f "$TEST_KB/untracked.txt"

# Verify already-staged unrelated files are not swept into the inbox commit.
echo "pre-staged" > "$TEST_KB/pre_staged.txt"
git -C "$TEST_KB" add pre_staged.txt
run "stage with pre-staged unrelated file" $KB --config "$CONFIG" stage test --note "Note with pre-staged unrelated file."
PRESTAGED_LOG=$(git -C "$TEST_KB" log --oneline -- pre_staged.txt 2>&1)
if [ -z "$PRESTAGED_LOG" ]; then
    PASS=$((PASS+1))
    echo "  PASS  pre-staged unrelated file not committed"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  pre-staged unrelated file was committed: $PRESTAGED_LOG"
fi
git -C "$TEST_KB" reset -- pre_staged.txt >/dev/null 2>&1 || true
rm -f "$TEST_KB/pre_staged.txt"

echo ""
echo "--- 5a. Stage --dir (bulk) ---"
DIR_SRC="$TMPDIR/source-tree"
mkdir -p "$DIR_SRC/sub/nested" "$DIR_SRC/node_modules/pkg" "$DIR_SRC/.git"
cat > "$DIR_SRC/intro.md" <<'MD'
# Intro
Top-level markdown source.
MD
cat > "$DIR_SRC/notes.txt" <<'TXT'
Plain text notes.
TXT
cat > "$DIR_SRC/sub/nested/deep.md" <<'MD'
# Deep
Recursively-found source.
MD
# Sources we should NOT pick up:
echo '{"junk":true}' > "$DIR_SRC/config.json"          # wrong extension
python3 -c "open('$DIR_SRC/blob.md', 'wb').write(b'\x00binary\x00')"  # null bytes
: > "$DIR_SRC/empty.md"                                 # empty (0 bytes)
echo "scm" > "$DIR_SRC/.git/HEAD"                       # hidden dir
echo "x" > "$DIR_SRC/node_modules/pkg/index.md"         # bloat dir
echo "# hidden" > "$DIR_SRC/.hidden.md"                 # hidden file
# Bulk stage and assert exactly the 3 expected files landed.
OUT=$($KB --config "$CONFIG" stage test --dir "$DIR_SRC" --json 2>&1)
STAGED_COUNT=$(echo "$OUT" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
print(len(d['staged']))
" 2>/dev/null)
if [ "$STAGED_COUNT" = "3" ]; then
    PASS=$((PASS+1))
    echo "  PASS  stage --dir staged exactly 3 text files"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  expected 3 staged, got $STAGED_COUNT (out: $OUT)"
fi
# Skip categories surface in JSON.
if echo "$OUT" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
skipped = d.get('skipped', {})
assert 'binary' in skipped, skipped
assert 'extension' in skipped, skipped
assert 'empty' in skipped, skipped
"; then
    PASS=$((PASS+1))
    echo "  PASS  stage --dir reports skip categories"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  stage --dir skip categories missing"
fi
# All staged files committed in a single bulk commit.
BULK_SUBJECT=$(git -C "$TEST_KB" log -1 --pretty=%s)
if echo "$BULK_SUBJECT" | grep -qE "kb: stage directory .* \(3 files\)"; then
    PASS=$((PASS+1))
    echo "  PASS  --dir commit subject reports count"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  unexpected commit subject: $BULK_SUBJECT"
fi
# Files copied verbatim (no frontmatter prepended).
NEW_DOC=$(find "$TEST_KB/inbox" -name '*-intro.md' | head -1)
if [ -n "$NEW_DOC" ] && head -1 "$NEW_DOC" | grep -q '^# Intro$'; then
    PASS=$((PASS+1))
    echo "  PASS  --dir copies content verbatim (no frontmatter)"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  --dir content not verbatim (file=$NEW_DOC)"
fi
# Mutex: --dir + --note must error.
run_fail 2 "--dir + --note rejected" $KB --config "$CONFIG" stage test --dir "$DIR_SRC" --note "x"
# Missing dir.
run_fail 2 "--dir nonexistent path rejected" $KB --config "$CONFIG" stage test --dir "$TMPDIR/does-not-exist"

echo ""
echo "--- 5b. Stage extraction (markitdown) ---"
# Only run extraction tests when markitdown is available; otherwise verify the
# graceful fallback paths.
HAS_MARKITDOWN=0
if command -v markitdown >/dev/null 2>&1; then HAS_MARKITDOWN=1; fi

if [ "$HAS_MARKITDOWN" = "1" ]; then
    # --file with .html → extracted markdown + provenance frontmatter, no source kept.
    EXTRACT_SRC="$TMPDIR/source.html"
    cat > "$EXTRACT_SRC" <<'HTML'
<html><body><h1>Sample</h1><p>Body of the document.</p></body></html>
HTML
    OUT=$($KB --config "$CONFIG" stage test --file "$EXTRACT_SRC" --json 2>&1)
    if echo "$OUT" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
assert d.get('mode') == 'extracted', d
assert d.get('extractor') == 'markitdown', d
assert d.get('extracted_from'), d
assert 'source' not in d, ('default should not keep source', d)
"; then
        PASS=$((PASS+1))
        echo "  PASS  --file extractable converts via markitdown"
    else
        FAIL=$((FAIL+1))
        echo "  FAIL  --file extractable mode wrong (out: $OUT)"
    fi

    EXTRACTED=$(echo "$OUT" | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['path'])")
    if head -10 "$TEST_KB/$EXTRACTED" | grep -q '^kind: "extracted"$' \
       && head -10 "$TEST_KB/$EXTRACTED" | grep -q 'extracted_from:' \
       && grep -q '# Sample' "$TEST_KB/$EXTRACTED"; then
        PASS=$((PASS+1))
        echo "  PASS  extracted file carries provenance frontmatter + content"
    else
        FAIL=$((FAIL+1))
        echo "  FAIL  extracted frontmatter/content malformed (file=$EXTRACTED)"
    fi

    # Default does NOT copy source to sources/.
    if [ ! -d "$TEST_KB/sources/2026" ] || ! find "$TEST_KB/sources" -name "*.html" 2>/dev/null | grep -q .; then
        PASS=$((PASS+1))
        echo "  PASS  default extraction does not copy source binary"
    else
        FAIL=$((FAIL+1))
        echo "  FAIL  source unexpectedly copied to sources/"
    fi

    # --keep-source copies original to sources/ and adds source: frontmatter.
    KEEP_SRC="$TMPDIR/keep-me.html"
    cat > "$KEEP_SRC" <<'HTML'
<html><body><h1>Keep</h1><p>this one</p></body></html>
HTML
    OUT=$($KB --config "$CONFIG" stage test --file "$KEEP_SRC" --keep-source --json 2>&1)
    if echo "$OUT" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
assert d.get('source', '').startswith('sources/'), d
" && find "$TEST_KB/sources" -name "keep-me.html" 2>/dev/null | grep -q .; then
        PASS=$((PASS+1))
        echo "  PASS  --keep-source copies original to sources/"
    else
        FAIL=$((FAIL+1))
        echo "  FAIL  --keep-source did not copy source (out: $OUT)"
    fi

    # --dir picks up an extractable file and counts it under 'extracted'.
    EXTRACT_DIR="$TMPDIR/extract-tree"
    mkdir -p "$EXTRACT_DIR"
    cat > "$EXTRACT_DIR/note.md" <<'MD'
# Plain
plain note
MD
    cat > "$EXTRACT_DIR/doc.html" <<'HTML'
<html><body><h1>HTML in tree</h1><p>extracted via dir walk</p></body></html>
HTML
    OUT=$($KB --config "$CONFIG" stage test --dir "$EXTRACT_DIR" --json 2>&1)
    if echo "$OUT" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
assert len(d.get('staged', [])) == 2, d
assert len(d.get('extracted', [])) == 1, d
assert d.get('sources_kept', []) == [], d
"; then
        PASS=$((PASS+1))
        echo "  PASS  --dir extracts .html, leaves .md verbatim"
    else
        FAIL=$((FAIL+1))
        echo "  FAIL  --dir extract counts wrong (out: $OUT)"
    fi

    # --dir + --keep-source copies sources alongside extractions.
    OUT=$($KB --config "$CONFIG" stage test --dir "$EXTRACT_DIR" --keep-source --json 2>&1)
    if echo "$OUT" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
assert len(d.get('sources_kept', [])) == 1, d
"; then
        PASS=$((PASS+1))
        echo "  PASS  --dir --keep-source copies the html source"
    else
        FAIL=$((FAIL+1))
        echo "  FAIL  --dir --keep-source did not copy source (out: $OUT)"
    fi

    # Duplicate source basenames from different directories must not collide
    # under sources/YYYY/MM/.
    DUP_DIR="$TMPDIR/extract-duplicates"
    mkdir -p "$DUP_DIR/a" "$DUP_DIR/b"
    cat > "$DUP_DIR/a/duplicate.html" <<'HTML'
<html><body><h1>Duplicate A</h1></body></html>
HTML
    cat > "$DUP_DIR/b/duplicate.html" <<'HTML'
<html><body><h1>Duplicate B</h1></body></html>
HTML
    OUT=$($KB --config "$CONFIG" stage test --dir "$DUP_DIR" --keep-source --json 2>&1)
    if echo "$OUT" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
kept = d.get('sources_kept', [])
assert len(kept) == 2, d
assert len(set(kept)) == 2, d
"; then
        PASS=$((PASS+1))
        echo "  PASS  --dir --keep-source avoids duplicate source names"
    else
        FAIL=$((FAIL+1))
        echo "  FAIL  duplicate source names collided (out: $OUT)"
    fi
else
    echo "  SKIP  markitdown not installed; extraction tests not run on this host"
fi

echo ""
echo "--- 6. Safety ---"
# v0 no longer scans content for secrets — credentials-discussing docs must stage cleanly.
run "credential-discussing doc stages cleanly" $KB --config "$CONFIG" stage test --note "examples include password=hunter2 and AKIA1234567890ABCDEF"

# Notes own their headings — the CLI must not prepend one.
$KB --config "$CONFIG" stage test --note "# Body Heading" --title "Heading Test" >/dev/null 2>&1
HEADING_NOTE=$(grep -rl "Body Heading" "$TEST_KB/inbox" | head -1)
HEADING_COUNT=$(grep -c "^# " "$HEADING_NOTE" 2>/dev/null || echo 0)
if [ "$HEADING_COUNT" -eq 1 ]; then
    PASS=$((PASS+1))
    echo "  PASS  stage does not double the heading"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  expected one H1 in staged note, found $HEADING_COUNT"
fi

# Frontmatter must survive embedded double-quote in title.
run "stage note with quoted title" $KB --config "$CONFIG" stage test --note "body" --title 'He said "hi"'
LATEST_NOTE=$(find "$TEST_KB/inbox" -name '*he-said-hi*.md' | head -1)
if [ -n "$LATEST_NOTE" ] && grep -q 'title: "He said \\"hi\\""' "$LATEST_NOTE"; then
    PASS=$((PASS+1))
    echo "  PASS  quoted title escaped in frontmatter"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  quoted title not escaped (file=$LATEST_NOTE)"
fi

# --source must appear in frontmatter.
run "stage with --source" $KB --config "$CONFIG" stage test --note "src-test note" --source "conversation-123"
SRC_NOTE=$(grep -rl "src-test note" "$TEST_KB/inbox" | head -1)
if [ -n "$SRC_NOTE" ] && grep -q 'source: "conversation-123"' "$SRC_NOTE"; then
    PASS=$((PASS+1))
    echo "  PASS  --source threaded into frontmatter"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  --source not in frontmatter (file=$SRC_NOTE)"
fi

# Documents (--file) are copied verbatim, no frontmatter, no auto-heading.
DOC_SRC="$TMPDIR/doc-sample.md"
cat > "$DOC_SRC" <<'DOC'
# Sample Document

This document was staged via --file. It must land verbatim.

Second paragraph with a `code span` and other content.
DOC
run "stage --file (document)" $KB --config "$CONFIG" stage test --file "$DOC_SRC"
DOC_NOTE=$(find "$TEST_KB/inbox" -name '*doc-sample*.md' | head -1)
if [ -n "$DOC_NOTE" ] && ! head -1 "$DOC_NOTE" | grep -q '^---$'; then
    PASS=$((PASS+1))
    echo "  PASS  document has no frontmatter"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  document has frontmatter (file=$DOC_NOTE)"
fi
if [ -n "$DOC_NOTE" ] && diff -q "$DOC_SRC" "$DOC_NOTE" >/dev/null 2>&1; then
    PASS=$((PASS+1))
    echo "  PASS  document content verbatim"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  document content differs from source"
fi
# Commit message should mention the source filename.
LAST_COMMIT=$(git -C "$TEST_KB" log -1 --pretty=%s)
if echo "$LAST_COMMIT" | grep -q "stage document doc-sample.md"; then
    PASS=$((PASS+1))
    echo "  PASS  commit message records source filename"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  commit message missing source filename: $LAST_COMMIT"
fi
# --note + --file together should error.
run_fail 2 "--note and --file mutually exclusive" $KB --config "$CONFIG" stage test --note "x" --file "$DOC_SRC"

# --url stages a URL pointer with kind:url and url: in frontmatter, empty body.
run "stage --url" $KB --config "$CONFIG" stage test --url "https://example.com/articles/why-agents-forget"
URL_NOTE=$(find "$TEST_KB/inbox" -name '*why-agents-forget*' | head -1)
if [ -n "$URL_NOTE" ] && grep -q '^kind: "url"$' "$URL_NOTE" && grep -q '^url: "https://example.com/articles/why-agents-forget"$' "$URL_NOTE"; then
    PASS=$((PASS+1))
    echo "  PASS  --url writes kind:url + url frontmatter"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  --url frontmatter wrong (file=$URL_NOTE)"
fi

# --url + --note: description becomes body.
run "stage --url + --note" $KB --config "$CONFIG" stage test --url "https://blog.example.com/memory" --note "Saved because it argues forgetting is the fix."
URL_DESC=$(grep -rl "forgetting is the fix" "$TEST_KB/inbox" | head -1)
if [ -n "$URL_DESC" ] && grep -q '^url: "https://blog.example.com/memory"$' "$URL_DESC"; then
    PASS=$((PASS+1))
    echo "  PASS  --url description body landed alongside url frontmatter"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  --url + --note combination broken (file=$URL_DESC)"
fi

# Invalid URL rejected.
run_fail 2 "reject non-http URL" $KB --config "$CONFIG" stage test --url "ftp://example.com/x"

# --url + --file mutually exclusive.
run_fail 2 "--url and --file mutex" $KB --config "$CONFIG" stage test --url "https://example.com/" --file "$DOC_SRC"

echo ""
echo "--- 7. Search ---"
run "search test" $KB --config "$CONFIG" search test "decision"
run "search --json" $KB --config "$CONFIG" search test "decision" --json
run "search all KBs" $KB --config "$CONFIG" search "note"

# Query is literal in both backends: regex metacharacters must match
# verbatim (rg runs with --fixed-strings, fallback uses re.escape).
$KB --config "$CONFIG" stage test --note "search-meta probe foo(bar) end" >/dev/null 2>&1
META_OUT=$($KB --config "$CONFIG" search test "foo(bar)" 2>&1)
if echo "$META_OUT" | grep -q "search-meta"; then
    PASS=$((PASS+1))
    echo "  PASS  search treats regex metacharacters literally"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  search missed literal 'foo(bar)': $META_OUT"
fi

# Dash-prefixed queries must not be parsed as rg flags.
$KB --config "$CONFIG" stage test --note "dash probe -dash-token end" >/dev/null 2>&1
DASH_OUT=$($KB --config "$CONFIG" search test -- "-dash-token" 2>&1)
if echo "$DASH_OUT" | grep -q "dash probe"; then
    PASS=$((PASS+1))
    echo "  PASS  search handles dash-prefixed query"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  search missed dash-prefixed query: $DASH_OUT"
fi

# Smart-case: lowercase queries match capitalised text (rg's default would
# diverge from the Python fallback's re.IGNORECASE here). Surfaced during
# kb 0.7.0 dogfooding when searching for "defensive validation" missed the
# canonical page titled "Defensive validation patterns".
$KB --config "$CONFIG" stage test --note "MixedCase Probe entry here" >/dev/null 2>&1
SMART_LOWER=$($KB --config "$CONFIG" search test "mixedcase probe" 2>&1)
if echo "$SMART_LOWER" | grep -q "MixedCase Probe"; then
    PASS=$((PASS+1))
    echo "  PASS  search lowercase query hits capitalised text (smart-case)"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  search missed capitalised text on lowercase query: $SMART_LOWER"
fi
# All-uppercase query stays case-sensitive (smart-case half).
SMART_UPPER=$($KB --config "$CONFIG" search test "MIXEDCASE PROBE" 2>&1)
if echo "$SMART_UPPER" | grep -q "No results"; then
    PASS=$((PASS+1))
    echo "  PASS  search uppercase query stays case-sensitive (smart-case)"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  smart-case broken — uppercase query matched anyway: $SMART_UPPER"
fi

echo ""
echo "--- 6b. Remember + Recall ---"
run "remember emma fact" $KB --config "$CONFIG" remember "EMMA's nightly job runs at 02:00 UTC via cron." --tags emma,runbook
run "remember codebase fact" $KB --config "$CONFIG" remember "analyze_meter_drift returns null when input has <30 days." --tags codebase,emma
REM_NOTE=$(find "$TEST_KB/notes" -name '*nightly-job*.md' | head -1)
if [ -n "$REM_NOTE" ] && grep -q '^created_at:' "$REM_NOTE" && grep -q '^tags: \[' "$REM_NOTE"; then
    PASS=$((PASS+1))
    echo "  PASS  remember note has created_at + tags frontmatter"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  remember frontmatter wrong (file=$REM_NOTE)"
fi
# Body must be verbatim — no auto-heading prepended.
if [ -n "$REM_NOTE" ] && ! grep -q "^# " "$REM_NOTE"; then
    PASS=$((PASS+1))
    echo "  PASS  remember note has no auto-heading"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  remember note has auto-heading or is missing"
fi

# recall --tag should find both emma-tagged notes.
TAG_OUT=$($KB --config "$CONFIG" recall test --tag emma 2>&1)
EMMA_HITS=$(echo "$TAG_OUT" | grep -c "notes/")
if [ "$EMMA_HITS" -ge 2 ]; then
    PASS=$((PASS+1))
    echo "  PASS  recall --tag emma finds both notes ($EMMA_HITS)"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  recall --tag emma found $EMMA_HITS (expected >=2)"
fi

# recall --query should find the note by substring.
QUERY_OUT=$($KB --config "$CONFIG" recall test --query "nightly" 2>&1)
if echo "$QUERY_OUT" | grep -q "nightly-job"; then
    PASS=$((PASS+1))
    echo "  PASS  recall --query finds note by substring"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  recall --query nightly missed: $QUERY_OUT"
fi

# recall must NOT include inbox content.
$KB --config "$CONFIG" stage test --note "inbox-only-marker-string" >/dev/null 2>&1
INBOX_OUT=$($KB --config "$CONFIG" recall test --query "inbox-only-marker-string" 2>&1)
if echo "$INBOX_OUT" | grep -q "No results"; then
    PASS=$((PASS+1))
    echo "  PASS  recall excludes inbox/"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  recall returned inbox content: $INBOX_OUT"
fi

# recall requires --query or --tag.
run_fail 2 "recall requires --query or --tag" $KB --config "$CONFIG" recall test
# ... and rejects both together (--tag used to be silently ignored).
run_fail 2 "recall rejects --query + --tag" $KB --config "$CONFIG" recall test --query nightly --tag emma

# Two remembers with identical text must yield two files, even within the
# same second (filenames are second-granular; collisions get numbered).
$KB --config "$CONFIG" remember "collision probe identical text" >/dev/null 2>&1
$KB --config "$CONFIG" remember "collision probe identical text" >/dev/null 2>&1
COLLISION_COUNT=$(find "$TEST_KB/notes" -name '*collision-probe*' | wc -l | tr -d ' ')
if [ "$COLLISION_COUNT" -eq 2 ]; then
    PASS=$((PASS+1))
    echo "  PASS  same-text remember x2 keeps both notes"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  same-text remember x2 left $COLLISION_COUNT notes (expected 2)"
fi

# Same invariant for stage.
$KB --config "$CONFIG" stage test --note "stage collision probe" >/dev/null 2>&1
$KB --config "$CONFIG" stage test --note "stage collision probe" >/dev/null 2>&1
STAGE_COLLISIONS=$(find "$TEST_KB/inbox" -name '*stage-collision-probe*' | wc -l | tr -d ' ')
if [ "$STAGE_COLLISIONS" -eq 2 ]; then
    PASS=$((PASS+1))
    echo "  PASS  same-text stage x2 keeps both notes"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  same-text stage x2 left $STAGE_COLLISIONS notes (expected 2)"
fi

echo ""
echo "--- 7b. Pending ---"
# pending should list inbox items but skip inbox/processed/.
mkdir -p "$TEST_KB/inbox/processed/2026/05"
cat > "$TEST_KB/inbox/processed/2026/05/already-processed.md" <<'PROCESSED'
---
kind: "decision"
title: "Already processed"
---

# Already processed

Body.
PROCESSED
git -C "$TEST_KB" add inbox/processed/ >/dev/null 2>&1
git -C "$TEST_KB" commit -m "test: pre-existing processed note" >/dev/null 2>&1

PENDING_OUT=$($KB --config "$CONFIG" pending test 2>&1)
if echo "$PENDING_OUT" | grep -q "Test decision note"; then
    PASS=$((PASS+1))
    echo "  PASS  pending lists inbox notes"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  pending missed inbox notes: $PENDING_OUT"
fi
if echo "$PENDING_OUT" | grep -q "Already processed"; then
    FAIL=$((FAIL+1))
    echo "  FAIL  pending included inbox/processed/"
else
    PASS=$((PASS+1))
    echo "  PASS  pending skips inbox/processed/"
fi

PENDING_JSON=$($KB --config "$CONFIG" pending test --json 2>&1)
if echo "$PENDING_JSON" | python3 -c "import json,sys; data=json.load(sys.stdin); assert isinstance(data, list) and len(data) > 0" 2>/dev/null; then
    PASS=$((PASS+1))
    echo "  PASS  pending --json is a non-empty array"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  pending --json shape wrong"
fi

# followup kind must be accepted.
run "stage --kind followup" $KB --config "$CONFIG" stage test --kind followup --note "Remember to gather more sources on X."

echo ""
echo "--- 8. Open + path traversal ---"
run "open BRIEF.md" $KB --config "$CONFIG" open test BRIEF.md
run "open --json" $KB --config "$CONFIG" open test BRIEF.md --json
run_fail 3 "reject path traversal" $KB --config "$CONFIG" open test ../../../etc/passwd
run_fail 2 "reject absolute path" $KB --config "$CONFIG" open test /etc/passwd

echo ""
echo "--- 9. Add validation ---"
# Create a directory missing contract files
INVALID_KB="$TMPDIR/invalid-kb"
mkdir -p "$INVALID_KB"
run_fail 2 "add rejects invalid contract" $KB --config "$CONFIG" add invalid --path "$INVALID_KB"
run "add --force with invalid contract" $KB --config "$CONFIG" add invalid --path "$INVALID_KB" --force
# Clean up invalid entry
$KB --config "$CONFIG" remove invalid >/dev/null 2>&1 || true

echo ""
echo "--- 10. Remove / Add round-trip ---"
run "remove test" $KB --config "$CONFIG" remove test
run "list empty" $KB --config "$CONFIG" list
run "add test back" $KB --config "$CONFIG" add test --path "$TEST_KB" --force
run "list after add" $KB --config "$CONFIG" list

echo ""
echo "--- 11. Sync ---"
run "sync local-only" $KB --config "$CONFIG" sync test

echo ""
echo "--- 11b. Malformed config rejected ---"
BAD_CONFIG="$TMPDIR/bad.json"
echo "{ not json" > "$BAD_CONFIG"
run_fail 2 "malformed config exits 2" $KB --config "$BAD_CONFIG" list

echo ""
echo "--- 11c. Single-default invariant ---"
DEFAULT_CONFIG="$TMPDIR/default.json"
cat > "$DEFAULT_CONFIG" <<JSON
{"version": 1, "default_kb_root": "$TMPDIR", "metrics_path": "$METRICS", "kbs": []}
JSON
KB_ONE="$TMPDIR/kb-one"
KB_TWO="$TMPDIR/kb-two"
$KB --config "$DEFAULT_CONFIG" bootstrap one --path "$KB_ONE" --default >/dev/null 2>&1
$KB --config "$DEFAULT_CONFIG" bootstrap two --path "$KB_TWO" --default >/dev/null 2>&1
DEFAULT_COUNT=$(python3 -c "
import json
d = json.load(open('$DEFAULT_CONFIG'))
print(sum(1 for k in d['kbs'] if k.get('default')))
")
if [ "$DEFAULT_COUNT" -eq 1 ]; then
    PASS=$((PASS+1))
    echo "  PASS  exactly one default after second --default bootstrap"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  expected 1 default, got $DEFAULT_COUNT"
fi

echo ""
echo "--- 11d. CLAUDE_PLUGIN_OPTION_* env var bridge ---"
# Set up two KBs in a fresh config so we can test which one wins.
BRIDGE_CONFIG="$TMPDIR/bridge.json"
cat > "$BRIDGE_CONFIG" <<JSON
{"version": 1, "default_kb_root": "$TMPDIR/bridge", "metrics_path": "$METRICS", "kbs": []}
JSON
mkdir -p "$TMPDIR/bridge"
$KB --config "$BRIDGE_CONFIG" bootstrap alpha --path "$TMPDIR/bridge/alpha-kb" >/dev/null 2>&1
$KB --config "$BRIDGE_CONFIG" bootstrap beta --path "$TMPDIR/bridge/beta-kb" >/dev/null 2>&1
# alpha was first so it carries default:true; bare `kb brief` returns alpha.
DEFAULT_OUT=$($KB --config "$BRIDGE_CONFIG" brief 2>&1 | head -1)
if echo "$DEFAULT_OUT" | grep -q "alpha"; then
    PASS=$((PASS+1))
    echo "  PASS  registry default resolves bare brief to alpha"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  expected alpha, got: $DEFAULT_OUT"
fi
# CLAUDE_PLUGIN_OPTION_DEFAULT_KB overrides the registry default.
ENV_OUT=$(CLAUDE_PLUGIN_OPTION_DEFAULT_KB=beta $KB --config "$BRIDGE_CONFIG" brief 2>&1 | head -1)
if echo "$ENV_OUT" | grep -q "beta"; then
    PASS=$((PASS+1))
    echo "  PASS  CLAUDE_PLUGIN_OPTION_DEFAULT_KB overrides registry default"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  expected beta via env, got: $ENV_OUT"
fi
# Explicit positional wins over env.
FLAG_OUT=$(CLAUDE_PLUGIN_OPTION_DEFAULT_KB=beta $KB --config "$BRIDGE_CONFIG" brief alpha 2>&1 | head -1)
if echo "$FLAG_OUT" | grep -q "alpha"; then
    PASS=$((PASS+1))
    echo "  PASS  explicit positional KB wins over env var"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  expected alpha via flag, got: $FLAG_OUT"
fi
# Env pointing at nonexistent KB errors clearly.
run_fail 2 "env var pointing at unknown KB exits 2" \
    env CLAUDE_PLUGIN_OPTION_DEFAULT_KB=ghost $KB --config "$BRIDGE_CONFIG" brief

# CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH redirects the config file.
EMPTY_CONFIG="$TMPDIR/empty-bridge.json"
cat > "$EMPTY_CONFIG" <<JSON
{"version": 1, "default_kb_root": "$TMPDIR", "metrics_path": "$METRICS", "kbs": []}
JSON
PATH_OUT=$(CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH="$EMPTY_CONFIG" $KB list 2>&1)
if echo "$PATH_OUT" | grep -q "No KBs registered"; then
    PASS=$((PASS+1))
    echo "  PASS  CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH honoured"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  expected empty list via env path, got: $PATH_OUT"
fi
# --config wins over CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH.
PRECEDENCE_OUT=$(CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH="$EMPTY_CONFIG" $KB --config "$BRIDGE_CONFIG" list 2>&1)
if echo "$PRECEDENCE_OUT" | grep -q "alpha"; then
    PASS=$((PASS+1))
    echo "  PASS  --config wins over CLAUDE_PLUGIN_OPTION_REGISTRY_CONFIG_PATH"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  expected --config precedence, got: $PRECEDENCE_OUT"
fi

echo ""
echo "--- 12. --config works from top-level ---"
# Verify top-level --config is honored and not ignored
ALT_CONFIG="$TMPDIR/alt-config.json"
cat > "$ALT_CONFIG" <<JSON
{"version": 1, "default_kb_root": "$TMPDIR", "metrics_path": "$METRICS", "kbs": []}
JSON
# List with alt config should show empty (no KBs in alt config)
OUTPUT=$($KB --config "$ALT_CONFIG" list 2>&1)
if echo "$OUTPUT" | grep -q "No KBs"; then
    PASS=$((PASS+1))
    echo "  PASS  --config before subcommand"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  --config before subcommand (got: $OUTPUT)"
fi
# Also test config after subcommand
OUTPUT=$($KB list --config "$ALT_CONFIG" 2>&1)
if echo "$OUTPUT" | grep -q "No KBs"; then
    PASS=$((PASS+1))
    echo "  PASS  --config after subcommand"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  --config after subcommand (got: $OUTPUT)"
fi

echo ""
echo "--- 12b. Reindex (index.json) ---"
# Fresh KB has no indexable content pages and the seed READMEs are excluded,
# so the first reindex writes an empty array.
run "reindex creates index.json" $KB --config "$CONFIG" reindex test --no-commit
run "index.json exists" test -f "$TEST_KB/index.json"
run "INDEX.md untouched (no markers)" bash -c "! grep -q 'kb:reindex' '$TEST_KB/INDEX.md'"
# Add knowledge + notes pages and rebuild; assert structure.
mkdir -p "$TEST_KB/knowledge"
cat > "$TEST_KB/knowledge/widgets.md" <<'MD'
---
tags: [widgets, manufacturing]
last_reviewed: 2026-05-26
---
# Widgets

Widgets are small mechanical assemblies used in EMMA telemetry rigs. They
ship from the Cardiff plant on Tuesdays.
MD
$KB --config "$CONFIG" remember "Demo fact about widgets and meters." --kb test --tags widgets,demo --no-commit >/dev/null 2>&1
$KB --config "$CONFIG" reindex test --no-commit >/dev/null 2>&1
# Verify index.json shape.
if python3 -c "
import json, sys
data = json.load(open('$TEST_KB/index.json'))
assert isinstance(data, list), data
paths = [e['path'] for e in data]
assert 'knowledge/widgets.md' in paths, paths
assert any(p.startswith('notes/') and p.endswith('.md') for p in paths), paths
widgets = next(e for e in data if e['path'] == 'knowledge/widgets.md')
assert widgets['title'] == 'Widgets', widgets
assert widgets['section'] == 'knowledge', widgets
assert 'widgets' in widgets['tags'], widgets
assert widgets['word_count'] > 0, widgets
assert widgets['summary'].startswith('Widgets are small'), widgets
" 2>/dev/null; then
    PASS=$((PASS+1))
    echo "  PASS  index.json has correct structure"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  index.json structure mismatch"
fi
# Idempotent: second run reports no change.
OUT=$($KB --config "$CONFIG" reindex test --no-commit --json 2>&1)
if echo "$OUT" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
assert d.get('changed') is False, d
"; then
    PASS=$((PASS+1))
    echo "  PASS  reindex idempotent on second run"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  reindex not idempotent (got: $OUT)"
fi
# Dry-run reports counts without writing.
rm -f "$TEST_KB/index.json"
OUT=$($KB --config "$CONFIG" reindex test --dry-run --json 2>&1)
if echo "$OUT" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
assert d.get('dry_run') is True, d
assert d.get('entries', 0) >= 2, d
assert d.get('changed') is True, d
" && [ ! -f "$TEST_KB/index.json" ]; then
    PASS=$((PASS+1))
    echo "  PASS  dry-run does not write index.json"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  dry-run wrote or misreported (got: $OUT)"
fi
# Rebuild for downstream tests.
$KB --config "$CONFIG" reindex test --no-commit >/dev/null 2>&1
# Recall consults index.json: query matching title should mark source=index.
OUT=$($KB --config "$CONFIG" recall test --query Widgets --json 2>&1)
if echo "$OUT" | python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
assert any(r.get('source') == 'index' and r.get('path') == 'knowledge/widgets.md'
           for r in data), data
"; then
    PASS=$((PASS+1))
    echo "  PASS  recall query ranks index hits"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  recall did not surface index match (got: $OUT)"
fi
# Tag recall uses index.json (no rg required).
OUT=$($KB --config "$CONFIG" recall test --tag widgets --json 2>&1)
if echo "$OUT" | python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
assert any(r.get('source') == 'index' for r in data), data
assert any('widgets' in (r.get('tags') or []) for r in data), data
"; then
    PASS=$((PASS+1))
    echo "  PASS  recall --tag uses index.json"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  recall --tag did not consult index.json (got: $OUT)"
fi
# Missing index.json: recall still works (body grep) and prints a tip.
rm -f "$TEST_KB/index.json"
TIP_OUT=$($KB --config "$CONFIG" recall test --query Widgets 2>&1)
if echo "$TIP_OUT" | grep -q "reindex"; then
    PASS=$((PASS+1))
    echo "  PASS  recall hints at reindex when index.json missing"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  no reindex hint emitted (got: $TIP_OUT)"
fi
# Tidy.
rm -f "$TEST_KB/knowledge/widgets.md"
$KB --config "$CONFIG" reindex test --no-commit >/dev/null 2>&1 || true

echo ""
echo "--- 12c. Agent-owned flexibility ---"
# Stage accepts an invented kind label that isn't in the suggestion list.
run "stage accepts arbitrary --kind" $KB --config "$CONFIG" stage test --note "Open question about meter calibration." --kind hypothesis
# Verify the frontmatter carries the agent-chosen kind verbatim.
LATEST=$(ls -t "$TEST_KB"/inbox/*/*/*.md 2>/dev/null | head -1)
if [ -n "$LATEST" ] && head -10 "$LATEST" | grep -q "^kind: \"hypothesis\""; then
    PASS=$((PASS+1))
    echo "  PASS  arbitrary --kind written to frontmatter verbatim"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  arbitrary --kind not written (file: $LATEST)"
fi
# Reindex auto-discovers a brand-new top-level section the agent invents.
mkdir -p "$TEST_KB/runbooks"
cat > "$TEST_KB/runbooks/incident-playbook.md" <<'MD'
# Incident playbook

Step-by-step response for production incidents.
MD
$KB --config "$CONFIG" reindex test --no-commit >/dev/null 2>&1
if python3 -c "
import json
data = json.load(open('$TEST_KB/index.json'))
assert any(e['section'] == 'runbooks' and e['path'] == 'runbooks/incident-playbook.md' for e in data), data
" 2>/dev/null; then
    PASS=$((PASS+1))
    echo "  PASS  reindex auto-discovers new top-level section"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  reindex did not pick up runbooks/ section"
fi
# Recall searches the same auto-discovered sections, not just notes/knowledge.
rm -f "$TEST_KB/index.json"
OUT=$($KB --config "$CONFIG" recall test --query incidents --json 2>&1)
if echo "$OUT" | python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
assert any(r.get('source') == 'body' and r.get('path') == 'runbooks/incident-playbook.md'
           for r in data), data
"; then
    PASS=$((PASS+1))
    echo "  PASS  recall body search covers discovered sections"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  recall missed discovered section body hit (got: $OUT)"
fi
$KB --config "$CONFIG" reindex test --no-commit >/dev/null 2>&1
# Forget works on the auto-discovered section too.
run "forget operates on discovered section" $KB --config "$CONFIG" forget test runbooks/incident-playbook.md --reason "test cleanup" --no-commit
run "forget removed page in discovered section" bash -c "! test -f '$TEST_KB/runbooks/incident-playbook.md'"
# Forget still refuses inbox/.
run_fail 2 "forget still refuses inbox/" $KB --config "$CONFIG" forget test inbox/whatever.md
# Tidy: the agent might still want runbooks/ empty.
rmdir "$TEST_KB/runbooks" 2>/dev/null || true

echo ""
echo "--- 12d. Forget ---"
# Seed a forgettable knowledge page + a notes file via remember.
cat > "$TEST_KB/knowledge/scratch.md" <<'MD'
# Scratch

Throwaway content for forget tests.
MD
NOTE_PATH=$($KB --config "$CONFIG" remember "Temporary fact about scratch." --kb test --tags scratch --no-commit --json 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)['path'])")
git -C "$TEST_KB" add -A >/dev/null 2>&1
git -C "$TEST_KB" commit -m "test: seed forget fixtures" >/dev/null 2>&1 || true
# Refuse paths outside indexable sections.
run_fail 2 "forget refuses inbox/" $KB --config "$CONFIG" forget test inbox/something.md
run_fail 3 "forget refuses BRIEF.md via traversal" $KB --config "$CONFIG" forget test knowledge/../BRIEF.md
run_fail 3 "forget refuses path traversal" $KB --config "$CONFIG" forget test ../etc/passwd
run_fail 1 "forget refuses nonexistent file" $KB --config "$CONFIG" forget test knowledge/does-not-exist.md
# Dry-run reports plan, leaves file alone.
OUT=$($KB --config "$CONFIG" forget test knowledge/scratch.md --dry-run --reason "duplicate of widgets" --json 2>&1)
if echo "$OUT" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
assert d.get('dry_run') is True, d
assert d.get('path') == 'knowledge/scratch.md', d
assert 'duplicate of widgets' in d.get('log_line', ''), d
" && test -f "$TEST_KB/knowledge/scratch.md"; then
    PASS=$((PASS+1))
    echo "  PASS  forget --dry-run reports plan without removing"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  forget dry-run touched file or misreported (got: $OUT)"
fi
# Apply: deletes file, appends LOG.md, commits.
run "forget removes knowledge page" $KB --config "$CONFIG" forget test knowledge/scratch.md --reason "obsolete"
run "forget actually removed file" bash -c "! test -f '$TEST_KB/knowledge/scratch.md'"
if grep -q "forgot \`knowledge/scratch.md\`" "$TEST_KB/LOG.md"; then
    PASS=$((PASS+1))
    echo "  PASS  LOG.md captured the forget entry"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  LOG.md missing forget entry"
fi
# Commit landed.
if git -C "$TEST_KB" log -1 --format=%s | grep -q "kb: forget knowledge/scratch.md"; then
    PASS=$((PASS+1))
    echo "  PASS  forget commit message is correct"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  forget did not commit (or wrong subject)"
fi
# Git history still has the content (forget = soft for retrieval, hard for surface).
if git -C "$TEST_KB" log --all -- knowledge/scratch.md | grep -q "test: seed forget fixtures"; then
    PASS=$((PASS+1))
    echo "  PASS  git history preserves forgotten content"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  git history lost the forgotten content"
fi
# Forget a notes/ entry too.
if [ -n "$NOTE_PATH" ] && [ -f "$TEST_KB/$NOTE_PATH" ]; then
    run "forget notes/ entry" $KB --config "$CONFIG" forget test "$NOTE_PATH"
    run "notes file removed" bash -c "! test -f '$TEST_KB/$NOTE_PATH'"
fi
# Forget warns when INDEX.md links the path.
cat > "$TEST_KB/knowledge/linked.md" <<'MD'
# Linked Page
Content.
MD
python3 - "$TEST_KB/INDEX.md" <<'PY'
import sys
p = sys.argv[1]
with open(p) as f: t = f.read()
with open(p, "w") as f: f.write(t + "\n- [Linked](knowledge/linked.md)\n")
PY
git -C "$TEST_KB" add -A >/dev/null 2>&1
git -C "$TEST_KB" commit -m "test: add linked fixture" >/dev/null 2>&1 || true
WARN_OUT=$($KB --config "$CONFIG" forget test knowledge/linked.md 2>&1)
if echo "$WARN_OUT" | grep -q "INDEX.md still references"; then
    PASS=$((PASS+1))
    echo "  PASS  forget warns about INDEX.md reference"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  no INDEX.md-reference warning (got: $WARN_OUT)"
fi
# No tidy: the temp KB is wiped by the EXIT trap. Skipped to avoid
# destructive git ops if someone overrides KB_REGISTRY_TEST_KB.

echo ""
echo "--- 13. Metrics ---"
EVENTS=$(wc -l < "$METRICS" 2>/dev/null || echo 0)
if [ "$EVENTS" -gt 0 ]; then
    PASS=$((PASS+1))
    echo "  PASS  metrics has $EVENTS events"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  metrics file empty or missing"
fi
# Check that failed commands have success=false
FAILURES=$(python3 -c "
import json, sys
with open('$METRICS') as f:
    events = [json.loads(l) for l in f]
failed = [e for e in events if e.get('success') == False]
print(len(failed))
" 2>/dev/null || echo 0)
if [ "$FAILURES" -gt 0 ]; then
    PASS=$((PASS+1))
    echo "  PASS  $FAILURES failed events have success=false"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  no failed events with success=false"
fi

echo ""
echo "--- 14. Plugin structure ---"
run "plugin.json exists" test -f plugins/kb/.claude-plugin/plugin.json
run "bin/kb exists" test -x plugins/kb/bin/kb
run "registry SKILL.md exists" test -f plugins/kb/skills/registry/SKILL.md
run "info SKILL.md exists" test -f plugins/kb/skills/info/SKILL.md
run "remember SKILL.md exists" test -f plugins/kb/skills/remember/SKILL.md
run "stage SKILL.md exists" test -f plugins/kb/skills/stage/SKILL.md
run "recall SKILL.md exists" test -f plugins/kb/skills/recall/SKILL.md
run "retrospective SKILL.md exists" test -f plugins/kb/skills/retrospective/SKILL.md
run "kb-dream agent exists" test -f plugins/kb/agents/kb-dream.md
run "bootstrap command exists" test -f plugins/kb/commands/bootstrap.md
run "add command exists" test -f plugins/kb/commands/add.md
run "status command exists" test -f plugins/kb/commands/status.md
run "sync command exists" test -f plugins/kb/commands/sync.md
run "shared references/ exists" test -d plugins/kb/references
# Every command file carries description + allowed-tools frontmatter.
for cmd in bootstrap add status sync; do
    CMD="plugins/kb/commands/$cmd.md"
    if head -10 "$CMD" | grep -q "^description:" \
       && head -10 "$CMD" | grep -q "^allowed-tools:"; then
        PASS=$((PASS+1))
        echo "  PASS  $cmd command frontmatter"
    else
        FAIL=$((FAIL+1))
        echo "  FAIL  $cmd command frontmatter (description/allowed-tools)"
    fi
done
run "plugin.json valid JSON" python3 -c "import json; json.load(open('plugins/kb/.claude-plugin/plugin.json'))"
run "marketplace registered as kb" python3 -c "
import json
d = json.load(open('.claude-plugin/marketplace.json'))
assert any(p['name'] == 'kb' for p in d['plugins'])
"
# Each skill SKILL.md must have third-person frontmatter (Anthropic template).
for skill in registry info remember stage recall retrospective; do
    SKILL="plugins/kb/skills/$skill/SKILL.md"
    if head -10 "$SKILL" | grep -q "^name: $skill$" \
       && head -10 "$SKILL" | grep -q "^description: This skill should be used when" \
       && head -10 "$SKILL" | grep -q "^version:"; then
        PASS=$((PASS+1))
        echo "  PASS  $skill SKILL.md frontmatter (name, description template, version)"
    else
        FAIL=$((FAIL+1))
        echo "  FAIL  $skill SKILL.md frontmatter (expects name/description-template/version)"
    fi
done
# Version lockstep: plugin.json == marketplace.json entry == __version__.
# An unbumped or drifted version ships stale code from the plugin cache.
run "version lockstep (plugin.json, marketplace.json, __version__)" python3 -c "
import json, sys
sys.path.insert(0, 'plugins/kb/scripts')
from kb_registry import __version__
plugin = json.load(open('plugins/kb/.claude-plugin/plugin.json'))['version']
market = next(p['version']
              for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']
              if p['name'] == 'kb')
assert plugin == market == __version__, (plugin, market, __version__)
"

# kb-dream agent frontmatter check.
AGENT="plugins/kb/agents/kb-dream.md"
if head -5 "$AGENT" | grep -q "^name: kb-dream$" \
   && head -40 "$AGENT" | grep -q "^description:" \
   && head -40 "$AGENT" | grep -q "Use this agent when"; then
    PASS=$((PASS+1))
    echo "  PASS  kb-dream agent frontmatter"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  kb-dream agent frontmatter"
fi

echo ""
echo "--- 15. Distill ---"
# Helper: emit a finding JSON payload on stdout.
# Args: track type source statement suggested_action detected_at [subkey]
distill_payload() {
    local track="$1" type="$2" source="$3" statement="$4" action="$5" detected_at="$6" subkey="${7:-}"
    python3 -c "
import json, sys
rec = {
    'track': sys.argv[1],
    'type': sys.argv[2],
    'source': sys.argv[3],
    'statement': sys.argv[4],
    'suggested_action': sys.argv[5],
    'detected_at': sys.argv[6],
    'recurrence_after_retention': False,
}
if len(sys.argv) > 7 and sys.argv[7]:
    rec['subkey'] = sys.argv[7]
print(json.dumps(rec))
" "$track" "$type" "$source" "$statement" "$action" "$detected_at" "$subkey"
}

# --- T1: record valid finding (all six types, both tracks) ---
# Fresh sub-fixture so dedup/prune semantics aren't perturbed by neighbours.
DISTILL_KB="$TMPDIR/distill-kb"
$KB --config "$CONFIG" bootstrap distill --path "$DISTILL_KB" >/dev/null 2>&1
DISTILL_LEDGER="$DISTILL_KB/.kb-internal/distill/findings.ndjson"

NOW="2026-06-16T12:00:00Z"
# Six records: three convergent + three divergent, one per v0 type.
$KB --config "$CONFIG" distill record distill --data "$(distill_payload convergent failure-mode    'knowledge/a.md#x1' 'fm stmt' promote-to-claude-md "$NOW")" >/dev/null
$KB --config "$CONFIG" distill record distill --data "$(distill_payload convergent resolution-path 'knowledge/a.md#x2' 'rp stmt' promote-to-skill    "$NOW")" >/dev/null
$KB --config "$CONFIG" distill record distill --data "$(distill_payload convergent heuristic       'knowledge/a.md#x3' 'h  stmt' harness-update       "$NOW")" >/dev/null
$KB --config "$CONFIG" distill record distill --data "$(distill_payload divergent  open-question   'knowledge/a.md#x4' 'oq stmt' needs-clarification  "$NOW")" >/dev/null
$KB --config "$CONFIG" distill record distill --data "$(distill_payload divergent  contradiction   'knowledge/a.md#x5' 'co stmt' needs-resolution     "$NOW")" >/dev/null
$KB --config "$CONFIG" distill record distill --data "$(distill_payload divergent  incomplete      'knowledge/a.md#x6' 'in stmt' needs-investigation  "$NOW")" >/dev/null

run "T1 findings.ndjson exists" test -f "$DISTILL_LEDGER"
LINE_COUNT=$(wc -l < "$DISTILL_LEDGER" | tr -d ' ')
if [ "$LINE_COUNT" -eq 6 ]; then
    PASS=$((PASS+1))
    echo "  PASS  T1 ledger has 6 entries (one per v0 type)"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T1 expected 6 entries, got $LINE_COUNT"
fi
# Every line is valid JSON and every record has a non-empty hash + all required fields.
if python3 -c "
import json
required = {'track','type','source','statement','suggested_action','detected_at','hash','recurrence_after_retention'}
types_seen = set()
tracks_seen = set()
with open('$DISTILL_LEDGER') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        assert required.issubset(rec.keys()), rec
        assert isinstance(rec['hash'], str) and rec['hash'], rec
        types_seen.add(rec['type'])
        tracks_seen.add(rec['track'])
assert types_seen == {'failure-mode','resolution-path','heuristic','open-question','contradiction','incomplete'}, types_seen
assert tracks_seen == {'convergent','divergent'}, tracks_seen
" 2>/dev/null; then
    PASS=$((PASS+1))
    echo "  PASS  T1 every entry valid JSON with schema fields + hash, all 6 types + 2 tracks present"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T1 ledger schema/hash/type-coverage check failed"
fi

# --- T2: dedup on (type, source) ---
# Use a fresh KB so we can count cleanly.
DEDUP_KB="$TMPDIR/distill-dedup-kb"
$KB --config "$CONFIG" bootstrap dedup --path "$DEDUP_KB" >/dev/null 2>&1
DEDUP_LEDGER="$DEDUP_KB/.kb-internal/distill/findings.ndjson"

# First record: prose A.
$KB --config "$CONFIG" distill record dedup --data "$(distill_payload convergent failure-mode 'knowledge/b.md#Cache Strategy' 'first prose' promote-to-claude-md "$NOW" subkeyA)" >/dev/null
# Second record: same (type, source) but different statement/context/subkey AND
# different casing on the anchor — must normalise to the same hash and dedup.
DUP_OUT=$($KB --config "$CONFIG" distill record dedup --data "$(distill_payload convergent failure-mode 'knowledge/b.md#cache-strategy' 'second prose drift' promote-to-claude-md "$NOW" subkeyB)" 2>&1)
DUP_RC=$?
if [ "$DUP_RC" -eq 0 ]; then
    PASS=$((PASS+1))
    echo "  PASS  T2 dedup call exits 0 (silent no-op)"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T2 dedup call exited $DUP_RC, expected 0"
fi
if echo "$DUP_OUT" | grep -q "hash already in ledger"; then
    PASS=$((PASS+1))
    echo "  PASS  T2 dedup emits observability message on stderr"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T2 missing 'hash already in ledger' notice (got: $DUP_OUT)"
fi
DEDUP_LINES=$(wc -l < "$DEDUP_LEDGER" | tr -d ' ')
if [ "$DEDUP_LINES" -eq 1 ]; then
    PASS=$((PASS+1))
    echo "  PASS  T2 same (type, source) under prose+casing drift → 1 entry"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T2 expected 1 entry after dedup, got $DEDUP_LINES"
fi

# --- T3: reject unknown type, unknown track, or track/type mismatch ---
# Unknown type.
BAD_TYPE='{"track":"convergent","type":"bogus","source":"knowledge/c.md#x","statement":"x","suggested_action":"promote-to-claude-md","detected_at":"2026-06-16T12:00:00Z","recurrence_after_retention":false}'
BEFORE_LINES=$(wc -l < "$DEDUP_LEDGER" | tr -d ' ')
run_fail 2 "T3 reject unknown type" $KB --config "$CONFIG" distill record dedup --data "$BAD_TYPE"
AFTER_LINES=$(wc -l < "$DEDUP_LEDGER" | tr -d ' ')
if [ "$BEFORE_LINES" = "$AFTER_LINES" ]; then
    PASS=$((PASS+1))
    echo "  PASS  T3 unknown type does not append to ledger"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T3 unknown type appended ($BEFORE_LINES → $AFTER_LINES)"
fi
# Unknown track.
BAD_TRACK='{"track":"weird","type":"failure-mode","source":"knowledge/c.md#y","statement":"x","suggested_action":"promote-to-claude-md","detected_at":"2026-06-16T12:00:00Z","recurrence_after_retention":false}'
run_fail 2 "T3 reject unknown track" $KB --config "$CONFIG" distill record dedup --data "$BAD_TRACK"
# Mismatched pair.
BAD_PAIR='{"track":"convergent","type":"open-question","source":"knowledge/c.md#z","statement":"x","suggested_action":"needs-clarification","detected_at":"2026-06-16T12:00:00Z","recurrence_after_retention":false}'
run_fail 2 "T3 reject track/type mismatch (convergent + open-question)" $KB --config "$CONFIG" distill record dedup --data "$BAD_PAIR"
FINAL_LINES=$(wc -l < "$DEDUP_LEDGER" | tr -d ' ')
if [ "$FINAL_LINES" = "$BEFORE_LINES" ]; then
    PASS=$((PASS+1))
    echo "  PASS  T3 no rejected record reaches the ledger"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T3 ledger grew after rejections ($BEFORE_LINES → $FINAL_LINES)"
fi

# --- T4: surface filters ---
# Reuse the 6-entry $DISTILL_KB from T1 (one per type, three per track).
count_surface() {
    local result
    result=$($KB --config "$CONFIG" distill surface distill --format json "$@" 2>/dev/null)
    if [ -z "$result" ]; then
        echo 0
    else
        echo "$result" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"
    fi
}
T4_TYPE_FM=$(count_surface --type failure-mode)
T4_TYPE_OQ=$(count_surface --type open-question)
T4_TRACK_C=$(count_surface --track convergent)
T4_TRACK_D=$(count_surface --track divergent)
T4_SINCE_FUTURE=$(count_surface --since 2099-01-01T00:00:00Z)
T4_SINCE_PAST=$(count_surface --since 2000-01-01T00:00:00Z)

if [ "$T4_TYPE_FM" -eq 1 ]; then
    PASS=$((PASS+1)); echo "  PASS  T4 --type failure-mode returns 1"
else
    FAIL=$((FAIL+1)); echo "  FAIL  T4 --type failure-mode expected 1, got $T4_TYPE_FM"
fi
if [ "$T4_TYPE_OQ" -eq 1 ]; then
    PASS=$((PASS+1)); echo "  PASS  T4 --type open-question returns 1"
else
    FAIL=$((FAIL+1)); echo "  FAIL  T4 --type open-question expected 1, got $T4_TYPE_OQ"
fi
if [ "$T4_TRACK_C" -eq 3 ]; then
    PASS=$((PASS+1)); echo "  PASS  T4 --track convergent returns 3"
else
    FAIL=$((FAIL+1)); echo "  FAIL  T4 --track convergent expected 3, got $T4_TRACK_C"
fi
if [ "$T4_TRACK_D" -eq 3 ]; then
    PASS=$((PASS+1)); echo "  PASS  T4 --track divergent returns 3"
else
    FAIL=$((FAIL+1)); echo "  FAIL  T4 --track divergent expected 3, got $T4_TRACK_D"
fi
if [ "$T4_SINCE_FUTURE" -eq 0 ]; then
    PASS=$((PASS+1)); echo "  PASS  T4 --since <future> returns 0"
else
    FAIL=$((FAIL+1)); echo "  FAIL  T4 --since <future> expected 0, got $T4_SINCE_FUTURE"
fi
if [ "$T4_SINCE_PAST" -eq 6 ]; then
    PASS=$((PASS+1)); echo "  PASS  T4 --since <past> returns all 6"
else
    FAIL=$((FAIL+1)); echo "  FAIL  T4 --since <past> expected 6, got $T4_SINCE_PAST"
fi

# --- T5: prune removes entries older than TTL ---
PRUNE_KB="$TMPDIR/distill-prune-kb"
$KB --config "$CONFIG" bootstrap prune --path "$PRUNE_KB" >/dev/null 2>&1
PRUNE_LEDGER="$PRUNE_KB/.kb-internal/distill/findings.ndjson"
PRUNE_TOMB="$PRUNE_KB/.kb-internal/distill/pruned-hashes.ndjson"

NOW_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OLD_TS="2024-01-01T00:00:00Z"
# One backdated, one fresh — distinct (type, source) so they get distinct hashes.
$KB --config "$CONFIG" distill record prune --data "$(distill_payload convergent failure-mode 'knowledge/p.md#old' 'old finding' promote-to-claude-md "$OLD_TS")" >/dev/null
$KB --config "$CONFIG" distill record prune --data "$(distill_payload convergent failure-mode 'knowledge/p.md#new' 'new finding' promote-to-claude-md "$NOW_TS")" >/dev/null
# Capture the old hash for T5/T6 cross-checks.
OLD_HASH=$(python3 -c "
import hashlib
print(hashlib.sha256(('failure-mode:knowledge/p.md#old').encode()).hexdigest())
")
$KB --config "$CONFIG" distill prune prune --ttl-days 30 >/dev/null
PRUNE_LINES=$(wc -l < "$PRUNE_LEDGER" | tr -d ' ')
if [ "$PRUNE_LINES" -eq 1 ]; then
    PASS=$((PASS+1))
    echo "  PASS  T5 prune leaves 1 entry (backdated removed)"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T5 expected 1 entry after prune, got $PRUNE_LINES"
fi
if ! grep -q '#old' "$PRUNE_LEDGER"; then
    PASS=$((PASS+1))
    echo "  PASS  T5 backdated entry gone from ledger"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T5 backdated entry still in ledger"
fi
if grep -q '#new' "$PRUNE_LEDGER"; then
    PASS=$((PASS+1))
    echo "  PASS  T5 fresh entry retained"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T5 fresh entry was dropped"
fi
if [ -f "$PRUNE_TOMB" ] && grep -q "$OLD_HASH" "$PRUNE_TOMB"; then
    PASS=$((PASS+1))
    echo "  PASS  T5 pruned hash appears in pruned-hashes.ndjson"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T5 pruned hash missing from tombstone"
fi

# --- T6: recurrence_after_retention on re-record after tombstone ---
# Re-record the previously-pruned (type, source) with a fresh detected_at.
$KB --config "$CONFIG" distill record prune --data "$(distill_payload convergent failure-mode 'knowledge/p.md#old' 'old finding returns' promote-to-claude-md "$NOW_TS")" >/dev/null
if python3 -c "
import json
target_hash = '$OLD_HASH'
hit = False
with open('$PRUNE_LEDGER') as f:
    for line in f:
        rec = json.loads(line)
        if rec.get('hash') == target_hash:
            hit = True
            assert rec.get('recurrence_after_retention') is True, rec
            break
assert hit, 'recurring record not present'
" 2>/dev/null; then
    PASS=$((PASS+1))
    echo "  PASS  T6 re-recorded tombstoned finding has recurrence_after_retention=true"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T6 recurrence_after_retention not set after retention"
fi

# --- T7: .kb-internal/ exclusion from reindex/search/recall ---
EXCL_KB="$TMPDIR/distill-excl-kb"
$KB --config "$CONFIG" bootstrap excl --path "$EXCL_KB" >/dev/null 2>&1
mkdir -p "$EXCL_KB/.kb-internal/distill/notes"
echo "SHOULD-NOT-APPEAR marker for T7" > "$EXCL_KB/.kb-internal/distill/notes/secret.md"
$KB --config "$CONFIG" reindex excl --no-commit >/dev/null 2>&1
if [ -f "$EXCL_KB/index.json" ]; then
    if ! grep -q "SHOULD-NOT-APPEAR" "$EXCL_KB/index.json" \
       && ! grep -q ".kb-internal" "$EXCL_KB/index.json"; then
        PASS=$((PASS+1))
        echo "  PASS  T7 reindex skips .kb-internal/ contents"
    else
        FAIL=$((FAIL+1))
        echo "  FAIL  T7 index.json references .kb-internal/ content"
    fi
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T7 index.json was not produced"
fi
SEARCH_OUT=$($KB --config "$CONFIG" search excl "SHOULD-NOT-APPEAR" 2>&1)
if echo "$SEARCH_OUT" | grep -q "No results"; then
    PASS=$((PASS+1))
    echo "  PASS  T7 kb search excludes .kb-internal/"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T7 kb search surfaced .kb-internal/ content: $SEARCH_OUT"
fi
RECALL_OUT=$($KB --config "$CONFIG" recall excl --query "SHOULD-NOT-APPEAR" 2>&1)
if echo "$RECALL_OUT" | grep -q "No results"; then
    PASS=$((PASS+1))
    echo "  PASS  T7 kb recall excludes .kb-internal/"
else
    FAIL=$((FAIL+1))
    echo "  FAIL  T7 kb recall surfaced .kb-internal/ content: $RECALL_OUT"
fi

# T11 — validator rejects naive (timezone-less) detected_at at the boundary.
TZ_KB=$TMPDIR/tz-kb
$KB --config "$CONFIG" bootstrap tz --path "$TZ_KB" >/dev/null
NAIVE_REC='{"track":"divergent","type":"open-question","source":"k/x.md#a","statement":"q","suggested_action":"needs-clarification","detected_at":"2024-01-01T00:00:00"}'
run_fail 2 "T11 reject naive detected_at (no Z or offset)" \
    $KB --config "$CONFIG" distill record tz --data "$NAIVE_REC"
AWARE_REC='{"track":"divergent","type":"open-question","source":"k/x.md#a","statement":"q","suggested_action":"needs-clarification","detected_at":"2026-06-16T12:00:00Z"}'
run "T11 accept aware detected_at (Z suffix)" \
    $KB --config "$CONFIG" distill record tz --data "$AWARE_REC"
run "T11 accept aware detected_at (+HH:MM offset)" \
    $KB --config "$CONFIG" distill record tz --data \
    '{"track":"divergent","type":"open-question","source":"k/y.md#b","statement":"q","suggested_action":"needs-clarification","detected_at":"2026-06-16T14:00:00+02:00"}'

# T12 — `.kb-internal/` self-installs a gitignore; KB repo stays clean across
# record + prune. Plugin-managed maintenance state must not block `kb sync`
# or violate kb-dream's dry-run-first contract by leaving the repo dirty.
GI_KB=$TMPDIR/gi-kb
$KB --config "$CONFIG" bootstrap gi --path "$GI_KB" >/dev/null
$KB --config "$CONFIG" distill record gi --data "$AWARE_REC" >/dev/null
if [ -f "$GI_KB/.kb-internal/.gitignore" ]; then
    PASS=$((PASS+1)); echo "  PASS  T12 .kb-internal/.gitignore self-installed on first record"
else
    FAIL=$((FAIL+1)); echo "  FAIL  T12 .kb-internal/.gitignore missing after record"
fi
GI_DIRTY=$(git -C "$GI_KB" status --porcelain 2>/dev/null | grep -c "\.kb-internal" || true)
if [ "$GI_DIRTY" -eq 0 ]; then
    PASS=$((PASS+1)); echo "  PASS  T12 .kb-internal/ does not dirty the KB repo after record"
else
    FAIL=$((FAIL+1)); echo "  FAIL  T12 .kb-internal/ appeared in git status: $GI_DIRTY entries"
fi
$KB --config "$CONFIG" distill prune gi --ttl-days 1 >/dev/null
GI_DIRTY_AFTER_PRUNE=$(git -C "$GI_KB" status --porcelain 2>/dev/null | grep -c "\.kb-internal" || true)
if [ "$GI_DIRTY_AFTER_PRUNE" -eq 0 ]; then
    PASS=$((PASS+1)); echo "  PASS  T12 .kb-internal/ does not dirty the KB repo after prune"
else
    FAIL=$((FAIL+1)); echo "  FAIL  T12 prune left .kb-internal/ dirty: $GI_DIRTY_AFTER_PRUNE entries"
fi

# T13 — JSON-mode surface always emits valid JSON. Empty ledger AND
# filter-to-zero both return `[]`, so downstream `jq` / kb-dream's
# context-aware emission step parses cleanly. Text mode keeps "doing
# nothing is success" empty-stdout contract (covered by T4).
JSON_KB=$TMPDIR/json-kb
$KB --config "$CONFIG" bootstrap json --path "$JSON_KB" >/dev/null
EMPTY_LEDGER_JSON=$($KB --config "$CONFIG" distill surface json --format json 2>/dev/null)
if [ "$EMPTY_LEDGER_JSON" = "[]" ]; then
    PASS=$((PASS+1)); echo "  PASS  T13 JSON surface on empty ledger emits []"
else
    FAIL=$((FAIL+1)); echo "  FAIL  T13 JSON surface on empty ledger emitted: '$EMPTY_LEDGER_JSON'"
fi
$KB --config "$CONFIG" distill record json --data "$AWARE_REC" >/dev/null
FILTERED_EMPTY_JSON=$($KB --config "$CONFIG" distill surface json --format json --type failure-mode 2>/dev/null)
if [ "$FILTERED_EMPTY_JSON" = "[]" ]; then
    PASS=$((PASS+1)); echo "  PASS  T13 JSON surface with no-match filter emits []"
else
    FAIL=$((FAIL+1)); echo "  FAIL  T13 JSON surface filter-to-zero emitted: '$FILTERED_EMPTY_JSON'"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
