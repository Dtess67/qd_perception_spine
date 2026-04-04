# QD Build Ledger

## Purpose
This is the single source of truth for:
- where we are
- what is locked
- what changed today
- what is next
- what is intentionally not being changed

---

## Project Identity
**Project name:** qd_perception_spine

**Primary repo/folder:** `X:/Dev/QD_Main/qd_perception_spine`

**Related repos/folders:**
- `X:/Dev/QD_Main/truth_engine_v1`
- `X:/Dev/QD_Main/QD_v3`
- GitHub repo list exists, but qd_perception_spine is not currently initialized as a Git repo

**Current branch:** N/A — not a Git repo yet in this folder

**Last known good commit:** N/A in this folder

**Working rule:** Truth above comfort. False certainty is worse than hold.

---

## Current Build State
### Current layer / frontier
Unified System Consumer Consistency / Stage Lock v1.1

### Last completed layer
Unified System Consumer Consistency / Stage Lock v1.1 (read-only audit layer over unified posture)

### Current recommended next layer
Unified System Consumer Gate v1.2

### Why this next layer exists
The top umbrella consumer posture is now covered by a stage-lock audit. The next honest step is a read-only consumer gate that composes unified posture + unified stage lock into a stable consumer stance without reopening lower-band semantics.

---

## Locked Contracts
### Locked lower infrastructure
- Observability band locked:
  - Cross-Event Capture Quality Summary v1.4
  - Bounded Time-Slice Capture Quality Summary v1.5
  - Event-Order Bounded Capture Quality Summary v1.6
  - Window Comparator Summary v1.7
  - Observability Consistency / Stage Lock v1.8
- Cross-band band locked:
  - Cross-Band Self-Check Audit v1.0a
  - Bounded Multi-Event Cross-Band Consistency Sampler v1.1
  - Cross-Band Self-Check Event-Order Window v1.2
  - Cross-Band Window Comparator v1.3
  - Cross-Band Consistency / Stage Lock v1.4
- Top-level lock stack present:
  - Umbrella Lock Integration v1.0
  - System Lock Consumer Gate v1.1
- Evidence review stack present and corrected:
  - Cross-Band Evidence Review Summary v1.0
  - System-Wide Evidence Review v1.1
  - System Evidence Review Consistency / Stage Lock v1.2
  - System Evidence Review Consumer Gate v1.3
  - System Evidence Consumer Summary v1.4
- Unified umbrella consumer stack present:
  - Unified System Consumer Posture Summary v1.0
  - Unified System Consumer Consistency / Stage Lock v1.1

### Preserved posture
- neutral lane only
- no hidden semantics
- no overclaiming
- no rewrite of history
- no current-state inference for missing historical evidence
- prefer composition over rewriting
- false certainty is worse than hold
- no fake symmetry between cross-band review and observability
- no pressure-capture-quality influence on top-level evidence posture
- no system-gate-state influence on top-level evidence posture
- no observability-stage-lock substitution for observability evidence review

### Things we are explicitly NOT changing
- lower-band bucket meanings
- lower-band window semantics
- comparator delta directions
- corrected READY/PARTIAL/UNAVAILABLE evidence-review contract
- lineage history rules
- read-only guardrail posture

---

## Latest Verified Facts
### What is actually present in code
- All upper-stack APIs are currently being implemented in `src/qd_perception/neutral_family_memory_v1.py`
- System-Wide Evidence Review v1.1 uses corrected READY logic requiring:
  - cross-band evidence review available and READY
  - cross-band auditable evidence > 0
  - real observability evidence review available and READY
- Unified System Consumer Posture Summary v1.0 was added as a pure wrapper above:
  - `get_system_evidence_consumer_summary()`
  - `get_system_lock_gate_posture()`
- Unified System Consumer Consistency / Stage Lock v1.1 is present as a read-only audit over:
  - `get_unified_system_consumer_posture_summary()`
  - canonical posture state contract + read-only guardrail consistency checks

### What is inferred but not yet verified
- Whether qd_perception_spine should ultimately live inside an existing GitHub repo or become its own Git repo
- Whether truth_engine_v1 will later absorb any of this posture/gating architecture

### What is still unknown / HOLD
- Git destination strategy for qd_perception_spine
- Whether `runs/` artifacts should be versioned or ignored
- Whether `BUILD_LEDGER.md` should live only locally first or be committed immediately after git init

---

## Today’s Work Log
**Date:** 2026-04-04

### What we built
- Unified System Consumer Consistency / Stage Lock v1.1 was validated and finalized as the active frontier
- Focused stage-lock drift tests were added for canonical-state checks, fail-closed shape checks, guardrail checks, missing/unusable surface handling, and no hidden lower-band dependency checks

### Files changed
- `tests/test_unified_system_consumer_posture_stage_lock.py`
- `runs/unified_system_consumer_stage_lock_v1_1_transcript.txt`
- `runs/unified_system_consumer_stage_lock_v1_1_delivery.txt`
- `BUILD_LEDGER.md`

### Tests run
- Focused tests:
  - `tests/test_unified_system_consumer_posture_stage_lock.py`
  - `tests/test_unified_system_consumer_posture_summary.py`
- Full pytest suite

### Result counts
- Focused tests: 13 passed, 1 warning
- Full suite: 300 passed, 1 warning
- Warnings:
  - pytest cache permission warning
  - temp symlink cleanup PermissionError warning (non-blocking)

### Run artifacts / notes
- Delivery/transcript artifacts were written under `runs/`
- qd_perception_spine is currently not a Git repo in this folder

---

## Current APIs / Surfaces Added
- `get_cross_band_evidence_review_summary()`
- `get_system_evidence_review_summary()`
- `get_system_evidence_review_stage_lock_audit()`
- `get_system_evidence_review_consumer_gate()`
- `get_system_evidence_consumer_summary()`
- `get_system_lock_gate_posture()`
- `get_unified_system_consumer_posture_summary()`
- `get_unified_system_consumer_posture_stage_lock_audit()`

---

## Next Step
### Immediate next step
Unified System Consumer Gate v1.2

### Why this is the next honest step
The unified posture now has freeze/audit coverage. A minimal consumer gate is the next composition layer to expose a stable rely/limited/hold style posture for downstream consumers based only on unified summary and unified stage-lock results.

### What it must use
- `get_unified_system_consumer_posture_summary()`
- `get_unified_system_consumer_posture_stage_lock_audit()`

### What it must NOT do
- reopen lower-band semantics
- invent new truth predicates
- call lower-band evidence/observability APIs as hidden dependencies for posture resolution
- mutate lineage, create events, or rewrite history

---

## Git Checkpoint
### Commit status
- Repo initialized: NO
- Changes committed: NO
- Changes pushed: NO

### Commit to make next
**Suggested commit message:** Add unified consumer stage-lock v1.1 focused tests and ledger checkpoint

### Files that should be committed
- `src/`
- `tests/`
- `README.md`
- `BUILD_LEDGER.md`
- selected stable run artifacts only if they are intentionally part of delivery history

### Files that should probably stay out of Git
- `runs/` (unless curated intentionally)
- temp outputs
- machine-specific junk
- `.pytest_cache/`

---

## Restart Prompt
Use this to start the next thread:

"Resume qd_perception_spine from the Build Ledger. Read Project Identity, Current Build State, Locked Contracts, Today’s Work Log, and Next Step first. Do not reopen locked lower semantics unless the ledger explicitly says to do so."

---

## End-of-Day Snapshot
### Built today
- Validated and finalized Unified System Consumer Consistency / Stage Lock v1.1
- Added focused stage-lock drift and guardrail tests
- Verified full suite on the updated frontier

### Verified today
- unified posture stage-lock audit surface is present in `neutral_family_memory_v1.py`
- final full suite reported green at 300 passed, 1 warning
- current qd_perception_spine folder is not initialized as a Git repo

### Open questions
- Should qd_perception_spine become its own Git repo?
- What run artifacts belong in version control?
- How should truth_engine_v1 relate to this repo, if at all?

### First action next session
- Initialize Git or identify intended parent repo
- decide whether `runs/` stays unversioned after Git init
- build Unified System Consumer Gate v1.2

### Pressure items / risks
- continuity drift if ledger is not kept current
- repo drift if Git is not initialized soon
- artifact clutter if `runs/` is committed indiscriminately

---

## Successes & Failures
### Successes
- kept the stack read-only and composition-first
- avoided fake symmetry and hidden READY predicates
- added a top umbrella consumer posture without contaminating lower truth surfaces

### Technical Failures
- qd_perception_spine is not currently a Git repo
- continuity has depended too much on chat/thread memory instead of file-based state

### Conceptual Failures
- inconsistent use of a persistent ledger/process anchor across sessions
- project identity drift between truth_engine_v1, qd_perception_spine, and broader Truth Engine ideas
