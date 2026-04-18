# CONSTRAINTS

This is a Phase I constitutional artifact. It converts ratified empirical and rebuild findings into enforceable guardrails for governance progression and downstream build work.

## Scope and Role in Phase I

- This document defines constitutional constraints, not implementation details.
- It is binding for sessions that propose or perform architecture-affecting work.
- It is grounded in:
  - `governance/QD_END_TO_END_BUILD_PLAN_v0_3.md`
  - `governance/EXPERIMENTAL_FOUNDATION.md`
  - `governance/REBUILD_RATIONALE.md`
- It does not prohibit exploratory or diagnostic work. It prohibits treating such work as canonical before constitutional earning conditions are satisfied.

## Constraint Format

Each constraint is enforceable through this structure:
- **Statement:** the binding rule.
- **Why it exists:** the failure/risk it prevents.
- **Source grounding:** direct artifact basis and/or governance-derived constitutional basis.
- **What it forbids:** disallowed actions or claims.
- **What it still allows:** allowed work within bounds.

## Locked Constraint Set

### C1. No Silent Runtime Mode Variance
- **Statement:** Runtime mode differences that affect behavior must be explicit, observable, and auditable; silent fallback variance is prohibited for canonical paths.
- **Why it exists:** Ratified rebuild findings identify silent mode variance as a reproducibility and trust risk.
- **Source grounding:** directly grounded in `REBUILD_RATIONALE.md` (fallback variance risk) and `EXPERIMENTAL_FOUNDATION.md` (explicit mode-obligation requirement).
- **What it forbids:** hidden fallback behavior, undocumented mode switching, and equivalence claims across environments without mode disclosure.
- **What it still allows:** diagnostic fallback experimentation, provided it is explicitly labeled, traceable, and non-canonical.

### C2. No Externalized Critical Gating
- **Statement:** Safety-critical or truth-critical gating cannot depend on implicit external caller discipline; governing gates must have explicit contract-level traceability.
- **Why it exists:** Rebuild rationale identifies externally triggered critical gating as a continuity and safety risk under cross-session drift.
- **Source grounding:** directly grounded in `REBUILD_RATIONALE.md` (externalized cooldown/gating pressure) and governance-derived from `QD_END_TO_END_BUILD_PLAN_v0_3.md` (honest failure and anti-corruption duties).
- **What it forbids:** critical path reliance on undocumented external invocation assumptions.
- **What it still allows:** modular decomposition, as long as the contract explicitly names trigger authority, observability, and failure behavior.

### C3. No Semantic Shaping in Claimed Neutral Substrate
- **Statement:** Any layer claiming neutrality must not be silently pre-shaped by human semantic roles in its core substrate logic.
- **Why it exists:** Rebuild and governing artifacts identify semantic backflow into neutral lanes as a core drift/falsity risk.
- **Source grounding:** directly grounded in `REBUILD_RATIONALE.md` (semantic pre-shaping pressure) and `QD_END_TO_END_BUILD_PLAN_v0_3.md` (human semantics must not leak backward).
- **What it forbids:** presenting semantically pre-shaped transforms as neutral substrate detection.
- **What it still allows:** explicit bridge-layer semantics and observational scaffolding, if clearly labeled non-neutral and non-authoritative.

### C4. No Unavailable-Artifact Continuity Claims
- **Statement:** Continuity claims requiring missing artifacts must be held as bounded HOLD until source recovery or ratified replacement mapping is available.
- **Why it exists:** Ratified artifacts identify missing continuity sources as unresolved reconstruction limits.
- **Source grounding:** directly grounded in `EXPERIMENTAL_FOUNDATION.md` and `REBUILD_RATIONALE.md` (missing `constraint_bootstrap_v1*` bounded gap).
- **What it forbids:** asserting recovered lineage, causes, or constraints from memory when source artifacts are unavailable.
- **What it still allows:** bounded reconstruction statements, explicit uncertainty labels, and targeted source-recovery tasks.

### C5. No Local-Completeness-as-Constitutional-Proof
- **Statement:** Local technical completion cannot be treated as constitutional closure without explicit cross-session governance legibility and inheritance mapping.
- **Why it exists:** Rebuild rationale and governing plan identify local correctness without constitutional coherence as a repeat risk.
- **Source grounding:** governance-derived from `QD_END_TO_END_BUILD_PLAN_v0_3.md` (cold-session legibility, anti-drift requirements), reinforced by `REBUILD_RATIONALE.md` (local workflow strength was not sufficient for constitutional continuity).
- **What it forbids:** claiming constitutional advancement solely from local module quality, test pass status, or isolated artifact polish.
- **What it still allows:** local improvements and experiments, provided constitutional status remains explicitly unearned until governance conditions are met.

### C6. No Authoritative Advancement Without Constitutional Artifact Closure
- **Statement:** No major layer or posture may be treated as authoritative advancement until the required constitutional artifacts for that phase are closed and ratified.
- **Why it exists:** Governing plan requires explicit constitutional closure to prevent distributed contradiction and session drift.
- **Source grounding:** governance-derived from `QD_END_TO_END_BUILD_PLAN_v0_3.md` (Phase I closure test and advancement rule), reinforced by `BUILD_LEDGER.md` lock discipline.
- **What it forbids:** elevating exploratory/diagnostic outputs to canonical status before earning criteria are met.
- **What it still allows:** exploratory and diagnostic work as non-canonical inputs to pressure testing, reconstruction, and later ratification.

### C7. No Cold-Session Ambiguity in Governing State
- **Statement:** Governing state must be discoverable by a cold session without prior thread memory; entry points, current frontier, and immediate target must be explicit.
- **Why it exists:** Governing plan identifies cold-session ambiguity as a direct mechanism of contradiction debt.
- **Source grounding:** governance-derived from `QD_END_TO_END_BUILD_PLAN_v0_3.md` (manifest discoverability and entry-point requirements), reinforced by `BUILD_LEDGER.md` constitutional pre-read rule.
- **What it forbids:** governance changes that are only present in chat context, personal memory, or implicit assumptions.
- **What it still allows:** iterative drafting, provided ledger/governance surfaces are updated to preserve cold-session continuity.

## Relationship to Governing Artifacts

- `QD_END_TO_END_BUILD_PLAN_v0_3.md`: defines settled principles, anti-drift posture, and constitutional closure requirements that these constraints enforce.
- `EXPERIMENTAL_FOUNDATION.md`: provides ratified empirical inheritance and measurement-obligation grounding for constraints on truth claims, mode disclosure, and bounded HOLD.
- `REBUILD_RATIONALE.md`: provides ratified rebuild-pressure evidence and bounded reconstruction limits that these constraints convert into ongoing prohibitions and allowances.

## Non-Goals / Non-Claims

- This document does not claim the current build already satisfies all constraints.
- This document does not replace `ADVANCEMENT_RULES.md` or define layer-earning procedure details.
- This document does not outlaw exploratory/diagnostic work.
- This document does not assert new rebuild causes beyond ratified artifacts.
- This document does not settle open questions already marked open in governing artifacts.

## Pressure-Test Readiness

This artifact is pressure-test-ready when each constraint can be checked for:
1. explicit statement and enforceable boundary,
2. source-grounded justification (direct and/or governance-derived),
3. clear forbid/allow distinction,
4. compatibility with exploratory non-canonical work,
5. cold-session legibility without thread memory.
