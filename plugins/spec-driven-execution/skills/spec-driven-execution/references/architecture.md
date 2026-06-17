# Architecture pass

When the umbrella decomposition names ≥3 items of plausibly-similar shape (or
any item is described as "like a future one"), pause before per-change framing
and zoom out. The goal is a **grounding document** — pattern vocabulary the
agent reaches for plus a proposed default shape — not a binding spec.

The pass exists to counteract a specific agent failure mode: narrow
implementation focus, where each change is built by copying the previous and
diverging silently. See `failure-modes.md` → *Copy-the-previous-change drift*.

## When to run it

Run when **any** of these is true:

- The decomposition lists 3+ items that look similar (workflows, services,
  parsers, forms, scrapers, pipelines, …).
- A change's framing would naturally start "like {N-1} but …".
- The roadmap is known well past the current change — design for the known
  shape, not the unknown one.

Skip when changes are genuinely heterogeneous (one DB migration + one bugfix +
one UI page = no common shape). **"No common shape — N independent changes"
is a valid result.** Record it and move on; don't manufacture an engine for
work that doesn't have one. Premature abstraction is the inverse failure.

## What you write

A new **Architecture** section in `PROJECT.md` (default), with three parts.
For a heavyweight batch — multi-paragraph rationale, several invariants,
expected to outlive the immediate work — promote it to a dedicated
`.changes/ARCHITECTURE.md`. Same shape as the per-change `proposal.md` vs
`design.md` split.

### Pattern survey

Name the applicable patterns from `references/patterns.md` (or others not
listed there). One line each on why the pattern fits. Cite the canonical
reference rather than reproducing it. Two or three patterns as the spine is
usually right; more than four is pattern soup.

### Proposed default shape

One or two paragraphs sketching the high-level shape — engine + injected
stages, a state machine, a strategy table, a pipeline with named filters. Name
the **extension points** concretely: where each planned change plugs in.

This is a **working hypothesis**, not a contract. It exists to give per-change
framing something to deviate from explicitly, not to lock the design before
the first change has informed it.

### Decisions

Numbered **A-1, A-2, …** so per-change `validation.md` can reference them
(`per A-2`, `deviates from A-3 because …`). Same shape as `D-N` at the change
level; the `A` prefix (architecture) keeps them visually separable from
per-change `D-N` decisions and `I-N` invariants.

A decision typically locks one of:

- a pattern choice (e.g. *A-1: workflows are a pipeline + strategy; stages
  inject the variant logic*);
- an extension point (*A-2: triage stage produces a `WorkItem` iterable*);
- an explicit non-decision (*A-3: dry-run/live mode handled by the engine,
  not per-workflow*).

## Deviation contract

A change going off-shape is fine — sometimes the architecture is wrong, often
a specific change has a constraint the architecture didn't anticipate. The
rule is that deviation must be **explicit**, not silent.

A change's `validation.md` either:

- references `A-N` in its locked decisions ("per A-2: this workflow uses the
  shared `triage` stage"), OR
- records a deviation ("deviates from A-2: this workflow's stage 1 is not
  config-driven because …").

Silent drift is the failure mode. Naming the deviation makes it visible at
review time and at archive time — and surfaces when the architecture itself
should change.

## Worked example: WARDEN workflows

The batch shape: build N workflows (assigned-issues, cloudwatch-scan,
tech-debt-scan, distill, kb-consolidate). Each takes a triage signal → opens
PR(s) → reconciles state.

A pattern survey would have named **pipeline** (sequential stages),
**strategy** (per-workflow triage logic), **dependency injection** (stages
composed at engine construction).

A proposed default shape: one workflow engine, three injected stages —
`triage` produces a work-list, `implement` is the LLM step that opens PR(s),
`finalize` reconciles state. Dry-run / agent-dry-run / live become an engine
concern decided once.

Extension points: each new workflow plugs in a `triage` strategy and an
`implement` skill; `finalize` is shared.

Without the pass, each workflow was copy-pasted from the previous and
diverged — fragmented `run.py`s, three near-duplicate verdict tools, the
#362 bug where assigned-issues inherited cloudwatch-scan's read-only `Read/
Grep/Glob` tool grant without inheriting the reproduction harness that
justified it.

## Subagent: Architect

When delegating the pass to a subagent:

> "Read `.changes/PROJECT.md`. Survey the candidate decomposition. Identify
> the common shape, if any. Propose: (a) a pattern survey naming 2–4
> applicable patterns from `references/patterns.md` with a one-line fit
> rationale each; (b) a proposed default shape (engine, pipeline, state
> machine, …) with concrete extension points; (c) numbered `A-N` decisions
> the per-change framings will reference. If the changes are genuinely
> heterogeneous, say so explicitly — 'no common shape' is a valid output."

The escape-hatch instruction is load-bearing: a subagent under pressure to
produce a shape will manufacture one.
