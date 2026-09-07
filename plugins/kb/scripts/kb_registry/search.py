"""Lexical search: rg-first with Python fallback.

Queries are tokenised into alphanumeric terms before matching, so a
sentence-shaped query ("how do we handle a stale index") still reaches a
page titled "Stale index handling". Files rank by how many distinct query
terms they carry; lines containing the whole query sort first within a
file. Both backends share the tokeniser, the case rule, and the ranker, so
environments without rg (typical CI runners) see the same hits.
"""

import fnmatch
import json
import os
import re
import shutil
import subprocess


def _rg_available():
    return shutil.which("rg") is not None


# Matches emitted per file. A single hit per file frequently lands in
# frontmatter; 3 lets the agent see body matches too without flooding.
_DEFAULT_MAX_PER_FILE = 3
# Matches collected per file before ranking. Ranking needs more candidates
# than it emits, or the best line in a file gets cut before it is scored.
_CANDIDATE_MAX_PER_FILE = 20
# Ceiling on collected candidates, so a huge KB or a very common term
# cannot balloon memory before ranking.
_CANDIDATE_MAX_TOTAL = 5000

# Function words carry no retrieval signal but match everywhere, which
# would swamp coverage ranking. Negations are deliberately absent — "not"
# is a meaningful token in technical prose.
_STOPWORDS = frozenset({
    "a", "about", "all", "an", "and", "any", "are", "as", "at", "be",
    "because", "been", "but", "by", "can", "did", "do", "does", "for",
    "from", "had", "has", "have", "how", "if", "in", "into", "is", "it",
    "its", "me", "my", "of", "on", "or", "our", "out", "over", "should",
    "so", "that", "the", "their", "them", "then", "there", "these",
    "they", "this", "those", "to", "up", "us", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "why", "will",
    "with", "would", "you", "your",
})


def tokenize_query(query):
    """Split a query into distinct match terms, preserving original case.

    A query with no whitespace is an identifier — "foo(bar)",
    "-dash-token", "analyze_meter_drift" — and is matched verbatim rather
    than split, so exact lookups keep their old precision. Splitting those
    on punctuation turns a distinctive string into common words that hit
    everywhere. Only multi-word queries tokenise, which is the case the
    old literal matching handled badly.

    Case survives so callers can apply smart-case. Stopwords and single
    characters drop out unless that would empty the query — an all-stopword
    query still has to search for something.
    """
    stripped = query.strip()
    if not stripped:
        return []
    if len(stripped.split()) == 1:
        return [stripped]

    tokens = []
    seen = set()
    for tok in re.findall(r"[0-9A-Za-z]+", query):
        key = tok.lower()
        if key in seen:
            continue
        seen.add(key)
        tokens.append(tok)
    meaningful = [
        t for t in tokens if len(t) > 1 and t.lower() not in _STOPWORDS
    ]
    return meaningful or tokens


def min_coverage(term_count):
    """Distinct terms a file must carry to qualify as a hit.

    One- and two-term queries demand every term, keeping short queries
    precise. Longer queries relax to half, so a single off word in a
    sentence-shaped query no longer zeroes the result set.
    """
    if term_count <= 2:
        return term_count
    return max(2, (term_count + 1) // 2)


def case_sensitive_for(terms):
    """Smart-case decided on the terms actually searched.

    Deciding on the raw query would diverge between backends: in "A stale
    index" the uppercase "A" drops as a stopword, so rg's --smart-case
    (which inspects the pattern) would ignore case while a raw-query check
    would not. Both backends read this instead, and rg gets an explicit
    --case-sensitive/--ignore-case.
    """
    return any(c.isupper() for t in terms for c in t)


def _extract_title(abs_path):
    """Derive a result title: first H1 -> first non-blank body line ->
    filename slug. Skips YAML frontmatter."""
    try:
        with open(abs_path, "r", errors="replace") as f:
            in_frontmatter = False
            seen_open_dashes = False
            for raw in f:
                line = raw.rstrip("\n")
                if line.strip() == "---":
                    if not seen_open_dashes:
                        in_frontmatter = True
                        seen_open_dashes = True
                        continue
                    if in_frontmatter:
                        in_frontmatter = False
                        continue
                if in_frontmatter:
                    continue
                if line.startswith("# "):
                    return line[2:].strip()
                if line.strip():
                    return line.strip()[:80]
    except Exception:
        pass
    base = os.path.splitext(os.path.basename(abs_path))[0]
    return base.replace("-", " ").replace("_", " ").title()


def _collect_rg(path, terms, case_sensitive, glob_pattern, exclude_inbox):
    """Gather raw (abs_path, rel_path, line_number, text) candidates via rg."""
    args = [
        "rg", "--json",
        "--case-sensitive" if case_sensitive else "--ignore-case",
        "--max-count", str(_CANDIDATE_MAX_PER_FILE),
        "--glob", "!.git",
        # I-5: .kb-internal/ is plugin-managed, never searched.
        "--glob", "!.kb-internal/",
    ]
    if exclude_inbox:
        args += ["--glob", "!inbox/"]
    # Default to markdown only, matching the Python fallback. Without it rg
    # also reads index.json, whose summaries match almost any term once the
    # query is an alternation.
    args += ["--glob", glob_pattern or "*.md"]
    if len(terms) == 1:
        # Single term covers the identifier path, where the term is the raw
        # query and may hold regex metacharacters. --fixed-strings keeps it
        # literal, matching the fallback's re.escape.
        args += ["--fixed-strings", "-e", terms[0], path]
    else:
        # Multi-term alternation. Tokenised terms are alphanumeric by
        # construction, so this needs no escaping and cannot be mistaken
        # for an rg flag; -e keeps that true regardless.
        args += ["-e", "|".join(terms), path]

    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    candidates = []
    for line in r.stdout.splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "match":
            continue
        data = obj["data"]
        abs_path = data["path"]["text"]
        candidates.append((
            abs_path,
            os.path.relpath(abs_path, path),
            data["line_number"],
            data["lines"]["text"],
        ))
        if len(candidates) >= _CANDIDATE_MAX_TOTAL:
            break
    return candidates


def _collect_python(path, terms, case_sensitive, glob_pattern, exclude_inbox):
    """Fallback: walk the tree and gather the same raw candidates with re."""
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile("|".join(re.escape(t) for t in terms), flags)
    except re.error:
        return []

    candidates = []
    for dirpath, dirnames, filenames in os.walk(path):
        if ".git" in dirnames:
            dirnames.remove(".git")
        # I-5: .kb-internal/ is plugin-managed, never searched.
        if ".kb-internal" in dirnames:
            dirnames.remove(".kb-internal")
        rel_dir = os.path.relpath(dirpath, path)
        if exclude_inbox and (rel_dir == "inbox" or rel_dir.startswith(
                "inbox" + os.sep)):
            continue
        for fname in filenames:
            if not fname.endswith(".md"):
                continue
            if glob_pattern and not _glob_match(fname, glob_pattern):
                continue
            fpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fpath, path)
            try:
                with open(fpath, "r", errors="replace") as f:
                    hits = 0
                    for i, line in enumerate(f, 1):
                        if not pattern.search(line):
                            continue
                        candidates.append((fpath, rel_path, i, line))
                        hits += 1
                        if hits >= _CANDIDATE_MAX_PER_FILE:
                            break
            except Exception:
                continue
            if len(candidates) >= _CANDIDATE_MAX_TOTAL:
                return candidates
    return candidates


def _rank(candidates, terms, query, case_sensitive, max_results):
    """Rank raw candidates by per-file distinct-term coverage.

    A file qualifies once it carries `min_coverage` of the query's terms;
    files are then ordered by coverage, and within a file the lines that
    carry the most terms (or the whole query verbatim) come first.
    """
    match_terms = [t if case_sensitive else t.lower() for t in terms]
    phrase = query if case_sensitive else query.lower()
    required = min_coverage(len(match_terms))

    files = {}
    for abs_path, rel_path, line_no, text in candidates:
        hay = text if case_sensitive else text.lower()
        hit_terms = {t for t in match_terms if t in hay}
        if not hit_terms:
            continue
        score = len(hit_terms) + (2 if phrase and phrase in hay else 0)
        entry = files.setdefault(
            rel_path, {"abs": abs_path, "terms": set(), "lines": []}
        )
        entry["terms"] |= hit_terms
        entry["lines"].append((-score, line_no, len(hit_terms), text.strip()))

    ranked = []
    for rel_path, entry in files.items():
        coverage = len(entry["terms"])
        if coverage < required:
            continue
        entry["lines"].sort()
        best_line_score = -entry["lines"][0][0]
        ranked.append((-coverage, -best_line_score, rel_path, entry))
    ranked.sort(key=lambda x: (x[0], x[1], x[2]))

    results = []
    title_cache = {}
    for _, _, rel_path, entry in ranked:
        abs_path = entry["abs"]
        if abs_path not in title_cache:
            title_cache[abs_path] = _extract_title(abs_path)
        for _, line_no, term_hits, text in \
                entry["lines"][:_DEFAULT_MAX_PER_FILE]:
            results.append({
                "path": rel_path,
                "line": line_no,
                "title": title_cache[abs_path],
                "snippet": text[:200],
                "match_count": term_hits,
            })
            if len(results) >= max_results:
                return results
    return results


def _glob_match(filename, pattern):
    """Shell-style glob match (e.g. *.md, decision-*.md)."""
    return fnmatch.fnmatch(filename, pattern)


def search_kb(path, query, max_results=20, glob_pattern=None,
              exclude_inbox=False):
    """Search a single KB. Returns list of result dicts."""
    terms = tokenize_query(query)
    if not terms:
        return []
    case_sensitive = case_sensitive_for(terms)
    collect = _collect_rg if _rg_available() else _collect_python
    candidates = collect(
        path, terms, case_sensitive, glob_pattern, exclude_inbox
    )
    return _rank(candidates, terms, query, case_sensitive, max_results)
