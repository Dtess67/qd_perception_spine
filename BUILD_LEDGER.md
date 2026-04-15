# QD Build Ledger

Canonical governance documents live in /governance/. Start with governance/QD_END_TO_END_BUILD_PLAN_v0_3.md before advancing the build.
Any session that intends to advance the build must read the governing document and applicable constitutional artifacts in /governance/ before proposing or making architecture changes.

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
Phase I — Constitutional Lock (governing v0.3 in effect)

### Last completed layer
EXPERIMENTAL_FOUNDATION.md v1.1 drafted, tightened, pressure-tested, and ratified

### Current recommended next layer
Phase I continuation — select and draft the next constitutional artifact (recommended: REBUILD_RATIONALE.md)

### Why this next layer exists
The empirical inheritance bridge is now ratified. The next honest move is to continue Phase I by closing another constitutional artifact, with REBUILD_RATIONALE.md recommended because EXPERIMENTAL_FOUNDATION.md explicitly identifies unresolved QD_v3 inheritance gaps.

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
- current bounded system evidence-review sampler surfaces:
  - `get_system_evidence_review_sampler_window(...)`
  - `get_system_evidence_review_sampler_event_order_window(...)`
- current bounded system evidence-review stage-lock surfaces:
  - `get_system_evidence_review_sampler_stage_lock_window(...)`
  - `get_system_evidence_review_sampler_stage_lock_event_order_window(...)`
- current bounded system evidence-review consumer gate surfaces:
  - `get_system_evidence_review_sampler_consumer_gate_window(...)`
  - `get_system_evidence_review_sampler_consumer_gate_event_order_window(...)`
- current durable-ledger root-truth audit surface:
  - `get_durable_transition_ledger_integrity_audit()`
- current corrective-learning contract surfaces:
  - `CorrectiveLearningRecordV1a`
  - `get_corrective_learning_record_contract_v1a()`
  - `validate_corrective_learning_record_v1a(...)`
  - `build_corrective_learning_record_v1a(...)`
  - `format_corrective_learning_record_v1a(...)`
  - `map_durable_ledger_audit_findings_to_corrective_records_v1_2(...)`
- current isolated decision-loop prototype surface:
  - `resolve_manual_decision_trace_v0_0(...)`

### Design-anchor frontier (spec-only)
- `QD Decision Loop v0.1` anchored in `QD_DECISION_LOOP_v0_1.md`
- `QD Decision Loop v0.2 - Resolution Criteria Draft` anchored in `QD_DECISION_LOOP_v0_2.md`
- `QD Decision Loop v0.3 - Branch Weighting / Collapse Heuristics Draft` anchored in `QD_DECISION_LOOP_v0_3.md`
- `QD Decision Loop v0.4 - Worked Decision Traces` anchored in `QD_DECISION_LOOP_v0_4.md`
- `QD Decision Loop v0.4a - Ambiguity Closure Notes` anchored in `QD_DECISION_LOOP_v0_4a.md`
- `QD Decision Loop Prototype v0.0 - Manual Trace Resolver Plan` anchored in `QD_DECISION_LOOP_PROTOTYPE_v0_0_PLAN.md`
- one-line definition:
  - `Question -> Delta Split -> Polarity Evaluation -> Temporal Assessment -> Resolution`
- clarified geometry interpretation:
  - internal HOLD is a zone, not a node
  - external HOLD is a node, not a zone
  - contact plane is the active synthesis region
  - resolution collapses earned tension, not mere uncertainty
- v0.2 draft additions:
  - explicit collapse-vs-block resolution criteria
  - explicit output-class criteria (`-1`, `+1`, conditional, limited/caution, external HOLD)
  - explicit Delta Ingress criteria and weak/missing prior-state handling
  - explicit temporal evidence asymmetry notes (grounded recall > softer projection)
- v0.3 draft additions:
  - explicit branch-strength input classes for `-1` and `+1`
  - explicit weighting effects for substrate degradation and corrective relevance
  - explicit collapse heuristics draft for resolved/conditional/limited/external HOLD outputs
- v0.4 draft additions:
  - canonical declarative worked traces for collapse/block outcomes
  - explicit per-trace contributions (past/projection/substrate/corrective/contradiction context)
  - ambiguity notes exposed by worked traces
- v0.4a closure additions:
  - explicit boundary rules for conditional answer vs limited/caution answer
  - explicit projection support vs projection-upgrade constraints
  - explicit qualitative substrate bands (`usable`, `degraded`, `collapse-blocking`)
  - explicit qualitative corrective-learning suppression bands (`advisory`, `caution-inducing`, `collapse-blocking`)
- scope posture:
  - specification only in this step
  - no runtime behavior
  - no autonomous decision logic
  - no coupling into existing evidence/consumer surfaces

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
- `get_system_evidence_review_sampler_window(...)` and `get_system_evidence_review_sampler_event_order_window(...)` are present in `src/qd_perception/neutral_family_memory_v1.py` as bounded read-only system composition over:
  - `get_cross_band_evidence_review_summary_window(...)`
  - `get_cross_band_evidence_review_summary_event_order_window(...)`
  - `get_observability_evidence_review_summary_window(...)`
  - `get_observability_evidence_review_summary_event_order_window(...)`
- Focused bounded system evidence-review sampler tests now exist in:
  - `tests/test_system_evidence_review_sampler_windowed.py`
- `get_system_evidence_review_sampler_stage_lock_window(...)` and `get_system_evidence_review_sampler_stage_lock_event_order_window(...)` are present in `src/qd_perception/neutral_family_memory_v1.py` as read-only bounded sampler contract audits over:
  - `get_system_evidence_review_sampler_window(...)`
  - `get_system_evidence_review_sampler_event_order_window(...)`
  - matching bounded review anchors only
- Focused bounded system sampler stage-lock tests now exist in:
  - `tests/test_system_evidence_review_sampler_stage_lock.py`
- `get_system_evidence_review_sampler_consumer_gate_window(...)` and `get_system_evidence_review_sampler_consumer_gate_event_order_window(...)` are present in `src/qd_perception/neutral_family_memory_v1.py` as read-only bounded consumer reliance gates composed only from:
  - `get_system_evidence_review_sampler_window(...)`
  - `get_system_evidence_review_sampler_event_order_window(...)`
  - `get_system_evidence_review_sampler_stage_lock_window(...)`
  - `get_system_evidence_review_sampler_stage_lock_event_order_window(...)`
- Focused bounded system sampler consumer-gate tests now exist in:
  - `tests/test_system_evidence_review_sampler_consumer_gate.py`
- Cross-window consumer-gate parity tests now exist in:
  - `test_cross_window_equivalence_ready_locked_yields_rely`
  - `test_cross_window_equivalence_partial_locked_yields_limited`
  - `test_cross_window_equivalence_inconsistent_stage_lock_yields_hold`
- Truth note:
  - production inspection found no real bounded consumer-gate bug; both modes already share one helper and decision branches
  - parity hardening closed the observed cross-window test gap, so no new runtime API layer was earned in this session
- `get_durable_transition_ledger_integrity_audit()` is present in `src/qd_perception/neutral_family_memory_v1.py` as a read-only root-truth durable ledger audit over:
  - `get_event_ledger()`
  - `_get_ledger_event_by_id(...)`
  - `run_lineage_integrity_audit(...)`
  - `get_lineage_integrity_report(...)`
- Focused durable-ledger integrity audit tests now exist in:
  - `tests/test_durable_transition_ledger_integrity_audit.py`
- Corrective Learning v1.0a contract/schema surfaces are present in `src/qd_perception/neutral_family_memory_v1.py`:
  - `CorrectiveLearningRecordV1a`
  - `get_corrective_learning_record_contract_v1a()`
  - `validate_corrective_learning_record_v1a(...)`
- Corrective Learning v1.1 usage-path surfaces are present in `src/qd_perception/neutral_family_memory_v1.py`:
  - `build_corrective_learning_record_v1a(...)`
  - `format_corrective_learning_record_v1a(...)`
- Corrective Learning v1.2 mapping surface is present in `src/qd_perception/neutral_family_memory_v1.py`:
  - `map_durable_ledger_audit_findings_to_corrective_records_v1_2(...)`
  - mapping scope currently explicit to `get_durable_transition_ledger_integrity_audit()` findings only
- Focused corrective-learning contract tests now exist in:
  - `tests/test_corrective_learning_contract_v1a.py`
- Focused corrective-learning builder/formatter tests now exist in:
  - `tests/test_corrective_learning_builder_formatter_v1_1.py`
- Focused corrective-learning audit-mapping tests now exist in:
  - `tests/test_corrective_learning_audit_mapping_v1_2.py`
- Design anchor spec now exists at repo root:
  - `QD_DECISION_LOOP_v0_1.md`
  - `QD_DECISION_LOOP_v0_2.md`
  - `QD_DECISION_LOOP_v0_3.md`
  - `QD_DECISION_LOOP_v0_4.md`
  - `QD_DECISION_LOOP_v0_4a.md`
  - `QD_DECISION_LOOP_PROTOTYPE_v0_0_PLAN.md`
- Decision-loop prototype runtime surface now exists in:
  - `src/qd_perception/decision_loop_prototype_v0_0.py`
  - `resolve_manual_decision_trace_v0_0(...)`
  - `ManualTraceInputV0`
- Focused decision-loop prototype tests now exist in:
  - `tests/test_decision_loop_prototype_v0_0.py`
- Prototype v0.0a pressure-test corrections now applied:
  - degraded substrate no longer blocks all resolved collapse paths when grounded dominance remains strong
  - non-blocking recall/projection contradiction is routed to `limited_caution_answer` instead of premature `external_hold`
- Latest verified full-suite baseline:
  - `404 passed, 1 warning`

### What is inferred but not yet verified
- Whether qd_perception_spine should ultimately live inside an existing GitHub repo or become its own Git repo
- Whether truth_engine_v1 will later absorb any of this posture/gating architecture

### What is still unknown / HOLD
- Git destination strategy for qd_perception_spine
- Whether `runs/` artifacts should be versioned or ignored
- Whether `BUILD_LEDGER.md` should live only locally first or be committed immediately after git init

---

## Today’s Work Log
### Session date: 2026-04-15 (Phase I Empirical Bridge — EXPERIMENTAL_FOUNDATION v1.1 Ratified)
#### What we built
- drafted governance/EXPERIMENTAL_FOUNDATION.md as the Phase I empirical inheritance bridge
- completed v1.1 tightening pass
- added explicit source-resolution notes
- added metric inheritance crosswalk
- operationalized HOLD / bounded recovery language
- checked Non-Obligations consistency against derived obligations
- document was pressure-tested and ratified for commit by Claude
- next governance target remains open for Phase I follow-up

### Session date: 2026-04-15 (Phase I Governance Opening — Governing v0.3 Alignment)
#### What we built
- governance directory and governing build file created
- constitutional stub files created
- BUILD_LEDGER.md updated with governance entry point and constitutional pre-read rule
- BUILD_LEDGER.md aligned to governing v0.3 posture
- next target is governance/EXPERIMENTAL_FOUNDATION.md

### Session date: 2026-04-06 (Decision Loop Prototype v0.0a - Edge-Case Pressure Tests)
#### What we built
- added focused edge-case tests for prototype chamber behavior:
  - tie-ish branch pulls under usable substrate/low contradiction
  - usable substrate with caution-inducing suppression
  - degraded substrate with strong grounded recall
  - projection-strong case with missing prior state
  - contradictory recall/projection under non-blocking substrate
  - named-conditions present vs absent for conditional-trend case
  - precedence ordering for collapse-blocking substrate/suppression
  - underspecified input fail-closed behavior
- two real spec-consistency mismatches were exposed and corrected minimally in resolver logic:
  - degraded substrate now applies strictness without universally forbidding resolved output when grounded dominance remains strong
  - non-blocking recall/projection conflict now resolves to `limited_caution_answer` (not default `external_hold`)
- scope remained isolated:
  - no persistence
  - no autonomous learning
  - no coupling into existing evidence/consumer runtime surfaces

#### Files changed
- `src/qd_perception/decision_loop_prototype_v0_0.py`
- `tests/test_decision_loop_prototype_v0_0.py`
- `BUILD_LEDGER.md`

#### Tests run
- focused prototype edge-case tests with `PYTHONPATH=src`: `15 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `404 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-06 (QD Decision Loop Prototype v0.0 - Manual Trace Resolver)
#### What we built
- implemented an isolated prototype runtime module:
  - `src/qd_perception/decision_loop_prototype_v0_0.py`
- added deterministic manual-trace resolver surface:
  - `resolve_manual_decision_trace_v0_0(...)`
- added lightweight typed manual input/output contract support:
  - `ManualTraceInputV0`
  - qualitative enums for branch/temporal/substrate/suppression/contradiction/prior-state/output classes
- enforced fail-closed prototype rules:
  - collapse-blocking substrate/suppression and high/blocking contradiction force `external_hold`
  - projection-alone upgrade to resolved is blocked under sparse/conflicting recall or degraded substrate
  - conditional requires directional candidate + named conditions
  - limited/caution covers mixed/weak/caution-pressure cases
- kept scope strict:
  - no persistence
  - no autonomous learning
  - no coupling into evidence/consumer runtime surfaces

#### Files changed
- `src/qd_perception/decision_loop_prototype_v0_0.py`
- `tests/test_decision_loop_prototype_v0_0.py`
- `BUILD_LEDGER.md`

#### Tests run
- focused prototype tests with `PYTHONPATH=src`: `6 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `395 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-06 (QD Decision Loop v0.4a - Ambiguity Closure Notes / Spec Only)
#### What we built
- added a focused ambiguity-closure design artifact:
  - `QD_DECISION_LOOP_v0_4a.md`
- closed the specific v0.4 ambiguities for:
  - conditional answer vs limited/caution boundary
  - projection support vs projection-upgrade eligibility
  - qualitative substrate degradation bands
  - qualitative corrective-learning suppression bands
- preserved spec-only posture:
  - no runtime behavior changes
  - no coupling into existing evidence/consumer surfaces

#### Files changed
- `QD_DECISION_LOOP_v0_4a.md`
- `BUILD_LEDGER.md`

#### Tests run
- none (spec-only step; no runtime/code-path changes)

### Session date: 2026-04-06 (QD Decision Loop v0.4 - Worked Decision Traces / Spec Only)
#### What we built
- added a worked-trace design artifact:
  - `QD_DECISION_LOOP_v0_4.md`
- included canonical declarative traces for:
  - strong past recall / weak projection
  - weak past recall / strong projection
  - substrate degradation forcing external HOLD
  - corrective-learning relevance suppressing collapse
  - mixed evidence producing limited/caution output
- each trace records:
  - input/delta
  - polarity split
  - internal HOLD state
  - past recall contribution
  - future projection contribution
  - substrate integrity contribution
  - corrective-learning contribution
  - collapse-vs-block rationale
  - output class
- explicit ambiguity notes were added to capture unresolved spec boundaries.

#### Files changed
- `QD_DECISION_LOOP_v0_4.md`
- `BUILD_LEDGER.md`
- `runs/qd_decision_loop_v0_4_worked_traces_transcript.txt`
- `runs/qd_decision_loop_v0_4_worked_traces_delivery.txt`

#### Tests run
- none (spec-only step; no runtime/code-path changes)

### Session date: 2026-04-06 (QD Decision Loop v0.3 - Branch Weighting / Collapse Heuristics Draft / Spec Only)
#### What we built
- added a new decision-loop design artifact:
  - `QD_DECISION_LOOP_v0_3.md`
- defined draft branch-strength inputs for both `-1` and `+1`
- defined evidence classes for:
  - grounded past recall
  - future projection
  - substrate integrity quality
  - corrective-learning relevance
  - contradiction pressure
- defined weighting asymmetry rules for:
  - grounded recall vs projection
  - substrate degradation effects
  - remembered wrongness effects
- defined collapse heuristics draft for:
  - resolved `-1`
  - resolved `+1`
  - conditional answer
  - limited/caution answer
  - external HOLD
- preserved non-goals:
  - no runtime implementation
  - no autonomous decision logic
  - no hidden coupling into existing code paths

#### Files changed
- `QD_DECISION_LOOP_v0_3.md`
- `BUILD_LEDGER.md`
- `runs/qd_decision_loop_v0_3_branch_weighting_transcript.txt`
- `runs/qd_decision_loop_v0_3_branch_weighting_delivery.txt`

#### Tests run
- none (spec-only step; no runtime/code-path changes)

### Session date: 2026-04-06 (QD Decision Loop v0.2 - Resolution Criteria Draft / Spec Only)
#### What we built
- added a new decision-loop design artifact:
  - `QD_DECISION_LOOP_v0_2.md`
- defined draft resolution criteria for collapse out of internal HOLD vs block conditions
- defined explicit output-class criteria:
  - resolved `-1`
  - resolved `+1`
  - conditional answer
  - limited/caution answer
  - external HOLD
- clarified Delta Ingress role:
  - change detection
  - normalization
  - prior-state comparison anchor
  - weak/missing prior-state handling posture
- clarified temporal asymmetry weighting:
  - grounded past recall stronger than softer future projection
- preserved non-goals:
  - no runtime implementation
  - no autonomous decision logic
  - no coupling into evidence/consumer runtime surfaces

#### Files changed
- `QD_DECISION_LOOP_v0_2.md`
- `BUILD_LEDGER.md`
- `runs/qd_decision_loop_v0_2_resolution_criteria_transcript.txt`
- `runs/qd_decision_loop_v0_2_resolution_criteria_delivery.txt`

#### Tests run
- none (spec-only step; no runtime/code-path changes)

### Session date: 2026-04-06 (QD Decision Loop v0.1 - Geometry Clarification Revision)
#### What we built
- revised the existing `QD_DECISION_LOOP_v0_1.md` spec to correct HOLD semantics:
  - internal HOLD = active zone/contact plane
  - external HOLD = output node when resolution is not earned
- clarified stage semantics:
  - polarity split generates the internal HOLD zone
  - assessment chamber is the active tension/synthesis zone
  - past recall and future projection both run inside the active zone
  - past recall and future projection are not epistemically symmetric
- clarified loop flow:
  - internal HOLD does not re-enter
  - only external HOLD loops back on new delta/evidence
- clarified Delta Ingress role:
  - change detection + normalization + prior-state comparison anchor
- preserved non-goals:
  - no runtime implementation
  - no autonomous decision logic
  - no coupling into existing evidence/consumer surfaces

#### Files changed
- `QD_DECISION_LOOP_v0_1.md`
- `BUILD_LEDGER.md`

#### Tests run
- none (spec-only revision; no runtime/code-path changes)

### Session date: 2026-04-06 (QD Decision Loop v0.1 - Design Anchor / Spec Only)
#### What we built
- anchored `QD Decision Loop v0.1` as a repo-visible design specification:
  - `Question -> Delta Split -> Polarity Evaluation -> Temporal Assessment -> Resolution`
- stage definitions recorded:
  - Question Node
  - Delta Ingress
  - Polarity Split
  - Assessment Chamber
  - Past Outcome Recall
  - Future Outcome Projection
  - Resolution Node
- explicit output possibilities recorded:
  - answer
  - conditional answer
  - limited/caution answer
  - HOLD
- relationship to current build recorded:
  - durable ledger integrity audit as root-truth substrate check
  - corrective learning v1.0a/v1.1/v1.2 as remembered wrongness structure
  - decision loop as future behavioral control loop candidate
- explicit non-goals recorded:
  - not implemented behavior yet
  - no runtime coupling yet
  - no autonomous learning yet
  - no confidence/posture rewrite yet

#### Files changed
- `QD_DECISION_LOOP_v0_1.md`
- `BUILD_LEDGER.md`

#### Tests run
- none (spec-only step; no runtime/code-path changes)

### Session date: 2026-04-06 (Corrective Learning v1.2 - Audit Finding to Corrective Record Mapping)
#### What we built
- added explicit read-only mapping helper:
  - `map_durable_ledger_audit_findings_to_corrective_records_v1_2(...)`
- mapping scope intentionally constrained to durable-ledger integrity audit findings only
- deterministic mapping classes currently include:
  - duplicate event_id ambiguity
  - ledger ordering issue
  - required field/schema issue
  - lineage anchor mismatch/unusable
- mapping composition anchored to existing corrective-learning surfaces:
  - `build_corrective_learning_record_v1a(...)`
  - `format_corrective_learning_record_v1a(...)`
  - `validate_corrective_learning_record_v1a(...)`
- truth note:
  - no persistence added
  - no automatic invocation added to audit surfaces
  - no evidence/consumer behavior changes
  - no autonomous/adaptive behavior added

#### Files changed
- `src/qd_perception/neutral_family_memory_v1.py`
- `tests/test_corrective_learning_audit_mapping_v1_2.py`
- `BUILD_LEDGER.md`
- `runs/corrective_learning_v1_2_audit_mapping_transcript.txt`
- `runs/corrective_learning_v1_2_audit_mapping_delivery.txt`

#### Tests run
- focused corrective-learning mapping/contract tests with `PYTHONPATH=src`: `16 passed, 1 warning`
- adjacent root-truth tests with `PYTHONPATH=src`: `33 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `389 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-06 (Corrective Learning v1.1 - Example Record Builder / Formatter)
#### What we built
- added deterministic corrective-learning usage-path helpers:
  - `build_corrective_learning_record_v1a(...)`
  - `format_corrective_learning_record_v1a(...)`
- builder behavior:
  - explicit input-only construction
  - enforced v1.0a contract compatibility via `validate_corrective_learning_record_v1a(...)`
  - fail-closed `ValueError` on invalid shape/type input
- formatter behavior:
  - deterministic export/report shape
  - explicit field order from contract-required field list
  - read-only guardrail flags remain false
- truth note:
  - no persistence added
  - no autonomous/adaptive behavior added
  - no coupling added into top consumer/evidence surfaces

#### Files changed
- `src/qd_perception/neutral_family_memory_v1.py`
- `tests/test_corrective_learning_builder_formatter_v1_1.py`
- `BUILD_LEDGER.md`
- `runs/corrective_learning_v1_1_builder_formatter_transcript.txt`
- `runs/corrective_learning_v1_1_builder_formatter_delivery.txt`

#### Tests run
- focused corrective-learning builder/contract tests with `PYTHONPATH=src`: `11 passed, 1 warning`
- adjacent root-truth tests with `PYTHONPATH=src`: `28 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `384 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-06 (Corrective Learning v1.0a - Contract / Schema Only)
#### What we built
- implemented minimal contract-only corrective-learning schema surfaces:
  - `CorrectiveLearningRecordV1a`
  - `get_corrective_learning_record_contract_v1a()`
  - `validate_corrective_learning_record_v1a(...)`
- truth note:
  - no autonomous learning behavior added
  - no adaptive behavior added
  - no coupling added into top consumer/evidence surfaces
  - no mutation/backfill/history rewrite behavior added

#### Files changed
- `src/qd_perception/neutral_family_memory_v1.py`
- `tests/test_corrective_learning_contract_v1a.py`
- `BUILD_LEDGER.md`
- `runs/corrective_learning_v1_0a_contract_schema_transcript.txt`
- `runs/corrective_learning_v1_0a_contract_schema_delivery.txt`

#### Tests run
- focused corrective-learning contract tests with `PYTHONPATH=src`: `6 passed, 1 warning`
- adjacent root-truth tests with `PYTHONPATH=src`: `23 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `379 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-06 (Durable Transition Ledger Integrity Audit v1.0)
#### What we built
- implemented and validated `get_durable_transition_ledger_integrity_audit()` as a read-only foundational durable-ledger integrity audit surface
- audit scope enforces:
  - durable ledger readability/shape checks
  - per-event minimal transition schema conformance for downstream relied fields
  - duplicate `event_id` and ambiguity detection
  - ledger ordering integrity checks
  - lineage anchor consistency checks via:
    - `run_lineage_integrity_audit(...)`
    - `get_lineage_integrity_report(...)`
- truth note:
  - no bounded stack continuation was built
  - no upper consumer predicate behavior was changed

#### Files changed
- `src/qd_perception/neutral_family_memory_v1.py`
- `tests/test_durable_transition_ledger_integrity_audit.py`
- `BUILD_LEDGER.md`
- `runs/durable_transition_ledger_integrity_audit_v1_0_transcript.txt`
- `runs/durable_transition_ledger_integrity_audit_v1_0_delivery.txt`

#### Tests run
- focused durable-ledger audit tests with `PYTHONPATH=src`: `5 passed, 1 warning`
- adjacent durable-ledger/lineage tests with `PYTHONPATH=src`: `17 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `373 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-06 (Bounded Consumer-Gate Cross-Window Parity Hardening)
#### What we built
- test hardening only; no production/API layer changes
- added explicit cross-window equivalence tests in `tests/test_system_evidence_review_sampler_consumer_gate.py`:
  - `test_cross_window_equivalence_ready_locked_yields_rely`
  - `test_cross_window_equivalence_partial_locked_yields_limited`
  - `test_cross_window_equivalence_inconsistent_stage_lock_yields_hold`
- truth note:
  - production inspection found no real bug in bounded consumer-gate runtime logic
  - both bounded consumer-gate modes already share one helper and one decision-branch set
  - parity hardening closed the currently observed cross-window parity gap; no new API was earned this session

#### Files changed
- `tests/test_system_evidence_review_sampler_consumer_gate.py`
- `BUILD_LEDGER.md`

#### Tests run
- focused bounded consumer-gate tests with `PYTHONPATH=src`: `11 passed, 1 warning`
- adjacent bounded sampler/stage-lock/gate tests with `PYTHONPATH=src`: `30 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-05 (Bounded System Evidence Review Consumer Gate v1.2)
#### What we built
- implemented bounded sampler consumer-gate surfaces:
  - `get_system_evidence_review_sampler_consumer_gate_window(...)`
  - `get_system_evidence_review_sampler_consumer_gate_event_order_window(...)`
- decision posture constrained to bounded sampler + bounded sampler stage-lock only:
  - `RELY` only for bounded sampler READY under bounded sampler stage-lock LOCKED
  - `LIMITED` for bounded sampler PARTIAL under bounded sampler stage-lock LOCKED
  - `HOLD` for unavailable/inconsistent/unusable inputs (fail-closed)
- no direct lower-band raw/windowed calls and no full-range posture predicates in bounded gate decisions

#### Files changed
- `src/qd_perception/neutral_family_memory_v1.py`
- `tests/test_system_evidence_review_sampler_consumer_gate.py`
- `BUILD_LEDGER.md`
- `runs/bounded_system_evidence_review_consumer_gate_v1_2_transcript.txt`
- `runs/bounded_system_evidence_review_consumer_gate_v1_2_delivery.txt`

#### Tests run
- focused bounded consumer-gate + adjacent sampler/stage-lock tests with `PYTHONPATH=src`: `27 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `365 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-05 (Bounded System Evidence Review Consistency / Stage Lock v1.1)
#### What we built
- implemented bounded sampler contract-audit surfaces:
  - `get_system_evidence_review_sampler_stage_lock_window(...)`
  - `get_system_evidence_review_sampler_stage_lock_event_order_window(...)`
- audit checks include:
  - matching-mode bounded composition integrity
  - fail-closed behavior under window-spec misalignment
  - bounded scope non-equivalence to full-range
  - full-range surfaces remain non-predicate context
  - read-only guardrail flags

#### Files changed
- `src/qd_perception/neutral_family_memory_v1.py`
- `tests/test_system_evidence_review_sampler_stage_lock.py`
- `BUILD_LEDGER.md`
- `runs/bounded_system_evidence_review_sampler_stage_lock_v1_1_transcript.txt`
- `runs/bounded_system_evidence_review_sampler_stage_lock_v1_1_delivery.txt`

#### Tests run
- focused bounded sampler stage-lock tests with `PYTHONPATH=src`: `7 passed, 1 warning`
- adjacent bounded sampler/review tests with `PYTHONPATH=src`: `34 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `357 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

### Session date: 2026-04-05 (Bounded System Evidence Review Sampler v1.0)
#### What we built
- implemented bounded system evidence-review sampler surfaces:
  - `get_system_evidence_review_sampler_window(...)`
  - `get_system_evidence_review_sampler_event_order_window(...)`
- composition constrained to matching bounded review modes only:
  - index-to-index
  - event-order-to-event-order
- fail-closed behavior enforced on missing/unusable/shape-invalid/misaligned bounded review surfaces
- no direct lower-band raw/windowed source calls and no hidden full-range posture predicates

#### Files changed
- `src/qd_perception/neutral_family_memory_v1.py`
- `tests/test_system_evidence_review_sampler_windowed.py`
- `BUILD_LEDGER.md`
- `runs/bounded_system_evidence_review_sampler_v1_0_transcript.txt`
- `runs/bounded_system_evidence_review_sampler_v1_0_delivery.txt`

#### Tests run
- focused sampler tests with `PYTHONPATH=src`: `12 passed, 1 warning`
- adjacent bounded review/system tests with `PYTHONPATH=src`: `31 passed, 1 warning`
- full pytest with `PYTHONPATH=src`: `350 passed, 1 warning`

#### Warnings
- pytest cache permission warning
- temp symlink cleanup PermissionError warning (non-blocking)

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
- `get_system_evidence_review_sampler_window(...)`
- `get_system_evidence_review_sampler_event_order_window(...)`
- `get_system_evidence_review_sampler_stage_lock_window(...)`
- `get_system_evidence_review_sampler_stage_lock_event_order_window(...)`
- `get_system_evidence_review_sampler_consumer_gate_window(...)`
- `get_system_evidence_review_sampler_consumer_gate_event_order_window(...)`
- `get_durable_transition_ledger_integrity_audit()`
- `CorrectiveLearningRecordV1a`
- `get_corrective_learning_record_contract_v1a()`
- `validate_corrective_learning_record_v1a(...)`
- `build_corrective_learning_record_v1a(...)`
- `format_corrective_learning_record_v1a(...)`
- `map_durable_ledger_audit_findings_to_corrective_records_v1_2(...)`
- `ManualTraceInputV0`
- `resolve_manual_decision_trace_v0_0(...)`
- `manual_trace_input_to_dict(...)`

---

## Next Step
### Immediate next step
- commit and push the ratified EXPERIMENTAL_FOUNDATION.md update
- then select the next Phase I artifact to draft
- recommended next artifact: governance/REBUILD_RATIONALE.md

### Why this is the next honest step
- the governing build plan is already in place
- EXPERIMENTAL_FOUNDATION.md is now ratified
- Phase I should continue by closing the next constitutional gap named by the empirical bridge
- REBUILD_RATIONALE.md is the strongest candidate because missing/partial QD_v3 inheritance is now explicitly bounded

### What it must use
- governance/QD_END_TO_END_BUILD_PLAN_v0_3.md
- governance/EXPERIMENTAL_FOUNDATION.md
- BUILD_LEDGER.md
- inspected QD_v3 source files and any recoverable legacy rationale artifacts

### What it must NOT do
- reopen ratified empirical bridge claims casually
- invent QD_v3 failure causes not grounded in recoverable source
- drift back into unguided architecture work outside Phase I priorities
- bypass governance documents when advancing the build

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
**Suggested commit message:** Add decision loop prototype v0.0a edge-case pressure tests and ledger update

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
Resume qd_perception_spine from BUILD_LEDGER.md and governance/QD_END_TO_END_BUILD_PLAN_v0_3.md.

Read these first:
1. governance/QD_END_TO_END_BUILD_PLAN_v0_3.md
2. BUILD_LEDGER.md
3. applicable files in /governance/ for the current Phase I task

Current governing posture:
- v0.3 is governing
- Phase I is open
- EXPERIMENTAL_FOUNDATION.md is ratified
- constitutional artifacts must be read before advancing the build

Immediate next target:
- choose and draft the next constitutional artifact
- recommended next target: governance/REBUILD_RATIONALE.md

Do not:
- reopen lower-band semantics casually
- invent new predicates outside constitutional scope
- bypass governance docs when advancing the build
- treat prototype history as current frontier

---

## End-of-Day Snapshot
### Built today
- Added Decision Loop Prototype v0.0a edge-case pressure tests
- Corrected two prototype-only spec-consistency issues exposed by pressure tests
- Verified full suite on updated prototype v0.0a baseline
- Implemented QD Decision Loop Prototype v0.0 manual trace resolver in isolated module
- Added focused prototype tests and verified full-suite baseline after prototype addition
- Implemented Corrective Learning v1.2 audit-finding to corrective-record mapping
- Added focused corrective-learning audit-mapping tests
- Verified full suite on updated corrective-learning v1.2 frontier
- Implemented Corrective Learning v1.1 builder/formatter usage path
- Added focused corrective-learning builder/formatter tests
- Verified full suite on updated corrective-learning v1.1 frontier
- Implemented Corrective Learning v1.0a contract/schema surfaces
- Added focused corrective-learning contract tests
- Verified full suite on updated corrective-learning contract frontier
- Implemented Durable Transition Ledger Integrity Audit v1.0
- Added focused durable-ledger integrity audit tests
- Verified full suite on updated durable-ledger integrity frontier
- Implemented Bounded System Evidence Review Consistency / Stage Lock v1.1 (index + event-order)
- Added focused bounded system sampler stage-lock tests
- Verified full suite on updated bounded sampler stage-lock frontier
- Implemented Bounded System Evidence Review Sampler v1.0 (index + event-order)
- Added focused bounded system sampler tests
- Verified full suite on updated bounded system sampler frontier
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
- decision-loop prototype surface `resolve_manual_decision_trace_v0_0(...)` is present in `decision_loop_prototype_v0_0.py`
- focused prototype edge-case suite reported green at 15 passed, 1 warning
- unified posture stage-lock audit surface is present in `neutral_family_memory_v1.py`
- unified summary delivery surface is present in `neutral_family_memory_v1.py`
- observability evidence-review surface is present in `neutral_family_memory_v1.py`
- observability evidence-review stage-lock surface is present in `neutral_family_memory_v1.py`
- bounded cross-band evidence-review windowed surfaces are present in `neutral_family_memory_v1.py`
- bounded observability evidence-review windowed surfaces are present in `neutral_family_memory_v1.py`
- bounded system evidence-review sampler surfaces are present in `neutral_family_memory_v1.py`
- bounded system evidence-review sampler stage-lock surfaces are present in `neutral_family_memory_v1.py`
- bounded system evidence-review sampler consumer-gate surfaces are present in `neutral_family_memory_v1.py`
- durable transition-ledger integrity audit surface is present in `neutral_family_memory_v1.py`
- corrective-learning contract/schema surfaces are present in `neutral_family_memory_v1.py`
- corrective-learning builder/formatter surfaces are present in `neutral_family_memory_v1.py`
- corrective-learning audit-mapping surface is present in `neutral_family_memory_v1.py`
- final full suite reported green at 404 passed, 1 warning
- focused system-evidence revalidation suite reported green at 28 passed, 1 warning
- top unified posture stage lock present and validated
- repo initialized and first local checkpoint commit created

### Open questions
- Should qd_perception_spine become its own Git repo?
- What run artifacts belong in version control?
- How should truth_engine_v1 relate to this repo, if at all?

### First action next session
- read BUILD_LEDGER.md first
- hold prototype integration/autonomy/persistence expansion; pressure-test manual traces only unless explicit coupling contract is requested
- update ledger again before stopping

### Pressure items / risks
- continuity drift if ledger is not kept current
- repo drift if Git is not initialized soon
- artifact clutter if `runs/` is committed indiscriminately
- avoid accidental bounded-to-full-range equivalence claims in any new bounded system sampler output
- avoid hidden predicate coupling from durable-ledger audit into existing upper evidence surfaces
- avoid implicit behavior creep from corrective-learning contract into autonomous/adaptive logic
- avoid implicit auto-invocation coupling of audit-to-correction mapping without explicit contract
- avoid accidental coupling of decision-loop prototype into existing evidence/consumer runtime surfaces without explicit contract

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
