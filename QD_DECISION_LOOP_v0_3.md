# QD Decision Loop v0.3 - Branch Weighting / Collapse Heuristics Draft

## Name
QD Decision Loop v0.3

## One-line Definition
Question -> Delta Split -> Polarity Evaluation -> Temporal Assessment -> Resolution

## Internal vs External HOLD
- Internal HOLD zone:
  - active evidence chamber/contact plane where branch tension is synthesized.
  - not an output; this is where weighting and collapse assessment occur.
- External HOLD output:
  - final output node when collapse is not earned honestly.
  - re-entry occurs only when new delta/evidence is available.

## Branch-strength Inputs (-1 and +1)
- `branch_signal_polarity`: directional support inside each branch (`-1` or `+1`).
- `past_recall_support`: grounded memory support aligned with branch.
- `future_projection_support`: projected support aligned with branch.
- `substrate_integrity_support`: support quality adjusted by substrate integrity.
- `corrective_relevance_adjustment`: support penalty/guardrail from remembered wrongness relevance.
- `contradiction_pressure`: opposing/conflicting pressure against branch collapse.

## Evidence Classes
- Grounded past recall:
  - durable/audit-backed memory evidence.
- Future projection:
  - softer inference evidence under stated assumptions.
- Substrate integrity quality:
  - root-truth quality context from durable substrate checks.
- Corrective-learning relevance:
  - remembered wrongness signals relevant to current question/delta class.
- Contradiction pressure:
  - explicit unresolved conflict signal in active chamber.

## Weight Asymmetry Rules
- Grounded recall vs projection:
  - grounded recall has higher trust priority than projection.
  - projection may reinforce but should not override grounded recall on direct conflict.
- Substrate degradation effect:
  - degraded substrate quality reduces usable branch strength and increases collapse strictness.
- Remembered wrongness effect:
  - relevant corrective memory increases caution pressure and reduces premature directional collapse.
  - repeated related wrongness biases toward conditional/limited/external HOLD outcomes.

## Draft Collapse Heuristics
### Earns resolved -1
- `-1` branch strength clearly dominates `+1` after asymmetry and degradation adjustments.
- contradiction pressure remains below blocking threshold.
- no unresolved high-impact guardrail conflict from corrective relevance.

### Earns resolved +1
- `+1` branch strength clearly dominates `-1` after asymmetry and degradation adjustments.
- contradiction pressure remains below blocking threshold.
- no unresolved high-impact guardrail conflict from corrective relevance.

### Earns conditional answer
- directional dominance exists, but depends on explicit condition(s) for honesty.
- condition set is explicit, bounded, and testable.
- contradiction or context weakness is non-zero but not collapse-blocking.

### Earns limited/caution answer
- directional signal exists but is not strong enough for full directional collapse.
- evidence quality is constrained (coverage, substrate quality, or corrective relevance pressure).
- honesty requires explicit limitation over binary commitment.

### Forces external HOLD
- no branch reaches honest dominance after weighting adjustments.
- contradiction pressure remains blocking.
- substrate degradation or prior-state weakness is severe.
- corrective relevance indicates unresolved wrongness risk that blocks safe collapse.

## Weak/Missing Prior-state Behavior
- Prior state/context absent or weak:
  - delta ingress still runs, but with low-context flag.
  - collapse thresholds become stricter.
  - tie/near-tie outcomes bias toward limited/caution or external HOLD.
- Prior state/context strong:
  - branch-strength confidence can increase when aligned with grounded recall and substrate quality.

## Relationship To Existing Build
- Durable ledger integrity audit = substrate truth check:
  - `get_durable_transition_ledger_integrity_audit()`
- Corrective-learning artifacts = remembered wrongness inputs:
  - `CorrectiveLearningRecordV1a`
  - `get_corrective_learning_record_contract_v1a()`
  - `validate_corrective_learning_record_v1a(...)`
  - `build_corrective_learning_record_v1a(...)`
  - `format_corrective_learning_record_v1a(...)`
  - `map_durable_ledger_audit_findings_to_corrective_records_v1_2(...)`
- Decision loop remains spec-only and not runtime-coupled in this draft.

## Explicit Non-goals (v0.3 draft)
- no runtime implementation
- no autonomous decision logic
- no numeric certainty theater unless clearly provisional
- no hidden coupling into existing code paths
