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
- GitHub repo list exists; qd_perception_spine is now initialized as a local Git repo

**Current branch:** `main`

**Last known good commit:** `89c77e3ee7d03e030b2e788ef33ab3408f18a319`

**Working rule:** Truth above comfort. False certainty is worse than hold.

---

## Current Build State
### Current layer / frontier
Observability Evidence Review Summary Windowed v1.1

### Last completed layer
Observability Evidence Review Summary Windowed v1.1 implemented and verified

### Current recommended next layer
Bounded System Evidence Review Sampler v1.0

### Why this next layer exists
Both bounded evidence-review sides now exist (cross-band and observability, each for index and event-order windows). The next honest substantive step is bounded system-level sampling over those bounded review surfaces without implying full-range equivalence.

### Current frozen and verified top surfaces
- current frozen posture surface: `get_unified_system_consumer_posture_summary()`
- current verified top audit surface: `get_unified_system_consumer_posture_stage_lock_audit()`
- audit relationship: `get_unified_system_consumer_posture_stage_lock_audit()` freezes/audits `get_unified_system_consumer_posture_summary()`
- current top delivery surface: `get_unified_system_consumer_summary()`
- current observability evidence-review surface: `get_observability_evidence_review_summary()`
- current observability evidence-review audit surface: `get_observability_evidence_review_stage_lock_audit()`
- current cross-band bounded evidence-review surfaces:
  - `get_cross_band_evidence_review_summary_window(...)`
  - `get_cross_band_evidence_review_summary_event_order_window(...)`
- current observability bounded evidence-review surfaces:
  - `get_observability_evidence_review_summary_window(...)`
  - `get_observability_evidence_review_summary_event_order_window(...)`

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
  - Observability Evidence Review Summary v1.0
  - Observability Evidence Review Consistency / Stage Lock v1.1
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
- `get_unified_system_consumer_posture_stage_lock_audit()` is present in `src/qd_perception/neutral_family_memory_v1.py`
- `get_unified_system_consumer_posture_stage_lock_audit()` is the current verified top audit surface, freezing/auditing `get_unified_system_consumer_posture_summary()`
- `get_unified_system_consumer_summary()` is present in `src/qd_perception/neutral_family_memory_v1.py` as a pure read-only packaging layer above:
  - `get_unified_system_consumer_posture_summary()`
  - `get_unified_system_consumer_posture_stage_lock_audit()`
- `get_observability_evidence_review_summary()` is present in `src/qd_perception/neutral_family_memory_v1.py` as a read-only observability evidence-review surface composed only from:
  - `get_pressure_capture_quality_summary()`
  - `get_observability_stage_lock_audit()`
- Minimal demo invocation returned:
  - `audit_available = true`
  - `audit_mode = UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK`
  - `lock_state = UNIFIED_SYSTEM_CONSUMER_STAGE_LOCKED`
  - `reason = ALL_CONSISTENCY_CHECKS_PASSED`
- Focused unified stage-lock tests now exist in:
  - `tests/test_unified_system_consumer_posture_stage_lock.py`
- Focused unified consumer summary tests now exist in:
  - `tests/test_unified_system_consumer_summary.py`
- Focused observability evidence review tests now exist in:
  - `tests/test_observability_evidence_review.py`
- `get_observability_evidence_review_stage_lock_audit()` is present in `src/qd_perception/neutral_family_memory_v1.py` as a read-only audit over:
  - `get_observability_evidence_review_summary()`
  - `get_pressure_capture_quality_summary()`
  - `get_observability_stage_lock_audit()`
- Focused observability evidence-review stage-lock tests now exist in:
  - `tests/test_observability_evidence_review_stage_lock.py`
- System-wide evidence review v1.1 behavior was revalidated with the real `get_observability_evidence_review_summary()` surface active:
  - READY/PARTIAL/UNAVAILABLE contract remained unchanged
  - no implementation/test correction was required
- `get_cross_band_evidence_review_summary_window(...)` and `get_cross_band_evidence_review_summary_event_order_window(...)` are present in `src/qd_perception/neutral_family_memory_v1.py` as bounded read-only review mappings over:
  - `get_cross_band_self_check_summary_window(...)`
  - `get_cross_band_self_check_summary_event_order_window(...)`
  - `get_cross_band_self_check_window_comparator(...)` as supporting context only
- Focused bounded cross-band evidence-review tests now exist in:
  - `tests/test_cross_band_evidence_review_windowed.py`
- `get_observability_evidence_review_summary_window(...)` and `get_observability_evidence_review_summary_event_order_window(...)` are present in `src/qd_perception/neutral_family_memory_v1.py` as bounded read-only review mappings over:
  - `get_pressure_capture_quality_summary_window(...)`
  - `get_pressure_capture_quality_summary_event_order_window(...)`
  - `get_pressure_capture_quality_window_comparator(...)` as supporting context only
- Focused bounded observability evidence-review tests now exist in:
  - `tests/test_observability_evidence_review_windowed.py`
- Latest verified full-suite baseline:
  - `338 passed, 1 warning`

### What is inferred but not yet verified
- Whether qd_perception_spine should ultimately live inside an existing GitHub repo or become its own Git repo
- Whether truth_engine_v1 will later absorb any of this posture/gating architecture

### What is still unknown / HOLD
- Git destination strategy for qd_perception_spine
- Whether `runs/` artifacts should be versioned or ignored
- Whether `BUILD_LEDGER.md` should live only locally first or be committed immediately after git init

---

## Today’s Work Log
### Session date: 2026-04-05 (Observability Evidence Review Summary Windowed v1.1)
#### What we built
- implemented bounded observability evidence-review mapping surfaces:
  - `get_observability_evidence_review_summary_window(...)`
  - `get_observability_evidence_review_summary_event_order_window(...)`
- composition constrained to allowed bounded observability surfaces:
  - `get_pressure_capture_quality_summary_window(...)`
  - `get_pressure_capture_quality_summary_event_order_window(...)`
  - `get_pressure_capture_quality_window_comparator(...)` as supporting context only
- explicit bounded scope non-equivalence retained in output contract; comparator context kept non-predicate

#### Files changed
- `src/qd_perception/neutral_family_memory_v1.py`
- `tests/test_observability_evidence_review_windowed.py`
- `BUILD_LEDGER.md`
- `runs/observability_evidence_review_summary_windowed_v1_1_transcript.txt`
- `runs/observability_evidence_review_summary_windowed_v1_1_delivery.txt`

#### Tests run
- focused bounded observability review tests with `PYTHONPATH=src`: `11 passed, 1 warning`
- adjacent observability/window tests with `PYTHONPATH=src`: `26 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `338 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-04 (End-of-day closeout)
#### What we finalized
- built/validated Observability Evidence Review Consistency / Stage Lock v1.1
- revalidated System-Wide Evidence Review v1.1a; no code correction required
- validated and then committed Cross-Band Evidence Review Summary Windowed v1.1
- important truth note: bounded cross-band source diff in `src/qd_perception/neutral_family_memory_v1.py` was explicitly inspected, confirmed required for public bounded APIs, and then committed

#### Key commits (today)
- `67576de4d400520aeacb3b31834d05c98e0fe972` - Add observability evidence review stage lock v1.1
- `ec6c62711430e015e64280be40eb7e5376a6e520` - Record system-wide evidence review v1.1a revalidation
- `f639d2ef56736952e17dcdf17f9b8274b9df676e` - Add validation for cross-band evidence review windowed v1.1
- `89c77e3ee7d03e030b2e788ef33ab3408f18a319` - Add cross-band evidence review windowed v1.1

#### Key test baselines
- `316 passed, 1 warning` after observability evidence-review stage lock work
- `327 passed, 1 warning` after bounded cross-band review validation/commit

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-04 (Cross-Band Evidence Review Summary Windowed v1.1)
#### What we built
- validated and completed bounded cross-band evidence-review mapping surfaces:
  - `get_cross_band_evidence_review_summary_window(...)`
  - `get_cross_band_evidence_review_summary_event_order_window(...)`
- important truth note: these two API blocks were already present in `neutral_family_memory_v1.py` before this session; work in this session was focused contract verification, focused tests, and ledger/run-artifact updates

#### Files changed
- `tests/test_cross_band_evidence_review_windowed.py`
- `BUILD_LEDGER.md`
- `runs/cross_band_evidence_review_summary_windowed_v1_1_transcript.txt`
- `runs/cross_band_evidence_review_summary_windowed_v1_1_delivery.txt`

#### Tests run
- focused bounded review tests with `PYTHONPATH=src`: `11 passed, 1 warning`
- adjacent cross-band tests with `PYTHONPATH=src`: `34 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `327 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-04
#### What we built
- verified/finished Unified System Consumer Consistency / Stage Lock v1.1
- important truth note: `get_unified_system_consumer_posture_stage_lock_audit()` was already present in source before this session; work performed this session was focused drift/guardrail test coverage plus validation, not invention of a brand-new decision layer

#### Files changed
- `tests/test_unified_system_consumer_posture_stage_lock.py`
- `BUILD_LEDGER.md`
- `runs/unified_system_consumer_stage_lock_v1_1_transcript.txt`
- `runs/unified_system_consumer_stage_lock_v1_1_delivery.txt`

#### Tests run
- initial focused run failed due to missing `PYTHONPATH=src`
- corrected focused run: `13 passed, 1 warning`
- corrected full suite: `300 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-04 (Unified Summary / Delivery v1.2)
#### What we built
- implemented `get_unified_system_consumer_summary()` as a pure read-only packaging/delivery layer
- composition constrained to:
  - `get_unified_system_consumer_posture_summary()`
  - `get_unified_system_consumer_posture_stage_lock_audit()`
- no new truth predicates added; summary state/reason package unified posture state/reason directly

#### Files changed
- `src/qd_perception/neutral_family_memory_v1.py`
- `tests/test_unified_system_consumer_summary.py`
- `BUILD_LEDGER.md`
- `runs/unified_system_consumer_summary_v1_2_transcript.txt`
- `runs/unified_system_consumer_summary_v1_2_delivery.txt`

#### Tests run
- focused unified-stack tests with `PYTHONPATH=src`: `18 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `305 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-04 (Observability Evidence Review Summary v1.0)
#### What we built
- implemented `get_observability_evidence_review_summary()` as the missing observability-side read-only evidence-review surface
- composition constrained to:
  - `get_pressure_capture_quality_summary()`
  - `get_observability_stage_lock_audit()`
- no direct lower observability internal calls were added in this new review surface

#### Files changed
- `src/qd_perception/neutral_family_memory_v1.py`
- `tests/test_observability_evidence_review.py`
- `tests/test_system_evidence_review.py`
- `BUILD_LEDGER.md`
- `runs/observability_evidence_review_summary_v1_0_transcript.txt`
- `runs/observability_evidence_review_summary_v1_0_delivery.txt`

#### Tests run
- focused tests with `PYTHONPATH=src`: `14 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `310 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-04 (System-Wide Evidence Review Revalidation v1.1a)
#### What we built
- performed inspection/revalidation of `get_system_evidence_review_summary()` against the now-real observability evidence-review surface
- verified adjacent stage-lock/gate/consumer-summary surfaces remain contract-consistent
- no code or test correction was required for v1.1a

#### Files changed
- `BUILD_LEDGER.md`
- `runs/system_wide_evidence_review_revalidation_v1_1a_transcript.txt`
- `runs/system_wide_evidence_review_revalidation_v1_1a_delivery.txt`

#### Tests run
- focused revalidation tests with `PYTHONPATH=src`: `28 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `310 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-04 (Observability Evidence Review Consistency / Stage Lock v1.1)
#### What we built
- implemented `get_observability_evidence_review_stage_lock_audit()` as a read-only contract freeze/audit over allowed observability evidence-review source surfaces
- audit checks include:
  - allowed-source state/reason mapping consistency
  - quality-count composition honesty
  - no hidden cross-band/system-gate context
  - read-only guardrail flags

#### Files changed
- `src/qd_perception/neutral_family_memory_v1.py`
- `tests/test_observability_evidence_review_stage_lock.py`
- `BUILD_LEDGER.md`
- `runs/observability_evidence_review_stage_lock_v1_1_transcript.txt`
- `runs/observability_evidence_review_stage_lock_v1_1_delivery.txt`

#### Tests run
- focused tests with `PYTHONPATH=src`: `25 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `316 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

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
- `get_unified_system_consumer_summary()`
- `get_observability_evidence_review_summary()`
- `get_observability_evidence_review_stage_lock_audit()`
- `get_cross_band_evidence_review_summary_window(...)`
- `get_cross_band_evidence_review_summary_event_order_window(...)`
- `get_observability_evidence_review_summary_window(...)`
- `get_observability_evidence_review_summary_event_order_window(...)`

---

## Next Step
### Immediate next step
Bounded System Evidence Review Sampler v1.0

### Why this is the next honest step
Bounded cross-band and bounded observability evidence-review mappings now both exist, so bounded system-level composition can be added without mixing bounded inputs with missing bounded anchors.

### What it must use
- `get_cross_band_evidence_review_summary_window(...)`
- `get_cross_band_evidence_review_summary_event_order_window(...)`
- `get_observability_evidence_review_summary_window(...)`
- `get_observability_evidence_review_summary_event_order_window(...)`
- bounded comparator context only through supporting surfaces (no hidden predicate promotion)

### What it must NOT do
- invent new truth predicates
- reopen lower evidence or observability semantics
- add hidden direct lower-band dependencies outside established composition surfaces
- no lower-band bucket meaning changes
- no window semantic changes
- no comparator delta-direction reinterpretation
- no hidden cross-band/system-gate predicates
- imply bounded outputs are full-range equivalent
- mutate lineage, create events, or rewrite history

---

## Git Checkpoint
### Commit status
- Repo initialized: YES
- Changes committed: YES (latest committed baseline at `89c77e3ee7d03e030b2e788ef33ab3408f18a319`)
- Changes pushed: YES (to `origin/main`)
- Repo clean: NO (current session changes pending commit)
- Branch: `main`
- Upstream: `origin/main`
- Synced with upstream: YES at last commit; working tree currently dirty with local uncommitted changes

### Latest relevant commits (today)
- `89c77e3ee7d03e030b2e788ef33ab3408f18a319` - Add cross-band evidence review windowed v1.1
- `f639d2ef56736952e17dcdf17f9b8274b9df676e` - Add validation for cross-band evidence review windowed v1.1
- `67576de4d400520aeacb3b31834d05c98e0fe972` - Add observability evidence review stage lock v1.1
- `ec6c62711430e015e64280be40eb7e5376a6e520` - Record system-wide evidence review v1.1a revalidation

### Commit to make next
**Suggested commit message:** Add observability evidence review summary windowed v1.1

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

### Current likely untracked files (expected)
- `.junie/`
- `cross_band_stage_lock_v1.4_summary.txt`
- `system_stage_lock_v1.0_report_for_q.txt`

---

## Restart Prompt
Resume qd_perception_spine from BUILD_LEDGER.md.

Read these sections first:
1. Current Build State
2. Locked Contracts
3. Latest Verified Facts
4. Today’s Work Log
5. Next Step

Current verified suite count:
- Full suite: 338 passed, 1 warning

Current frozen top surface:
- get_unified_system_consumer_posture_summary()

Current verified top audit surface:
- get_unified_system_consumer_posture_stage_lock_audit()

Current top delivery surface:
- get_unified_system_consumer_summary()

Current observability evidence-review surface:
- get_observability_evidence_review_summary()

Current observability evidence-review audit surface:
- get_observability_evidence_review_stage_lock_audit()

Immediate next target:
- Bounded System Evidence Review Sampler v1.0

Do not reopen locked lower semantics.
Do not invent new predicates.
Do not add hidden lower-band calls.
Preserve read-only guardrails and fail closed when evidence is insufficient.

---

## End-of-Day Snapshot
### Built today
- Implemented Observability Evidence Review Summary Windowed v1.1 (index + event-order)
- Added focused bounded observability evidence-review tests
- Verified full suite on updated bounded observability frontier
- Validated and finalized Unified System Consumer Consistency / Stage Lock v1.1
- Added focused stage-lock drift and guardrail tests
- Implemented Unified System Consumer Summary / Delivery v1.2
- Added focused unified consumer summary tests
- Implemented Observability Evidence Review Summary v1.0
- Added focused observability evidence review tests
- Revalidated System-Wide Evidence Review v1.1 (v1.1a) with no contract correction required
- Implemented Observability Evidence Review Consistency / Stage Lock v1.1
- Validated and completed Cross-Band Evidence Review Summary Windowed v1.1
- Committed required bounded cross-band source diff after explicit necessity audit
- Verified full suite on the updated frontier

### Verified today
- unified posture stage-lock audit surface is present in `neutral_family_memory_v1.py`
- unified summary delivery surface is present in `neutral_family_memory_v1.py`
- observability evidence-review surface is present in `neutral_family_memory_v1.py`
- observability evidence-review stage-lock surface is present in `neutral_family_memory_v1.py`
- bounded cross-band evidence-review windowed surfaces are present in `neutral_family_memory_v1.py`
- bounded observability evidence-review windowed surfaces are present in `neutral_family_memory_v1.py`
- final full suite reported green at 338 passed, 1 warning
- focused system-evidence revalidation suite reported green at 28 passed, 1 warning
- top unified posture stage lock present and validated
- repo initialized and first local checkpoint commit created

### Open questions
- Should qd_perception_spine become its own Git repo?
- What run artifacts belong in version control?
- How should truth_engine_v1 relate to this repo, if at all?

### First action next session
- read BUILD_LEDGER.md first
- inspect/build Bounded System Evidence Review Sampler v1.0
- update ledger again before stopping

### Pressure items / risks
- continuity drift if ledger is not kept current
- repo drift if Git is not initialized soon
- artifact clutter if `runs/` is committed indiscriminately
- avoid accidental bounded-to-full-range equivalence claims in any new bounded system sampler output

---

## Successes & Failures
### Successes
- kept the stack read-only and composition-first
- avoided fake symmetry and hidden READY predicates
- added a top umbrella consumer posture without contaminating lower truth surfaces

### Technical Failures
- continuity previously depended too much on chat/thread memory before ledger adoption
- first focused test run failed because `PYTHONPATH=src` was not set

### Conceptual Failures
- inconsistent use of a persistent ledger/process anchor across sessions
- project identity drift between truth_engine_v1, qd_perception_spine, and broader Truth Engine ideas
