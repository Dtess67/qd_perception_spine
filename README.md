# QD Perception Spine

An experimental perception subsystem for the QD architecture, designed to process raw sensory input before it reaches language or high-level expression layers.

## Overview
The `qd_perception_spine` module acts as the "front door" for external stimuli. It is **difference-first**, meaning it focuses on detecting changes (deltas) in input channels rather than just processing absolute states.

## Project Status & Versioning
- **Current Version:** `0.5.1` (defined in `src/qd_perception/__init__.py`).
- **Audit Trails:** Demo runs are persisted to `runs/perception_demo_audit.json` with a manifest-enabled JSON format.

### Key Architecture Stages
1.  **Sensor Events (`SensorEvent`):** Raw numeric data points from physical or virtual sensors (light, touch, temperature, etc.).
2.  **Delta Frames (`DeltaFrame`):** Computed differences between events, identifying magnitude, direction, and rate of change.
3.  **Feature Frames (`FeatureFrame`):** Qualitative categorization of deltas (e.g., "rising trend", "high intensity", "spike pattern").
4.  **Proto-Concepts (`ProtoConcept`):** Pre-linguistic mental labels (e.g., "sudden_rise", "gradual_shift", "stable_signal").
5.  **Status Codes & Labels:** Concise, deterministic summaries of the perception result (e.g., `SUDDEN_RISE`, `STABLE_SIGNAL`).
6.  **Candidate State Bridge (`CandidateState`):** Translates pre-linguistic perception results into internal "posture" (uncertainty, risk, evidence, emotional intensity).
7.  **Neutral State Vector (`NeutralStateVector`):** A parallel experimental bridge that uses structurally neutral axes (`axis_a`, `axis_b`, `axis_c`, `axis_d`) to avoid early human-shaped names like `harm_risk` or `uncertainty`.
8.  **Neutral Symbol Identity Contract v1.1/v2:** A deterministic structural bridge for deciding when a recurring pattern is new, a match, or a split.
    - **Trace Continuity:** Minted symbols carry forward their full structural history (centroid) from pre-symbol observations.
    - **Identity Anchoring:** Each symbol preserves its `mint_signature` to prevent slow identity smear from moving averages.
    - **Structural Envelope (Spread):** Symbols now track their initial and current structural "width" using Average Absolute Deviation (AAD), allowing the system to distinguish between tight and loose pattern families.
    - **Persistence Rule:** Drift/split only triggers after sustained (consecutive) divergence, preventing noise-driven identity fractures.
    - **Honest Status:** `RETIRED_RESERVED` explicitly marks unimplemented cleanup states.
9.  **Symbol Memory:** A persistent internal identity-memory experiment. Repeated stable regions earn neutral "symbols" (e.g., `sym_01`) to allow the system to recognize recurring structural placements before they are translated into human-readable concepts.

## Audit & Versioning
The `qd_perception_spine` module includes a built-in audit export system. Each demo run generates a structured JSON file that includes:
- **Manifest:** Version stamp (`module_version`), export timestamp (`exported_at`), and scenario metadata.
- **Scenario Records:** Full detail of every sensor event, derived delta/feature frames, and the final proto-concept identified.

This enables long-term behavior tracking and comparison across different versions of the perception logic.

## Why This Exists
This module provides a structured, deterministic way to translate raw sensor noisy data into discrete "mental tokens" that the rest of the QD architecture (like the expression spine) can eventually act upon.

## The State Bridge
The `qd_perception_spine` includes a mapper that converts perception results directly into a `CandidateState`. This state represents the internal "feeling" or "posture" of the system (e.g., high uncertainty, elevated risk) before it is translated into human-readable language.

This bridge is the first step toward connecting the input-focused perception module with the output-focused expression module.

## The Handshake Demo
The `qd_perception_spine` module includes a first "handshake" demo between perception and expression. The `handshake_demo.py` script takes a `CandidateState` from the perception spine, adapts it for the `qd_expression_spine`, and runs it through the full expression pipeline to produce human-readable phrases (e.g., "verified" for a stable signal).

This is a demo bridge and represents the first end-to-end flow from raw sensory stimulus to communicative output.

## Comparison & Analysis
The `bridge_comparison_demo.py` script acts as a diagnostic harness to study how the same sensory data is interpreted through different internal lenses:
- **Semantic Bridge:** Interprets perception results as human-shaped "posture" (risk, uncertainty, evidence).
- **Structural Bridge:** Interprets perception results as neutral vectors and abstract regions (axes A-D, region IDs).

This harness helps identify where human interpretation enters the system and ensures that the pre-semantic structural integrity of sensory data is preserved.

## Pattern Families & Glyph Earning
The `glyph_earning_demo.py` script demonstrates how stable structural patterns in the neutral lane earn unique, neutral identifiers (glyphs):
- **Stability Score:** Measures how consistently a repeated pattern lands in the same structural region.
- **Glyph Assignment:** Only occurs after a pattern family meets both frequency (minimum count) and stability thresholds.
- **Neutrality:** Glyph IDs (e.g., `glyph_01`, `glyph_02`) are intentionally numeric placeholders to ensure identity is earned via structure, not assigned via human language.

This layer allows the system to recognize and name recurring structural "shapes" in sensory data before a human-meaning bridge is ever built.

## Symbol Memory (Neutral Identity)
The `SymbolMemory` component in the neutral lane allows the system to recognize recurring structural "shapes" (regions) and assign persistent internal markers:
- **Persistent Symbols:** Once a region earns a neutral ID (e.g., `sym_01`), subsequent sightings of that same region reuse the same ID.
- **Earning Rule:** A region only earns a symbol after it has been seen multiple times with sufficient structural stability.
- **Pre-Semantic Identity:** These symbols serve as internal markers of "I have seen this structural configuration before," before any human-assigned name is attached to it.
10. **Neutral Family Formation:** A higher-order grouping layer that links related symbols together into families (e.g., `fam_01`) based on structural proximity.
    - **Symbol vs Family:** Symbols remain the primary identity units. Families provide a kinship layer without collapsing distinct symbol identities.
    - **Kinship Criteria:** Based on centroid distance and spread compatibility in the axis space.
    - **Conservative Grouping (Hold/Uncertainty Lane):** Implements a "hold" band and persistence requirements to prevent premature family collapse and ensure kinship is earned.
    - **Neutral Kinship:** Families are formed only when structural similarity is high, ensuring distinct shapes remain separate unless a strong kinship is earned.
11. **Multi-Family Tension v1:** A safety layer that detects when a symbol is structurally compatible with more than one family.
    - **Decision Hold:** If multiple families are too close in similarity (margin < 0.05), the system holds assignment under `FAMILY_TENSION`.
    - **Decisive Margin:** A symbol only joins a family if the best match is significantly better than the next best.
    - **Conservative:** One-family-only membership is enforced; unresolved competition results in a hold, not a forced merge.
12. **Bridge / Edge Symbols v1:** A persistence-aware boundary representation for symbols that repeatedly live near family borders.
    - **FAMILY_BRIDGE:** Earned after repeated `FAMILY_TENSION` (unresolved proximity to two or more families).
    - **FAMILY_EDGE:** Earned after repeated `FAMILY_HOLD` (borderline proximity to a single family).
    - **Persistence Required:** Status is only earned after 3 consecutive boundary/tension events, preventing noise-driven status shifts.
    - **No Forced Assignment:** Bridge/edge status identifies persistent boundary behavior without forcing a family assignment.
13. **Family Fracture v1:** Detects internal structural instability or over-breadth within a family.
    - **FAMILY_FRACTURE_HOLD:** Status for families showing internal structural separation or over-breadth.
    - **FAMILY_SPLIT_READY:** Status for families that have persistently shown fracture risk.
    - **Coherence-Aware:** Threshold-based detection (`MAX_COHERENCE_SPREAD = 0.35`) ensures families remain structurally unified.
    - **Conservative:** Persistence is required (`FRACTURE_PERSISTENCE_THRESHOLD = 3`) before a split is considered ready.
14. **Internal Subgroup Detection v1:** First-pass heuristic to distinguish broad clouds from two persistent internal subgroups.
    - **Dual-Center Detection:** Heuristic based on internal distance patterns (`SUBGROUP_TIGHTNESS_RATIO = 2.0`).
    - **Persistence Required:** Confirms internal bifurcation after repeated evidence (`SUBGROUP_PERSISTENCE_THRESHOLD = 3`).
    - **Non-Splitting (Prior Behavior):** Detection informed fracture state (`SPLIT_READY`) but did not execute successor creation.
15. **Actual Family Fission / Successor Family Creation v1:** Conservative structural succession from one family into two.
    - **Requires BOTH:** Persistent `FAMILY_SPLIT_READY` AND persistent dual-center subgroup evidence.
    - **Additional Conservatism:** Fission requires a stable subgroup partition to persist across additional observations (`FISSION_PERSISTENCE_THRESHOLD = 3`), refuses fission on tiny families (`MIN_MEMBERS_FOR_FISSION = 6`), and refuses fission when one subgroup is too small to be a successor (`MIN_SUBGROUP_MEMBERS_FOR_FISSION = 3`).
    - **Explicit Lineage:** Successor families store `lineage_parent_family_id` and `lineage_fission_event_id`; the parent stores `lineage_successor_family_ids`, `historical_member_symbol_ids`, and an in-process fission event record.
    - **No Silent Rewrites:** Parent family becomes inactive (`FAMILY_INACTIVE_SUCCESSOR_SPLIT`) and is preserved as a historical record rather than being overwritten as if it never existed.
    - **No Human Semantics:** The event rationale and gate summary remain structural-only.
16. **Actual Family Reunion / Re-merge v1:** Conservative structural reunion from two active families into one new successor family.
    - **New Successor Required:** Reunion does not overwrite either source family. It mints a new family ID for the reunited structure.
    - **Persistence Required:** One favorable observation is insufficient. Reunion requires repeated closeness (`REUNION_PERSISTENCE_THRESHOLD = 4`).
    - **Structural Gate Stack:** Requires center proximity (`REUNION_CENTER_DISTANCE_THRESHOLD = 0.10`), spread compatibility (`REUNION_SPREAD_DELTA_THRESHOLD = 0.08`), envelope overlap, and combined coherence checks (`REUNION_COMBINED_MAX_SPREAD = 0.30`, `REUNION_COMBINED_MAX_INTERNAL_DISTANCE = 0.30`).
    - **Source Family Minimums:** Each source family must have enough membership to qualify (`MIN_MEMBERS_PER_SOURCE_FOR_REUNION = 2`).
    - **Explicit Two-Parent Lineage:** Reunited successor stores `lineage_parent_family_ids` and `lineage_reunion_event_id`; each source family stores reunion event references and becomes inactive (`FAMILY_INACTIVE_SUCCESSOR_REUNION`) with historical members preserved.
    - **No Human Semantics:** Reunion rationale and event logs remain structural-only.
17. **Durable Family Event Ledger v1:** File-backed local ledger for family transition history.
    - **Scope:** Persists fission and reunion events to a durable local ledger while preserving existing in-memory event behavior.
    - **Format:** JSONL (one JSON object per line) for deterministic append-only writes and easy human inspection.
    - **Default Location:** `runs/family_transition_event_ledger_v1.jsonl`.
    - **Core Event Fields:** `event_id`, `event_type`, `event_order`, `source_family_ids`, `successor_family_ids`, `gate_summary`, structural membership summary (`partition` for fission, `members` for reunion), `rationale`.
    - **Ledger Metadata Fields:** `ledger_write_order`, `ledger_timestamp_utc`.
    - **Read/Query API:** `get_event_ledger()` and `get_events_for_family(family_id)`.
    - **Fail-Closed Write Behavior:** topology transitions attempt durable write first; write failure raises and prevents transition commit.
    - **v1 Limits:** local file only, no multi-process writer coordination, no compaction/rotation, no external database.
18. **Genealogy / Ancestry Query Layer v1:** Query-only lineage reconstruction over the durable ledger.
    - **Transition Source of Truth:** ancestry queries use the durable event ledger as primary transition history.
    - **Core Queries:** `get_family_origin(family_id)`, `get_family_parents(family_id)`, `get_family_successors(family_id, recursive=False, max_depth=6)`, `get_family_transition_events(family_id)`, `get_family_lineage(family_id, max_depth=6)`, `families_share_ancestry(family_a, family_b, max_depth=6)`.
    - **Structured Outputs:** query functions return deterministic dict/list structures suitable for tests and audit inspection.
    - **Bounded Traversal:** recursive lineage/successor traversal is bounded by `max_depth` and guarded against loops.
    - **Fail-Closed Unknown Handling:** unknown family IDs return explicit `family_known=False` with empty lineage/event sets.
    - **v1 Limits:** no full graph analytics engine, no probabilistic inference, local file-backed transition assumptions.
19. **Lineage Integrity Audit v1:** Structural consistency audit over current family records and durable lineage ledger.
    - **Audit Scope:** validates current records, durable ledger events, and cross-source consistency between them.
    - **Issue Categories:** `record_issues`, `ledger_issues`, `cross_source_issues`.
    - **Core Checks:** duplicate ledger event IDs, invalid/unknown family references, inactive families with live members, one-family-only symbol violations, lineage mismatches between record fields and ledger transitions, and bounded loop detection in lineage graph traversal.
    - **Audit API:** `run_lineage_integrity_audit(family_id=None, max_depth=8)` and `get_lineage_integrity_report(...)`.
    - **Bounded Loop Checks:** loop detection is explicit and depth-bounded (`max_depth`) to avoid unbounded traversal.
    - **Fail-Closed Reporting:** audit reports issues explicitly and does not auto-repair lineage state.
    - **v1 Limits:** no self-healing, no multi-file/event-stream reconciliation, local file-backed assumptions remain.
20. **Ancestry Report / Family Dossier v1:** Structured single-family dossier assembled from existing lineage systems.
    - **Query-Only Adapter:** does not redesign lineage, ledger, or audit layers; composes existing outputs.
    - **API:** `get_family_dossier(family_id, max_depth=8)` and alias `get_family_ancestry_report(...)`.
    - **Sections Included:** identity/current state, origin/lineage chain, descendants/successors, event history, minimal relations summary, integrity summary.
    - **Data Sources:** current family record + durable ledger + ancestry query APIs + per-family integrity audit.
    - **Traversal:** descendant/lineage traversal uses existing bounded loop-safe ancestry methods with explicit `max_depth`.
    - **Unknown Handling:** returns explicit structured `found=false` report (`reason=FAMILY_NOT_FOUND`) with no fabricated lineage.
    - **v1 Limits:** no narrative generation, no new source of truth, no full graph analytics beyond existing ancestry/audit bounded queries.
21. **Transition Explanation Report v1:** Structured single-event transition report assembled from existing lineage systems.
    - **Query-Only Adapter:** does not redesign ledger, ancestry, dossier, or audit layers; composes existing outputs.
    - **API:** `get_transition_report(event_id, max_depth=8)` and alias `get_event_dossier(...)`.
    - **Sections Included:** event identity, structural gate/rationale, participants, before/after current family state snapshot, lineage links, event-scoped integrity summary.
    - **Data Sources:** durable event ledger + current family records + ancestry query APIs + lineage integrity audit API.
    - **Unknown Handling:** returns explicit structured `found=false` report (`reason=EVENT_NOT_FOUND`) with no fabricated transition detail.
    - **Integrity Scope:** event-centered filtering of audit issues by `event_id` and directly involved family IDs.
    - **v1 Limits:** current-state snapshots only (no full historical snapshots unless already stored in event/records), no auto-repair, local file-backed assumptions remain.
22. **Geometric Residual / Lineage Fit Audit v1:** Structural fit auditing for family geometry and lineage transitions.
    - **Audit-Oriented Layer:** measurement/reporting only; no automatic lineage rewrite or transition outcome override.
    - **Core APIs:** `get_family_geometry_fit(family_id)` and `get_transition_geometry_fit(event_id)`.
    - **Fit Metric:** compares family stored geometry against member-derived aggregate geometry:
      center residual (`current_signature` vs member centroid), spread residual (`current_spread` vs member spread average), and normalized residual ratios.
    - **Broad-vs-False Separation:** broad families are not penalized by breadth alone; center residual is normalized by member dispersion/spread baseline.
    - **Fit Status Labels:** `GEOMETRY_FIT_GOOD`, `FAMILY_GEOMETRY_FIT_DECAY`, `FIT_RESIDUAL_HIGH`, `GEOMETRY_FIT_UNKNOWN`.
    - **Transition Fit Scope:** reports participant family fit plus event continuity center residual checks for fission/reunion events.
    - **Report Integration:** family dossier and transition report include `geometry_fit_summary` sections.
    - **Heuristics (Provisional):** `GEOMETRY_FIT_CENTER_RESIDUAL_MAX=0.03`, `GEOMETRY_FIT_CENTER_RESIDUAL_RATIO_MAX=0.35`, `GEOMETRY_FIT_SPREAD_RESIDUAL_MAX=0.03`, `GEOMETRY_FIT_SPREAD_RESIDUAL_RATIO_MAX=0.60`, `GEOMETRY_FIT_SCORE_DECAY_MAX=1.50`, `TRANSITION_CONTINUITY_CENTER_RESIDUAL_MAX=0.08`.
    - **v1 Limits:** no auto-correction, no historical state reconstruction beyond stored records/events, local file-backed assumptions remain.
23. **Topology Residual / Shape-Class Audit v1:** First-pass internal shape audit above center/spread summaries.
    - **Audit-Oriented Layer:** measures internal arrangement shape; does not replace family geometry and does not auto-rewrite lineage.
    - **Core APIs:** `get_family_topology_audit(family_id)` and `get_transition_topology_audit(event_id)`.
    - **Shape Classes:** `SHAPE_COMPACT`, `SHAPE_ELONGATED`, `SHAPE_DUAL_LOBE`, `SHAPE_UNKNOWN`.
    - **Evidence Inputs:** member signatures, pairwise distance summaries, anisotropy proxy from axis variance, and subgroup partition evidence.
    - **Compression-Risk Flags:** `TOPOLOGY_COMPRESSION_RISK` and `SHAPE_NOT_WELL_CAPTURED_BY_CENTER_SPREAD` when shape likely exceeds center+spread abstraction.
    - **Fit vs Topology Separation:** topology can report `SHAPE_ELONGATED` or `SHAPE_DUAL_LOBE` even when geometry fit remains good.
    - **Report Integration:** family dossier includes `topology_summary`; transition report includes event-centered `topology_summary`.
    - **Heuristics (Provisional):** `TOPOLOGY_MIN_MEMBERS=4`, `TOPOLOGY_COMPACT_ANISOTROPY_MAX=1.80`, `TOPOLOGY_COMPACT_PAIRWISE_RATIO_MAX=1.60`, `TOPOLOGY_ELONGATED_ANISOTROPY_MIN=2.50`, `TOPOLOGY_ELONGATED_PAIRWISE_RATIO_MIN=2.00`.
    - **v1 Limits:** first-pass shape abstraction only, no manifold/graph topology reconstruction, no auto-correction.
24. **Family Stability / Split-Pressure Forecast v1:** Diagnostic pressure read over already-earned geometry/topology/lineage signals.
    - **Diagnostic-Only Layer:** no event creation, no lineage mutation, no probability claims.
    - **Core API:** `get_family_pressure_forecast(family_id)`.
    - **Pressure States:** `PRESSURE_STABLE`, `PRESSURE_STRETCHED`, `PRESSURE_DUAL_CENTER_RISK`, `PRESSURE_FISSION_PRONE`, `PRESSURE_UNCLEAR`.
    - **Signal Inputs:** family geometry fit, topology/shape + compression risk, subgroup persistence, fracture/fission persistence, bridge/edge fractions, transition-count context, and evidence sufficiency.
    - **Fail-Closed Posture:** returns `PRESSURE_UNCLEAR` when evidence is sparse, incomplete, inactive, or contradictory.
    - **Scoring Contract:** scorecard values are comparative diagnostic indicators on `0..1`, explicitly not probabilities.
    - **Heuristics (Provisional):** `PRESSURE_MIN_MEMBERS=4`, `PRESSURE_STRETCHED_THRESHOLD=0.55`, `PRESSURE_DUAL_CENTER_THRESHOLD=0.70`, `PRESSURE_INSTABILITY_THRESHOLD=0.65`, `PRESSURE_FISSION_PRONE_THRESHOLD=0.75`, `PRESSURE_STABLE_THRESHOLD=0.60`.
    - **v1 Limits:** no re-merge forecast state, no automatic transition triggers, no self-healing.
25. **Transition Pressure Snapshot v1.1:** Event-centered pressure snapshot audit from recoverable event-linked evidence only.
    - **Diagnostic-Only Layer:** no event creation, no lineage mutation, no history rewrite.
    - **Core API:** `get_transition_pressure_snapshot(event_id)`.
    - **Honesty Rule:** if event-time pressure is not stored in event-linked evidence, snapshot is unavailable; no reconstruction from current family state.
    - **Output Contract:** event metadata, participant IDs, `pre_event_pressure`, `post_event_pressure`, evidence flags, warnings, explanation lines, and explicit guardrail metadata.
    - **Recoverability:** supports none/partial/full snapshot recovery when ledger event includes recoverable pressure snapshot fields.
    - **v1.1 Limits:** no retroactive inference engine, no pressure persistence backfill, no mutation side effects.
26. **Event-Write-Time Pressure Capture v1.2:** Forward-only pressure capture on newly emitted lineage events.
    - **Forward-Only Capture:** new transition events may store `pressure_snapshot` at write time; no retrofit of historical events.
    - **Emit Paths Updated:** fission/reunion event emit paths capture pressure best-effort during event construction.
    - **Capture Contract:** `pre_event_pressure`, `post_event_pressure`, `capture_attempted`, `capture_succeeded`, `capture_mode=EVENT_WRITE_TIME`, `capture_reason`.
    - **Best-Effort / Fail-Closed:** capture failure does not fabricate snapshots; event can still be written with honest capture metadata.
    - **No Outcome Mutation:** capture does not alter lineage decision gates, transition outcomes, or membership assignment.
    - **Reader Compatibility:** `get_transition_pressure_snapshot(event_id)` now recovers event-local capture metadata when present.
    - **v1.2 Limits:** no historical reconstruction, no backfill, no new pressure states.
27. **Pressure Capture Integrity / Replay Audit v1.3:** Integrity audit for event-local `pressure_snapshot` truthfulness.
    - **Audit API:** `get_transition_pressure_capture_audit(event_id)`.
    - **Audit States:** `PRESSURE_CAPTURE_AUDIT_VALID`, `PRESSURE_CAPTURE_AUDIT_INVALID`, `PRESSURE_CAPTURE_AUDIT_UNAVAILABLE`.
    - **Checks:** structural validity, capture metadata consistency, payload consistency, side-map key/status consistency, and reader consistency against `get_transition_pressure_snapshot`.
    - **No Repair:** audit reports integrity mismatches without mutating or fixing events.
    - **No Retrofit:** events without `pressure_snapshot` remain audit-unavailable; no backfill is attempted.
    - **v1.3 Limits:** no historical reconstruction, no semantic interpretation, no payload compaction.
28. **Cross-Event Capture Quality Summary v1.4:** Read-only observability summary over transition-event pressure capture health.
    - **Summary API:** `get_pressure_capture_quality_summary()`.
    - **Mode:** `summary_mode=LEDGER_READ_ONLY`; reads durable ledger plus existing snapshot/audit APIs only.
    - **Top-Level Counts:** total transition events, auditable event count, snapshot present/missing, audit-state counts, capture-reason counts, recoverability counts, and event-type counts.
    - **Per-Type Breakdown:** per event type, reports total/present/missing with audit/capture-reason/recoverability sub-counts.
    - **Honesty Rules:** preserves invalid/unavailable states explicitly and does not smooth them away.
    - **Guardrails:** no lineage mutation, no event creation, no history rewrite, no repair, no retrofit.
    - **v1.4 Limits:** no payload compaction and no historical reconstruction; local file-backed assumptions remain.
29. **Bounded Time-Slice Capture Quality Summary v1.5:** Read-only windowed observability over transition-event capture quality.
    - **Windowed Summary API:** `get_pressure_capture_quality_summary_window(start_index=None, end_index=None, max_events=None)`.
    - **Mode:** `summary_mode=LEDGER_READ_ONLY_WINDOWED`; uses durable ledger plus existing snapshot/audit APIs only.
    - **Window Contract:** includes `window_spec` (`start_index`, `end_index`, `max_events`, `applied_start_index`, `applied_end_index`, `applied_event_count`) and `window_event_count`.
    - **Index Rules:** `start_index` is inclusive, `end_index` is exclusive, and `max_events` is applied after index bounds are resolved.
    - **Honest Failure:** invalid bounds fail closed with explicit reason/warnings; empty slices remain explicit and do not broaden queries.
    - **Bucket Consistency:** preserves v1.4 bucket meanings (`audit_state_counts`, `capture_reason_counts`, `recoverability_counts`, per-event-type breakdown).
    - **Guardrails:** read-only only; no mutation, no repair, no retrofit/backfill, no inference from current family state.
    - **v1.5 Limits:** still no payload compaction and no historical reconstruction.
30. **Event-Order Bounded Capture Quality Summary v1.6:** Read-only windowed observability over transition-event capture quality using `event_order` bounds.
    - **Event-Order Summary API:** `get_pressure_capture_quality_summary_event_order_window(start_event_order=None, end_event_order=None, max_events=None)`.
    - **Mode:** `summary_mode=LEDGER_READ_ONLY_EVENT_ORDER_WINDOWED`; reads durable ledger plus existing snapshot/audit APIs only.
    - **Order Window Contract:** includes `window_spec` (`start_event_order`, `end_event_order`, `max_events`, `applied_start_event_order`, `applied_end_event_order`, `applied_event_count`) and `window_event_count`.
    - **Order Rules:** `start_event_order` inclusive, `end_event_order` inclusive.
    - **Selection Domain:** only transition events with usable numeric `event_order`; non-usable orders are excluded with explicit warnings.
    - **Determinism:** ordered by `(event_order asc, transition-ledger-sequence asc)` for stable tie handling on duplicate `event_order` values.
    - **Bounds Behavior:** invalid bounds fail closed without broadening; `max_events` applies after event-order filtering.
    - **Bucket Consistency:** preserves v1.4/v1.5 bucket meanings and per-event-type breakdown semantics.
    - **Guardrails:** read-only only; no mutation, no repair, no retrofit/backfill, no inference from current family state.
    - **v1.6 Limits:** still no payload compaction and no historical reconstruction.
31. **Window Comparator Summary v1.7:** Read-only side-by-side comparison between index-window (v1.5) and event-order-window (v1.6) capture summaries.
    - **Comparator API:** `get_pressure_capture_quality_window_comparator(start_index=None, end_index=None, index_max_events=None, start_event_order=None, end_event_order=None, event_order_max_events=None)`.
    - **Mode:** `comparison_mode=LEDGER_READ_ONLY_WINDOW_COMPARATOR`.
    - **Outputs:** request spec, both raw window summaries, comparison deltas, mismatch flags, warnings, and explanation lines.
    - **Delta Direction:** all numeric deltas are `event_order_window - index_window`.
    - **Mismatch Semantics:** mismatch flags indicate summary differences between selection methods; they do not imply corruption.
    - **Availability Handling:** reports index/event-order unavailable states explicitly, including both-unavailable conditions.
    - **Bucket Consistency:** reuses v1.4/v1.5/v1.6 bucket meanings without reinterpretation.
    - **Guardrails:** strictly read-only; no mutation, no repair, no retrofit/backfill, no inference from current family state.
    - **v1.7 Limits:** no compaction, no historical reconstruction, comparator is count-based only.
32. **Observability Consistency / Stage Lock v1.8:** Read-only consistency-and-freeze audit for observability surfaces v1.4-v1.7.
    - **Stage-Lock API:** `get_observability_stage_lock_audit()`.
    - **Mode:** `audit_mode=OBSERVABILITY_STAGE_LOCK`.
    - **Lock States:** `OBSERVABILITY_STAGE_LOCKED`, `OBSERVABILITY_STAGE_LOCK_INCONSISTENT`, `OBSERVABILITY_STAGE_LOCK_UNAVAILABLE`.
    - **Core Checks:** v1.4 vs full-range v1.5 consistency, comparator side agreement with direct v1.5/v1.6 outputs, bucket-surface stability, read-only guardrail flag integrity, known unavailable-case honesty, and comparator delta-direction/math consistency.
    - **Contract Surface:** reports required API presence, preserved bucket surfaces, preserved window semantics, and comparator delta direction (`event_order_window - index_window`).
    - **Guardrails:** strictly read-only; no mutation, no repair, no retrofit/backfill, no inference from current family state.
    - **v1.8 Limits:** stage-lock audit only; no new trend/analytics endpoints, no payload compaction.
33. **Cross-Band Self-Check Audit v1.0a:** Read-only single-event directional honesty check across already-earned topology, pressure, and transition outcome surfaces.
    - **Cross-Band API:** `get_transition_cross_band_self_check(event_id)`.
    - **Mode:** `audit_mode=CROSS_BAND_SELF_CHECK`.
    - **Self-Check States:** `CROSS_BAND_ALIGNMENT_OBSERVED`, `CROSS_BAND_CONTRADICTION_OBSERVED`, `CROSS_BAND_PARTIAL`, `CROSS_BAND_UNAVAILABLE`.
    - **Evidence Posture:** uses recoverable event-linked pressure snapshot plus adjacent transition topology audit only; does not reconstruct missing historical state from current family records.
    - **Directional Contract (Tightened):** pressure signal classes are distinct (`SPLIT_ORIENTED`, `STABLE`, `STRETCHED`, `UNCLEAR`, `MIXED`, `UNCLASSIFIED`, `UNAVAILABLE`); `STRETCHED`/`UNCLEAR` do not auto-align reunion or fission outcomes.
    - **Precedence Contract:** unsupported/no-directional-evidence -> `UNAVAILABLE`; trusted pressure contradiction -> `CONTRADICTION_OBSERVED`; trusted pressure alignment -> `ALIGNMENT_OBSERVED`; otherwise recoverable weak/adjacent-only evidence -> `PARTIAL`.
    - **Topology Restraint:** adjacent topology contradiction remains a low-confidence note and cannot by itself harden overall state to `CONTRADICTION_OBSERVED`.
    - **Guardrails:** strictly read-only; no mutation, no repair, no retrofit/backfill, no prediction semantics.
    - **v1.0a Limits:** single-event scope only, no trend summaries, no historical reconstruction engine.
34. **Bounded Multi-Event Cross-Band Consistency Sampler v1.1:** Read-only bounded count sampler over per-event cross-band self-check outputs.
    - **Summary API:** `get_cross_band_self_check_summary_window(start_index=None, end_index=None, max_events=None)`.
    - **Mode:** `summary_mode=CROSS_BAND_SELF_CHECK_WINDOW`.
    - **Window Semantics:** `start_index` inclusive, `end_index` exclusive, `max_events` applied after index bounds resolution.
    - **Count Surfaces:** `self_check_state_counts`, `contradiction_flag_counts`, and normalized `event_type_counts` over selected transition events.
    - **Composition Rule:** counts are composed directly from `get_transition_cross_band_self_check(event_id)` outputs; no duplicated directional logic.
    - **Guardrails:** strictly read-only; no mutation, no repair, no retrofit/backfill, no historical reconstruction, no trend semantics.
    - **v1.1 Limits:** bounded count sampling only; no trend endpoint and no semantic interpretation.
35. **Cross-Band Self-Check Event-Order Window v1.2:** Read-only event_order-bounded count sampler over per-event cross-band self-check outputs.
    - **Summary API:** `get_cross_band_self_check_summary_event_order_window(start_event_order=None, end_event_order=None, max_events=None)`.
    - **Mode:** `summary_mode=CROSS_BAND_SELF_CHECK_EVENT_ORDER_WINDOW`.
    - **Window Semantics:** `start_event_order` inclusive, `end_event_order` inclusive, `max_events` applied after event_order filtering.
    - **Eligibility Domain:** transition events with usable finite numeric `event_order`; ineligible records are excluded with explicit warnings.
    - **Determinism:** selected by `(event_order asc, transition-ledger-sequence asc)` for stable tie behavior.
    - **Count Surfaces:** `self_check_state_counts`, `contradiction_flag_counts`, normalized `event_type_counts`, plus `total_event_order_eligible_events`.
    - **Composition Rule:** counts are composed directly from `get_transition_cross_band_self_check(event_id)` outputs; no duplicated directional logic.
    - **Guardrails:** strictly read-only; no mutation, no repair, no retrofit/backfill, no historical reconstruction, no trend semantics.
    - **v1.2 Limits:** event_order-window parity only; no comparator logic and no trend endpoint.
36. **Cross-Band Window Comparator v1.3:** Read-only side-by-side comparison between cross-band index-window (v1.1) and event_order-window (v1.2) summaries.
    - **Comparator API:** `get_cross_band_self_check_window_comparator(start_index=None, end_index=None, index_max_events=None, start_event_order=None, end_event_order=None, event_order_max_events=None)`.
    - **Mode:** `comparison_mode=CROSS_BAND_WINDOW_COMPARATOR`.
    - **Outputs:** request spec, both raw window summaries, comparison deltas, mismatch flags, warnings, and explanation lines.
    - **Delta Direction:** all numeric deltas are `event_order_window - index_window`.
    - **Mismatch Semantics:** mismatches represent selection/count differences between methods, not data corruption claims.
    - **Availability Handling:** index/event_order unavailable states are preserved explicitly, including both-unavailable outcomes.
    - **Bucket Consistency:** preserves v1.0a/v1.1/v1.2 bucket meanings without reinterpretation.
    - **Guardrails:** strictly read-only; no mutation, no repair, no retrofit/backfill, no inference from current family state.
    - **v1.3 Limits:** comparator remains bounded count comparison only; no trend or calibration semantics.

## Project Structure
- `src/qd_perception/`: Core logic and data models.
- `tests/`: Automated regression suite.
- `runs/`: Output artifacts (future audit logs).

### Running Comparison Demo
To compare the semantic vs structural bridges:
```powershell
$env:PYTHONPATH = "src"
python src/qd_perception/bridge_comparison_demo.py
```

## Development
- **No external dependencies:** Uses standard Python library only.
- **Source Layout:** Imports follow the `qd_perception` package root.

### Running Tests
To run the full suite:
```powershell
$env:PYTHONPATH = "src"
pytest tests/
```

### Running the Demo
To see the system in action:
```powershell
$env:PYTHONPATH = "src"
python src/qd_perception/demo_perception.py
```

### Running Family Transition Demos
```powershell
$env:PYTHONPATH = "src"
python src/qd_perception/family_v8_fission_demo.py
python src/qd_perception/family_v9_reunion_demo.py
python src/qd_perception/family_v10_event_ledger_demo.py
python src/qd_perception/family_v11_ancestry_demo.py
python src/qd_perception/family_v12_lineage_integrity_audit_demo.py
python src/qd_perception/family_v13_dossier_demo.py
python src/qd_perception/family_v14_transition_report_demo.py
python src/qd_perception/family_v15_geometry_fit_demo.py
python src/qd_perception/family_v16_topology_audit_demo.py
python src/qd_perception/family_v17_pressure_forecast_demo.py
python src/qd_perception/family_v18_transition_pressure_snapshot_demo.py
python src/qd_perception/family_v19_event_write_pressure_capture_demo.py
python src/qd_perception/family_v20_pressure_capture_audit_demo.py
python src/qd_perception/family_v21_capture_quality_summary_demo.py
python src/qd_perception/family_v22_capture_quality_window_demo.py
python src/qd_perception/family_v23_capture_quality_event_order_window_demo.py
python src/qd_perception/family_v24_window_comparator_demo.py
python src/qd_perception/family_v25_observability_stage_lock_demo.py
python src/qd_perception/family_v26_cross_band_self_check_demo.py
python src/qd_perception/family_v27_cross_band_self_check_window_demo.py
python src/qd_perception/family_v28_cross_band_self_check_patch_demo.py
python src/qd_perception/family_v29_cross_band_self_check_event_order_window_demo.py
python src/qd_perception/family_v30_cross_band_window_comparator_demo.py
```
