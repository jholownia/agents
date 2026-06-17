# Pattern vocabulary

A short reference for the architecture pass. Naming a pattern doesn't bind
anyone — it just puts the right word in the agent's working vocabulary so
they reach for the shape *deliberately* instead of defaulting to whatever the
local code path already does.

The list is intentionally short. Each entry: name, a one-line *consider when*
tell, what the pattern gives you, and the canonical reference. Reach past
this list when the work calls for it; this is a starter vocabulary, not a
ceiling.

## Strategy

- **Consider when:** you're about to branch on a config flag or enum to pick
  between behaviours, *and* you expect more variants later.
- **What it gives you:** a single dispatch site; new variants register
  themselves rather than editing the existing if/elif chain.
- **Reference:** Gamma et al., *Design Patterns*; Fowler, *Refactoring* —
  "Replace Conditional with Polymorphism" / "Replace Conditional with
  Strategy".

## Command

- **Consider when:** operations need to be queueable, retryable, undoable, or
  inspectable as data after the fact.
- **What it gives you:** operations as first-class objects — loggable,
  serialisable, replayable without re-running the side effect.
- **Reference:** Gamma et al., *Design Patterns*.

## Policy

- **Consider when:** you're about to add a boolean flag to a function —
  especially the second one. Multiple booleans hide ~2^n behaviours.
- **What it gives you:** named variants for the decision the boolean was
  hiding; each variant testable in isolation and composable.
- **Reference:** [Don't use boolean flags in Python — use policies
  instead](https://app.daily.dev/posts/don-t-use-boolean-flags-in-python-use-policies-instead-o89vpoe4h).

## Pipeline (Pipes and Filters)

- **Consider when:** the work is a sequence of transformations, each stage
  independently testable, and the stage list might grow.
- **What it gives you:** stages as first-class objects; insertable,
  removable, reorderable without touching the engine.
- **Reference:** Fowler, *Patterns of Enterprise Application Architecture*
  (Pipes and Filters); Hohpe & Woolf, *Enterprise Integration Patterns*.

## State machine

- **Consider when:** an `if/else` on `current_state` already lives in 2+
  places, or invalid state transitions are causing bugs.
- **What it gives you:** transitions as named edges; validity becomes a
  property of the graph rather than scattered conditionals.
- **Reference:** Hopcroft & Ullman, *Introduction to Automata Theory*; for
  hierarchical / concurrent state: Harel, *Statecharts*.

## Dependency injection

- **Consider when:** a function reaches for `os.environ`, a module-level
  config, or a global to find a collaborator — testing requires
  monkey-patching.
- **What it gives you:** swap collaborators per call site; tests instantiate
  fakes without patching globals.
- **Reference:** Fowler, [*Inversion of Control Containers and the
  Dependency Injection pattern*](https://martinfowler.com/articles/injection.html).

## Ports and adapters (hexagonal)

- **Consider when:** infra concerns (HTTP, DB, filesystem, message bus) leak
  into pure logic — the unit test for "did we compute X" has to mock S3.
- **What it gives you:** core logic stays IO-free; infra adapters plug in at
  the edge. Swap the adapter, keep the core.
- **Reference:** Cockburn, [*Hexagonal Architecture*](https://alistair.cockburn.us/hexagonal-architecture/).

## Shared skeleton + hooks (Template Method)

- **Consider when:** N items follow the same orchestration shape (steps in
  the same order, same control flow, same finalisation) but each varies a
  small set of steps. The WARDEN-workflows failure mode.
- **What it gives you:** the orchestration is written once; variants supply
  only the hook implementations. New items can't drift from the skeleton
  because they don't own it.
- **Reference:** Gamma et al., *Design Patterns* (Template Method). In a
  functional codebase the same idea is a higher-order function that takes
  the variant steps as callables — *don't reach for inheritance just
  because the pattern name suggests a base class*.

## Antipatterns to watch during the pass

- **Premature abstraction.** Abstracting from one example. Rule of three:
  three concrete instances before extracting. The architecture pass uses the
  *known roadmap* to satisfy the rule of three — abstractions are grounded
  in named, anticipated instances, not imagined ones. If the roadmap only
  has two items, prefer copy-paste with eyes open over an engine for two.
- **Pattern soup.** Naming every pattern that fits and ending up with none
  of them as the dominant shape. Pick one or two as the spine; mention
  others as candidates for specific stages within.
- **Naming without grounding.** "We'll use the Strategy pattern" without
  saying *what the strategy interface is* and *which planned changes plug
  into it* is a label, not a design. The deviation contract in
  `architecture.md` is what gives the names teeth.
