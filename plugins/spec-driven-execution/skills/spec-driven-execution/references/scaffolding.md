# Scaffolding

How to bootstrap `.changes/` from scratch and seed `PROJECT.md` from the work's
actual origin (GitHub issue or freeform prompt).

## From a GitHub issue

```bash
# 1. Fetch the issue body + linked subissues
gh issue view <N> --json title,body,url
gh issue view <N> --json body --jq .body  # raw body for direct copy

# 2. If the issue references subissues, fetch those too
gh issue view <M> --json title,body,url
```

Read the issue. Look for:

- **An explicit decomposition the user already wrote** — numbered list, table,
  "subtasks" section. Each item usually maps 1:1 to a change folder.
- **Spec / design pointers** — links to a spec repo, design doc, or related
  issue. These belong in `PROJECT.md` "Context".
- **Scope boundaries the user has already drawn** — "this doesn't include X",
  "Y is out of scope". Quote these verbatim. They're load-bearing.
- **Stakeholders or deadlines** — anyone else who needs to know, anything date-gated.

Then:

1. Surface the proposed decomposition to the user, ask once, commit:
   > "I'd like to split #{N} into these change folders:
   > 1. `1-schema-migration` — new tables, drop legacy
   > 2. `2-service-rewrite` — main service logic
   > 3. `3-downstream-integration` — consumers + adapters
   > 4. `4-integration-tests` — end-to-end harness
   > Sound right, or do you want to merge / split any of these?"
2. Scaffold the directory:
   ```bash
   mkdir -p .changes/active .changes/archive
   ```
3. Copy the protocol file and project template:
   ```bash
   cp <skill-path>/assets/templates/CLAUDE.md .changes/CLAUDE.md
   cp <skill-path>/assets/templates/PROJECT.md .changes/PROJECT.md
   ```
4. Fill in `PROJECT.md`:
   - **Source:** the issue URL, the issue body **verbatim** (don't paraphrase
     — paraphrasing loses scope nuance). Use `gh issue view <N> --json body --jq .body` to get the raw text.
   - **External context:** spec repo paths, related docs, Slack threads.
   - **Decomposition:** the table the user just confirmed.
   - **Scope boundaries:** quoted clarifications from the issue and the
     surfacing exchange.

## From a freeform prompt

When the work originates in conversation, not a tracked issue:

1. **Restate.** Say back the goal in domain terms. The restated form goes into
   `PROJECT.md` as "Source: conversation, restated".
2. **Probe.** Ask only what you can't infer:
   - Deadline? Anyone else involved?
   - What's the smallest correct version of "done"?
   - Adjacent things that look in scope but aren't?
3. **Decompose.** Same as above — propose 3–7 folders, ask, commit.
4. **Scaffold + fill `PROJECT.md`.**

If the probing reveals the work is small (one folder, <10 tasks, one sitting),
skip the protocol entirely. Tell the user: "this is small enough to do
inline — I'll just work it without the change folder."

## From an in-flight piece of work

Sometimes the work already started before anyone reached for this protocol. Bootstrap
*retroactively*:

1. Inventory what's done so far — commits, PRs, scratch files.
2. Write `PROJECT.md` from the inventory. The "Source" section captures whatever
   triggered the work (often a conversation, sometimes a thread of commits).
3. Create one `archive/0-pre-protocol-work/` folder describing what landed
   before the protocol started, so the audit trail isn't blank up to a date.
4. Frame the **remaining** work as `active/{N-slug}/` folders. Don't try to
   retro-frame work that's already merged.

## PROJECT.md content

Keep it short. Sections, in order:

- **Source** — issue URL + verbatim body, or restated conversation goal.
- **Authoritative external context** — spec repo paths, design docs, with one-line summaries.
- **Decomposition** — table mapping change folders to subissues or sub-tasks, with status.
- **Scope boundaries** — quoted clarifications, what's in this batch, what's adjacent.
- **For dispatched agents** — read order: `.changes/CLAUDE.md`, `PROJECT.md`,
  `active/{change-id}/description.md`, `active/{change-id}/validation.md`, then the
  external specs.

If a section is empty for this work, omit it. Don't pad.

## Naming the change folders

- `{N}-{slug}` where `N` is the local ordering number (1, 2, 3…).
- Slug is grep-friendly kebab-case, 1–4 words: `schema-migration`,
  `service-rewrite`, `final-ab-validation`.
- The number reflects intended execution order, not priority. If order shifts
  mid-flight, leave the numbers as-is — renumbering breaks grep history.
- Numbering is local to the branch. Collisions across branches resolve manually
  on merge.
