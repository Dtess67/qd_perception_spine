# EXPERIMENTAL_FOUNDATION

This is not a history summary. This document is the empirical inheritance bridge for Phase II and defines measurement obligations the perception spine will be held against.

## Scope and Constraint

- This document governs empirical inheritance, not governance philosophy.
- External attractor classification may be used in Phase I as observation scaffolding only.
- External classifier output must not control the system.
- External classifier output must not define training targets.
- External classifier output must not substitute for internally earned attractor detection.

## Source Resolution Notes

- PrimordialSoupLab primary source:
  - Originally requested path: `X:\Dev\PrimordialSoupLab\polarity_grid_sim.py`
  - Actual inspected path: `X:\Dev\QD_Main\PrimordialSoupLab\polarity_grid_sim.py`
  - Originally requested path present: no
  - Resolution: the actual inspected path is the empirical source used for this draft; resolved in Phase I by source recovery.
- QD_v3 tri-polar source:
  - Originally requested path: `X:\Dev\QD_Main\QD_v3\tri_polar_map.py`
  - Actual inspected path: `X:\Dev\QD_Main\QD_v3\src\qd_simplex\tri_polar_map.py`
  - Originally requested path present: no
  - Resolution: the actual inspected path is the empirical source used for this draft; resolved in Phase I by source recovery.
- QD_v3 constraint bootstrap source:
  - Originally requested path: `X:\Dev\QD_Main\QD_v3\constraint_bootstrap_v1.py` (or nearest `constraint_bootstrap_v1*`)
  - Actual inspected path: none found
  - Originally requested path present: no
  - Resolution state: remains bounded pending unavailable source recovery.

## Source Systems

### PrimordialSoupLab

Source used:
- Requested path `X:\Dev\PrimordialSoupLab\polarity_grid_sim.py` was not present.
- Located and used: `X:\Dev\QD_Main\PrimordialSoupLab\polarity_grid_sim.py`
- Adjacent metrics/output note used: `X:\Dev\QD_Main\PrimordialSoupLab\README.md` (limited; does not define detailed metric semantics).
- Resolution status: requested-vs-actual path discrepancy resolved in Phase I by source recovery.

#### Anchor: 9 founders / lineage inheritance
- Status: **Demonstrated**
- Demonstrated phenomenon or observation: `--agents` defaults to `9`; founders initialize with `lineage=i`; reproduction creates child with `lineage=a.lineage`.
- Why it matters: founder count and lineage continuity are explicit empirical levers for inheritance tracking.
- Perception-spine measurement obligation: preserve identity continuity across split/replication events and keep lineage traceable in state outputs.
- How to test it: create seeded runs with reproduction enabled; verify child entities inherit lineage ID and lineage continuity is auditable over time.
- What is lost if absent: no reliable inheritance map; inability to distinguish structural novelty from lineage continuation.

#### Anchor: memory layer `M`
- Status: **Demonstrated**
- Demonstrated phenomenon or observation: optional global pathway memory field `M` exists (`--use-memory`), initialized, written by agents (`mem_write`), decayed (`mem_decay`), and logged (`mem_absmean`, `mem_absmax`).
- Why it matters: substrate state includes path-history effects beyond instantaneous field values.
- Perception-spine measurement obligation: represent persistent path-history influence as a measurable substrate component, not just instantaneous local state.
- How to test it: run matched seeds with and without memory; compare trajectory and summary-metric divergence under identical non-memory parameters.
- What is lost if absent: no measurable substrate entrenchment channel; reduced ability to detect history-shaped dynamics.

#### Anchor: `--mem-beta` as entrenchment / memory-retention control
- Status: **Demonstrated**
- Demonstrated phenomenon or observation: movement score explicitly includes memory term `mem = mem_beta * (-p) * M_neighbor`.
- Why it matters: entrenchment strength is parameterized and testable, not implicit.
- Perception-spine measurement obligation: include tunable coupling-weight observability for history terms that influence movement/selection dynamics.
- How to test it: parameter sweep on memory coupling while holding seed and other parameters fixed; verify measurable monotonic or regime-shift effects.
- What is lost if absent: inability to measure whether history coupling is load-bearing versus inert.

#### Anchor: `field_absmean`
- Status: **Demonstrated**
- Demonstrated phenomenon or observation: per-tick logging includes `field_absmean = mean(abs(F))` as an explicit substrate intensity metric.
- Why it matters: signed mean alone (`field_mean`) can hide high-energy cancellation; absolute field intensity captures global substrate pressure.
- Perception-spine measurement obligation: track both signed bias and absolute substrate intensity as distinct channels; do not collapse them into one scalar.
- How to test it: construct cases where signed mean is near zero but absolute magnitude remains high; verify the spine marks these as high-intensity unresolved states.
- What is lost if absent: false-neutral readings under opposing high-magnitude structure; missed pressure and premature certainty.

#### Anchor: attractor/world differences across seeds
- Status: **Observed but not yet replicated**
- Demonstrated phenomenon or observation: source supports split seeding (`seed`, `terrain_seed`, `founder_seed`) and writes seed metadata, enabling world/founder variation analysis.
- Why it matters: seed dependence is an explicit part of empirical reproducibility and attractor variability analysis.
- Perception-spine measurement obligation: enforce a seed-partitioned reproducibility matrix (base seed, terrain seed, founder seed) as a required measurement dimension for regime claims.
- How to test it: run controlled seed matrix and compute cross-seed regime signatures from the same metric contract.
- What is lost if absent: inability to separate robust structure from seed-specific artifacts.

#### Anchor: population-memory coupling
- Status: **Demonstrated**
- Demonstrated phenomenon or observation: agents write to memory and subsequently read memory during move scoring; coupling is bidirectional and time-extended.
- Why it matters: population dynamics and substrate memory are jointly causal, not independent layers.
- Perception-spine measurement obligation: detect and preserve two-way coupling between entity behavior and persistent substrate traces.
- How to test it: ablation test of write-path and read-path independently; verify coupled behavior degrades when either side is removed.
- What is lost if absent: inability to represent feedback loops that drive entrenchment and path dependence.

### Oscillator / Entrainment Work

Primary source used:
- `X:\Dev\QD_Main\QD_Nursery\lattice_playground\simplex_chorus_v4.py`

Secondary corroboration used only for clarification:
- `X:\Dev\QD_Main\QD_Nursery\lattice_playground\chorus_tests\chorus_entrainment.py`
- `X:\Dev\QD_Main\QD_Nursery\lattice_playground\chorus_tests\chorus_run.py`
- `X:\Dev\QD_Main\QD_Nursery\lattice_playground\simplex_chorus_v3.py`

In this source family, `coh`, `sect_coh_*`, `mu`, `var`, `energy`, and state counts are directly computed/logged metrics, while entrainment and propagation descriptions are inferred from those telemetry trajectories and update mechanisms.

#### Anchor: entrainment
- Status: **Observed but not yet replicated**
- Demonstrated phenomenon or observation: primary source defines cross-region and local coupling that can drive mutual alignment; secondary `chorus_entrainment.py` explicitly defines group-center pull and identity retention.
- Why it matters: Phase II needs a measurable notion of convergence pressure under coupling, not only static classification.
- Perception-spine measurement obligation: compute and track alignment-convergence signals over time (global and sector-local), with explicit residual divergence.
- How to test it: run coupled vs uncoupled ablations and measure convergence rate/plateau differences.
- What is lost if absent: no way to distinguish coordinated emergence from unstructured fluctuation.

#### Anchor: synchronization
- Status: **Demonstrated**
- Demonstrated phenomenon or observation: primary source logs global coherence (`coh`), sector coherence (`sect_coh_*`), energy, and state counts under repeated updates.
- Why it matters: synchronization is operationalized as measurable time-series, not only visual impression.
- Perception-spine measurement obligation: expose multi-scale coherence metrics (global + local) and preserve their temporal trajectories.
- How to test it: verify coherence trajectories differ under parameter sweeps and remain reproducible under fixed seeds.
- What is lost if absent: no objective synchronization evidence; impossible to audit claims of coordinated state formation.

#### Anchor: traveling-wave or propagation behavior
- Status: **Observed but not yet replicated**
- Demonstrated phenomenon or observation: local-neighbor plus sector-coupling updates provide a mechanism for spatial propagation, but no explicit traveling-wave detector is implemented in the inspected files.
- Why it matters: propagation-like structure can be present without global consensus and must be measured separately.
- Perception-spine measurement obligation: add propagation-sensitive metrics (e.g., lagged spatial correlation or front-tracking proxies) before treating wave behavior as established.
- How to test it: introduce localized perturbations and evaluate directional spread signatures over ticks.
- What is lost if absent: blind spot for structured transit dynamics that are neither static nor globally synchronized.

#### Anchor: coupling / damping dependence
- Status: **Demonstrated**
- Demonstrated phenomenon or observation: primary source exposes coupling and damping-like controls (`beta`, `beta_prime`, `gamma`, noise schedule), all directly in update equations.
- Why it matters: regime behavior is parameter-dependent and therefore falsifiable.
- Perception-spine measurement obligation: preserve parameter-sensitivity testing as a first-class requirement for canonical detectors.
- How to test it: controlled sweeps across coupling/memory/noise parameters with fixed seeds; quantify metric response surfaces.
- What is lost if absent: inability to distinguish genuine structural dynamics from single-setting artifacts.

#### Anchor: equilibrium-class differences
- Status: **Observed but not yet replicated**
- Demonstrated phenomenon or observation: primary source produces metric sets sufficient to separate candidate regimes (high/low coherence, energy bands, state-count distributions), but does not define formal equilibrium classes.
- Why it matters: class boundaries must be earned from measurable behavior, not naming.
- Perception-spine measurement obligation: define class thresholds only after multi-run validation on existing metrics.
- How to test it: cluster run outcomes across seed/parameter grid and evaluate stability of class assignments.
- What is lost if absent: no disciplined way to separate stable, metastable, and unstable operating regions.

### QD_v3

Source used:
- Requested path `X:\Dev\QD_Main\QD_v3\tri_polar_map.py` was not present.
- Located and used: `X:\Dev\QD_Main\QD_v3\src\qd_simplex\tri_polar_map.py`
- `X:\Dev\QD_Main\QD_v3\src\qd_kernel\resonance_metrics_logger.py`
- Resolution status: tri-polar path discrepancy resolved in Phase I by source recovery.

Constraint bootstrap source status:
- `X:\Dev\QD_Main\QD_v3\constraint_bootstrap_v1.py` not present.
- No `constraint_bootstrap_v1*` file located in `X:\Dev\QD_Main\QD_v3` (recursive search).
- HOLD: constraint-bootstrap inheritance cannot be reconstructed from inspected files.
- Resolution mechanism: remains bounded pending unavailable source recovery; target state is resolved in Phase I by source recovery.

#### Contribution: tri-polar structural mapping
- Status: **Demonstrated**
- Demonstrated phenomenon or observation: explicit thresholded mapping to `-1/0/+1` using a shared polarity threshold constant.
- Why it matters: provides a deterministic coarse-state abstraction from continuous inputs.
- Perception-spine measurement obligation: any tri-state collapse must remain traceable to pre-collapse values and explicit thresholds.
- How to test it: threshold-boundary tests around negative/positive cutoff and polarity-transition audit logs.
- What is lost if absent: no stable, auditable collapse rule for scalar-to-state mapping.

#### Contribution: resonance measurement logging
- Status: **Demonstrated**
- Demonstrated phenomenon or observation: logger writes per-axis rows including raw value, v2-adjusted value, delta, v1 polarity, v2 polarity, with scenario labels and timestamps.
- Why it matters: supports comparative measurement and drift auditing between baseline and adjusted pathways.
- Perception-spine measurement obligation: preserve paired raw-vs-adjusted logging and polarity transition visibility in measurement surfaces.
- How to test it: inject controlled axis values and verify exact row contract and expected polarity deltas.
- What is lost if absent: no auditable bridge between raw substrate readings and transformed decision inputs.

#### Insufficiency: silent fallback/variability risk in measurement path
- Status: **Observed but not yet replicated**
- Demonstrated phenomenon or observation: logger dynamically discovers optional kernel functions and falls back to identity adjustment/local polarity when absent.
- Why it matters: behavior may vary by runtime/module availability unless explicitly surfaced and tested.
- Perception-spine measurement obligation: runtime mode (full kernel vs fallback) must be explicit and test-gated, not silent.
- How to test it: run with and without optional kernel helpers; require mode flag and contract-consistent output checks.
- What is lost if absent: hidden behavioral drift and unverifiable cross-environment equivalence.

#### Rebuild motivation detail from inspected files
- Status: **Open reconstruction item**
- Demonstrated phenomenon or observation: inspected QD_v3 files do not provide a complete, explicit rebuild rationale; missing `constraint_bootstrap_v1*` blocks part of reconstruction.
- Why it matters: rebuild causes must be evidence-backed to avoid repeating failure modes.
- Perception-spine measurement obligation: carry unresolved legacy gaps as explicit HOLDs until source-complete reconstruction is available.
- How to test it: recover missing constraint-bootstrap artifacts or authoritative replacement and re-run inheritance mapping.
- What is lost if absent: incomplete failure-memory and risk of reintroducing known-but-undocumented defects.
- Resolution mechanism: remains bounded pending unavailable source recovery; target state is resolved in Phase I by source recovery.

## Metric Inheritance Crosswalk

| Source file | Source metric / mechanism | Derived obligation |
| --- | --- | --- |
| `X:\Dev\QD_Main\PrimordialSoupLab\polarity_grid_sim.py` | `field_absmean` (with `field_mean`) | Track signed substrate bias and absolute substrate intensity as separate channels. |
| `X:\Dev\QD_Main\PrimordialSoupLab\polarity_grid_sim.py` | Global memory field `M` with write/read/decay (`mem_absmean`, `mem_absmax`) | Measure persistent path-history influence on transitions; preserve bidirectional population-memory coupling. |
| `X:\Dev\QD_Main\PrimordialSoupLab\polarity_grid_sim.py` | `mem_beta` movement score term (`mem = mem_beta * (-p) * M_neighbor`) | Require tunable coupling-weight observability and parameter-sensitivity testing for history coupling. |
| `X:\Dev\QD_Main\QD_Nursery\lattice_playground\simplex_chorus_v4.py` | `coh` | Track global synchronization trajectory as an auditable time-series. |
| `X:\Dev\QD_Main\QD_Nursery\lattice_playground\simplex_chorus_v4.py` | `sect_coh_*` | Track sector-local synchronization to avoid hiding local fragmentation behind global aggregates. |
| `X:\Dev\QD_Main\QD_v3\src\qd_kernel\resonance_metrics_logger.py` | `raw_value`, `v2_adjusted_value`, `delta_value`, `v1_polarity`, `v2_polarity` | Preserve raw-vs-adjusted measurement visibility and polarity-transition auditing; prevent silent transform drift. |

## Derived Perception-Spine Measurement Obligations

1. **Obligation:** Track signed substrate bias and absolute substrate intensity as separate channels.  
   **Source basis:** `polarity_grid_sim.py` logs both `field_mean` and `field_absmean`.  
   **Status of source basis:** Demonstrated.  
   **Example test path:** zero-mean/high-abs synthetic and replay cases; verify distinct state outcomes.  
   **Failure consequence:** high-conflict/high-pressure states collapse into false neutral.

2. **Obligation:** Preserve lineage continuity across split/replication transitions.  
   **Source basis:** founder lineage assignment and child lineage inheritance in `polarity_grid_sim.py`.  
   **Status of source basis:** Demonstrated.  
   **Example test path:** reproduction scenario with lineage audits across generations.  
   **Failure consequence:** no auditable identity continuity; inheritance claims become non-falsifiable.

3. **Obligation:** Measure and expose persistent memory-field influence on local transition choice.  
   **Source basis:** `M` write/read/decay and `mem_beta` movement coupling in `polarity_grid_sim.py`.  
   **Status of source basis:** Demonstrated.  
   **Example test path:** memory on/off plus mem_beta sweep under fixed seeds.  
   **Failure consequence:** path dependence disappears from measurement, masking entrenchment dynamics.

4. **Obligation:** Enforce seed-partitioned reproducibility as a mandatory measurement axis for any regime claim.  
   **Source basis:** split-seed controls and run metadata in `polarity_grid_sim.py`.  
   **Status of source basis:** Observed but not yet replicated.  
   **Example test path:** fixed parameter grid with systematic `(seed, terrain_seed, founder_seed)` sweeps and regime-signature reproducibility checks.  
   **Failure consequence:** cannot separate robust detectors from seed artifacts.

5. **Obligation:** Track multi-scale synchronization (global and sector-local) over time.  
   **Source basis:** `simplex_chorus_v4.py` metrics (`coh`, `sect_coh_*`, `energy`, counts).  
   **Status of source basis:** Demonstrated.  
   **Example test path:** coupled/uncoupled and noise-schedule comparisons with identical seeds.  
   **Failure consequence:** coordination claims become qualitative and unauditable.

6. **Obligation:** Require parameter-sensitivity tests for coupling and damping-like controls before canonizing detectors.  
   **Source basis:** explicit `beta`, `beta_prime`, `gamma`, `eta`, `p_blue` controls in `simplex_chorus_v4.py`.  
   **Status of source basis:** Demonstrated.  
   **Example test path:** structured sweeps with metric response-surface checks.  
   **Failure consequence:** architecture may overfit one regime and fail under slight perturbation.

7. **Obligation:** Add propagation-sensitive measurement before claiming wave behavior as canonical.  
   **Source basis:** propagation mechanism exists in `simplex_chorus_v4.py`, but no explicit wave detector in inspected files.  
   **Status of source basis:** Observed but not yet replicated.  
   **Example test path:** localized perturbation experiments with lagged spatial-correlation analysis.  
   **Failure consequence:** propagation dynamics remain invisible and can be misclassified as noise or static drift.

8. **Obligation:** Preserve raw vs adjusted resonance measurement with explicit polarity-transition auditing.  
   **Source basis:** `resonance_metrics_logger.py` row contract (`raw_value`, `v2_adjusted_value`, `delta_value`, `v1_polarity`, `v2_polarity`).  
   **Status of source basis:** Demonstrated.  
   **Example test path:** deterministic axis fixtures at threshold boundaries with expected delta/polarity assertions.  
   **Failure consequence:** transformation drift cannot be detected or attributed.

9. **Obligation:** Expose and test fallback runtime modes as first-class measurement states.  
   **Source basis:** optional function discovery and silent fallbacks in `resonance_metrics_logger.py`.  
   **Status of source basis:** Observed but not yet replicated.  
   **Example test path:** kernel-present vs kernel-absent runs must emit explicit mode and pass mode-specific contracts.  
   **Failure consequence:** silent environment-dependent behavior undermines reproducibility and trust.

10. **Obligation:** Keep unresolved legacy constraint-bootstrap inheritance as explicit HOLD until recoverable.  
    **Source basis:** missing `constraint_bootstrap_v1*` in inspected QD_v3 files.  
    **Status of source basis:** Open reconstruction item.  
    **Example test path:** locate artifact or authoritative replacement; then derive and validate explicit constraints mapping.  
    **Failure consequence:** rebuild proceeds with undocumented constraint gaps and repeat-risk.  
    **Resolution mechanism:** remains bounded pending unavailable source recovery; target state is resolved in Phase I by source recovery.

## Non-Obligations / What This Document Does Not Yet Claim

- No claim that the current spine already satisfies these obligations.
- No claim that external classifier scaffolding is permanent.
- No claim that every CDS idea is already operationalized.
- No claim that all QD_v3 lessons are fully reconstructed yet.
- No claim that CDS geometry (including triangular bipyramid / cohesion-density-sphere framing) is the only valid structural interpretation of these phenomena.

## Phase II Pressure Criteria

This document should be pressure-tested by asking, for each claimed inheritance element:

- Is the phenomenon real and named?
- Is the measurement obligation concrete?
- Is there a test path?
- Is there meaningful loss if the obligation is absent?
