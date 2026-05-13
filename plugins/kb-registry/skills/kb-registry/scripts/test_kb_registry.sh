#!/usr/bin/env bash
# Lightweight repeatable validation for kb-registry.
# Run from the agents repo root:  bash plugins/kb-registry/skills/kb-registry/scripts/test_kb_registry.sh
#
# Uses a temporary config and a temporary KB by default.
# Set KB_REGISTRY_TEST_KB=../test-kb to validate against a chosen path.
# Existing test KB paths are not deleted unless KB_REGISTRY_TEST_RESET=1.

set -euo pipefail

KB="python3 plugins/kb-registry/skills/kb-registry/scripts/kb"
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
run "git repo init" git -C "$TEST_KB" rev-parse --git-dir

echo ""
echo "--- 3. List + Status ---"
run "list" $KB --config "$CONFIG" list
run "list --json" $KB --config "$CONFIG" list --json
run "status test" $KB --config "$CONFIG" status test

echo ""
echo "--- 4. Brief ---"
run "brief test" $KB --config "$CONFIG" brief test
run "brief --json" $KB --config "$CONFIG" brief test --json
run "brief --max-chars" $KB --config "$CONFIG" brief test --max-chars 100

echo ""
echo "--- 5. Stage ---"
run "stage decision" $KB --config "$CONFIG" stage test --kind decision --note "Test decision note."
run "stage raw-note" $KB --config "$CONFIG" stage test --kind raw-note --note "Test raw note."

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
echo "--- 6. Safety ---"
run_fail 3 "reject AWS key" $KB --config "$CONFIG" stage test --note "key is AKIA1234567890ABCDEF"
run_fail 3 "reject private key" $KB --config "$CONFIG" stage test --note "-----BEGIN PRIVATE KEY-----"
run_fail 3 "reject generic secret" $KB --config "$CONFIG" stage test --note "password=hunter2"

echo ""
echo "--- 7. Search ---"
run "search test" $KB --config "$CONFIG" search test "decision"
run "search --json" $KB --config "$CONFIG" search test "decision" --json
run "search all KBs" $KB --config "$CONFIG" search "note"

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
run "plugin.json exists" test -f plugins/kb-registry/.claude-plugin/plugin.json
run "SKILL.md exists" test -f plugins/kb-registry/skills/kb-registry/SKILL.md
run "kb-dream SKILL.md exists" test -f plugins/kb-registry/skills/kb-dream/SKILL.md
run "plugin.json valid JSON" python3 -c "import json; json.load(open('plugins/kb-registry/.claude-plugin/plugin.json'))"
run "marketplace registered" python3 -c "
import json
d = json.load(open('.claude-plugin/marketplace.json'))
assert any(p['name'] == 'kb-registry' for p in d['plugins'])
"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
