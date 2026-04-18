# ADVANCEMENT_RULES

This is a Phase I constitutional artifact. It defines what must be true before a layer, detector, gate, artifact, summary surface, or phase claim is allowed to advance from local work into canonical project state.

## Scope and Role in Phase I

- This document governs advancement claims, not implementation details.
- It does not ratify any specific layer by itself.
- It does not replace empirical grounding, rebuild rationale, constraints, or the build ledger.
- It defines the minimum lawful conditions under which a thing may be treated as:
  - exploratory
  - diagnostic
  - candidate-canonical
  - earned canonical
  - phase-closing

Exploratory and diagnostic work may exist before full closure. They may be useful, informative, and worth preserving. But they are not authoritative architecture merely because they run, pass local tests, or feel complete.

## Governing Inputs

This document is subordinate to and interpreted with:

- `governance/QD_END_TO_END_BUILD_PLAN_v0_3.md`
- `governance/EXPERIMENTAL_FOUNDATION.md`
- `governance/REBUILD_RATIONALE.md`
- `governance/CONSTRAINTS.md`
- `BUILD_LEDGER.md`

If an advancement claim contradicts any of the above, the advancement claim fails unless the contradiction is explicitly handled as a constitutional reopening event.

## Core Principle

A thing is not earned because it exists.

A thing is earned only when it:
1. is grounded,
2. is bounded,
3. is necessary,
4. is testable,
5. survives pressure,
6. is legible to a cold session,
7. is recorded into canonical state without ambiguity.

## Advancement Status Classes

### 1. Exploratory
Used for ideas, drafts, probes, experiments, prototypes, or observations that may be valuable but have not yet earned canonical standing.

Exploratory work:
- may inform later architecture
- may expose useful pressure points
- may be kept in-repo
- must not be treated as constitutional proof
- must not silently become load-bearing

### 2. Diagnostic
Used for layers or artifacts whose role is measurement, audit, comparison, or visibility rather than canonical truth determination.

Diagnostic work:
- may be necessary
- may become durable
- must declare itself diagnostic if it is not canonical
- must not silently substitute for the thing it audits

### 3. Candidate-Canonical
Used for a layer or artifact that has a named purpose, explicit dependencies, bounded claims, and a real test path, but has not yet completed full advancement conditions.

Candidate-canonical work:
- is under serious consideration
- may be pressure-tested
- may be implemented
- must not be presented as settled until full advancement conditions are met

### 4. Earned Canonical
Used only when a layer or artifact has satisfied all required advancement rules below and has been synthesized into canonical project state.

### 5. Phase-Closing
Used only when the relevant phase exit conditions from the governing build plan are satisfied, not merely when a set of local tasks feels complete.

## Required Advancement Rules

### A1. No advancement without a named phenomenon or governing need
A proposed layer must answer at least one of these clearly:
- What real phenomenon does it detect?
- What real failure does it prevent?
- What governing obligation does it satisfy?

If it cannot name a concrete reason to exist, it does not advance.

### A2. No advancement without declared status
Every new thing must declare which status class it currently occupies:
- exploratory
- diagnostic
- candidate-canonical
- earned canonical

If status is left implicit, advancement fails.

### A3. No advancement without explicit dependency and scope disclosure
A proposed layer must state:
- what it depends on
- what it does not depend on
- what it is allowed to influence
- what it must not silently influence

If its upstream/downstream role is ambiguous, advancement fails.

### A4. No advancement without bounded claims
A layer must say what it does and what it does not claim.

This includes:
- what problem it solves
- what it does not solve
- whether it is local or system-wide
- whether it is canonical or diagnostic only

If the boundaries are blurry, advancement fails.

### A5. No advancement without falsifiability and test path
A proposed layer must have a concrete way to show:
- what success looks like
- what failure looks like
- what evidence would disconfirm the claim
- how the claim is tested

If there is no real test path, it does not advance.

### A6. No advancement without constraint compliance
A proposed layer or artifact must not violate any constraint ratified in `governance/CONSTRAINTS.md`.

`CONSTRAINTS.md` is the single source of truth for the current binding constraint set.

If an advancement claim depends on violating a ratified constraint, advancement fails.

### A7. No advancement from unavailable or reconstructed continuity alone
Missing artifacts, remembered thread context, or informal prior understanding may guide inquiry, but they do not by themselves authorize canonical advancement.

Unavailable lineage must remain explicit HOLD or bounded reconstruction unless recovered or replaced through governed ratification.

### A8. No advancement from local success alone
The following are not sufficient by themselves:
- passing local tests
- internal elegance
- clean implementation
- completion of one repo-local loop
- absence of immediate criticism

Local correctness may be necessary. It is never sufficient as constitutional proof.

### A9. No advancement without pressure from outside the implementation seat
A major layer or artifact must survive critique from at least one non-invested pressure seat before being treated as earned.

Pressure must check for:
- overclaiming
- hidden assumptions
- scope inflation
- structural substitution
- contradiction with governing artifacts
- false certainty

If it has not survived pressure, it has not advanced fully.

### A10. No advancement without cold-session legibility
A cold session must be able to determine:
- what the thing is
- what it is for
- what status it has
- what it depends on
- what it must not be confused with
- whether it is settled, open, diagnostic, or exploratory

If that cannot be recovered from repo-visible governance state, advancement is incomplete.

### A11. No advancement is complete until canonical state is updated
A thing may be useful, implemented, tested, and pressure-surviving without yet being fully advanced.

Advancement is not complete until canonical project state is updated to reflect it.

Canonical update means, at minimum:
- the item’s status is written explicitly
- its boundaries and dependencies are stated clearly
- its ratification or non-ratification state is visible
- `BUILD_LEDGER.md` reflects the current honest posture
- the next frontier is not left ambiguous

If the thing exists but canonical state does not reflect it honestly, advancement remains incomplete.

## Minimum Advancement Packet

Before calling a layer or artifact advanced, the project must be able to answer all of the following:

1. What is the named phenomenon, failure, or governing need?
2. Is the item exploratory, diagnostic, candidate-canonical, or earned canonical?
3. What are its dependencies and boundaries?
4. What exact claim is being made?
5. What would falsify that claim?
6. What tests or pressure path were used?
7. What ratified artifacts does it rely on?
8. What constraints did it have to satisfy?
9. What would be lost if it were absent?
10. Has its status been written into canonical project state?

If any of these are missing, the advancement claim is incomplete.

## What Counts as Advancement

Advancement means one or more of the following has happened:

- a hidden assumption became explicit
- a disconnected lineage became connected
- a structural lie was removed
- a real phenomenon gained a lawful detector
- a layer survived pressure it previously could not survive
- a drift risk became governed instead of merely noticed
- a previously local or ambiguous layer gained explicit canonical status and boundaries

## What Does Not Count as Advancement

The following may contribute to quality, clarity, or usefulness, but do not count as advancement evidence by themselves:

- more code
- more documents
- more tests
- prettier wording
- cleaner diagrams
- stronger intuition
- remembered context from an unavailable thread
- a helper tool saying a thing looks right
- local completion without constitutional closure
- diagnostic usefulness being mistaken for canonical authority

## Reopening Rules

Once a layer or artifact is treated as earned canonical, it is not casually reopened in ordinary build flow.

Reopening a ratified governing artifact requires an explicit constitutional event, not casual revision, drift, or convenience editing.

Explicit reopening is required when:
- a ratified constraint would need to change
- a settled principle would need reinterpretation
- a phase-closing claim is shown to be false
- a canonical artifact conflicts with a newer ratified constitutional artifact
- a previously unavailable source materially changes the inheritance picture

Ordinary bug fixes, wording tightenings, tests, and clarity improvements do not constitute constitutional reopening unless they alter governing meaning.

## Phase-Level Advancement Rule

A phase does not close because several useful things were built.

A phase closes only when the governing build plan’s exit condition for that phase is satisfied in repo-visible, cold-session-legible form.

Anything less is progress inside the phase, not closure of the phase.

## Relationship to Other Constitutional Artifacts

- `EXPERIMENTAL_FOUNDATION.md` governs empirical inheritance and measurement obligation.
- `REBUILD_RATIONALE.md` governs why rebuild constraints exist and what must not reappear.
- `CONSTRAINTS.md` governs what is forbidden or bounded.
- `ADVANCEMENT_RULES.md` governs how something earns the right to move forward under those inherited obligations and constraints.
- `BUILD_LEDGER.md` records the honest current state after advancement has or has not occurred.

## Pressure-Test Readiness

This document is pressure-test-ready if each advancement rule can be checked for:

1. compatibility with the governing build plan,
2. non-contradiction with empirical and rebuild artifacts,
3. consistency with ratified constraints,
4. usefulness in preventing false advancement,
5. clarity for a cold session.

## Non-Goals / Non-Claims

- This document does not claim every useful experiment must be canonical.
- This document does not claim exploratory work is low value.
- This document does not claim implementation success is meaningless.
- This document does not claim all advancement is phase closure.
- This document does not replace the need for judgment, pressure, or ledger honesty.

It exists to prevent local success, missing lineage, or good intentions from being mistaken for earned constitutional advancement.
