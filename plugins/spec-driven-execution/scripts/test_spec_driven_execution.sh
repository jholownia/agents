#!/usr/bin/env bash
# Lightweight structural validation for the spec-driven-execution plugin.
# Run from the agents repo root:
#   bash plugins/spec-driven-execution/scripts/test_spec_driven_execution.sh
#
# This plugin ships no runtime code, so the test is a structural smoke check:
# manifest validity, required frontmatter, presence of templates and
# references the SKILL.md points at.

set -euo pipefail

ROOT="plugins/spec-driven-execution"
SKILL_DIR="$ROOT/skills/spec-driven-execution"
PASS=0
FAIL=0

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

echo "=== spec-driven-execution Validation ==="
echo ""

echo "--- 1. Manifest ---"
run "plugin.json exists" test -f "$ROOT/.claude-plugin/plugin.json"
run "plugin.json is valid JSON" python3 -c "import json; json.load(open('$ROOT/.claude-plugin/plugin.json'))"
run "plugin.json has name" python3 -c "
import json
d = json.load(open('$ROOT/.claude-plugin/plugin.json'))
assert d.get('name') == 'spec-driven-execution', d
"
run "plugin.json has version" python3 -c "
import json
d = json.load(open('$ROOT/.claude-plugin/plugin.json'))
assert isinstance(d.get('version'), str) and d['version'], d
"

echo ""
echo "--- 2. Marketplace registration ---"
run "marketplace.json registers spec-driven-execution" python3 -c "
import json
d = json.load(open('.claude-plugin/marketplace.json'))
assert any(p['name'] == 'spec-driven-execution' for p in d['plugins']), d
"
run "marketplace version matches plugin.json" python3 -c "
import json
mkt = json.load(open('.claude-plugin/marketplace.json'))
mfst = json.load(open('$ROOT/.claude-plugin/plugin.json'))
entry = next(p for p in mkt['plugins'] if p['name'] == 'spec-driven-execution')
assert entry.get('version') == mfst.get('version'), (entry, mfst)
"

echo ""
echo "--- 3. Skill structure ---"
run "SKILL.md exists" test -f "$SKILL_DIR/SKILL.md"
run "SKILL.md has name: frontmatter" python3 -c "
import re
text = open('$SKILL_DIR/SKILL.md').read()
m = re.search(r'^name:\s*spec-driven-execution\s*$', text, re.M)
assert m, 'name: spec-driven-execution missing in frontmatter'
"
run "SKILL.md has description: frontmatter" python3 -c "
import re
text = open('$SKILL_DIR/SKILL.md').read()
assert re.search(r'^description:\s*\S', text, re.M), 'description: missing or empty'
"
run "SKILL.md has version: frontmatter" python3 -c "
import re
text = open('$SKILL_DIR/SKILL.md').read()
assert re.search(r'^version:\s*\d', text, re.M), 'version: missing'
"
run "description uses Anthropic third-person template" python3 -c "
import re
text = open('$SKILL_DIR/SKILL.md').read()
# Match \"This skill should be used when\" near the start of the frontmatter.
m = re.search(r'^description:\s*This skill should be used when', text, re.M)
assert m, 'description should open with \"This skill should be used when ...\"'
"

echo ""
echo "--- 4. References ---"
for ref in framing scaffolding failure-modes architecture patterns; do
    run "references/$ref.md exists" test -f "$SKILL_DIR/references/$ref.md"
done

echo ""
echo "--- 5. Template assets ---"
for tpl in CLAUDE PROJECT description validation tasks proposal design impact; do
    run "assets/templates/$tpl.md exists" test -f "$SKILL_DIR/assets/templates/$tpl.md"
done

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
