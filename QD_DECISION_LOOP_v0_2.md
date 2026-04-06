# QD Decision Loop v0.2 - Resolution Criteria Draft

## Name
QD Decision Loop v0.2

## One-line Definition
Question -> Delta Split -> Polarity Evaluation -> Temporal Assessment -> Resolution

## HOLD Distinction
- Internal HOLD zone:
  - Active contact plane/synthesis region created by polarity split.
  - Work zone where tension is evaluated and collapsed only when earned.
- External HOLD output:
  - Final output node used when collapse criteria are not earned.
  - Wait/retry posture pending new delta/evidence.

## Delta Ingress (What It Does)
- Delta Ingress performs a combined intake function:
  - change detection between current question context and prior known context,
  - normalization of detected changes into explicit decision-comparable deltas,
  - prior-state comparison anchoring for downstream assessment.
- Prior-state/context role:
  - strengthens confidence in delta framing when grounded context exists.
- Weak or missing prior state:
  - ingress remains valid but flagged as weaker-context intake.
  - collapse thresholds should be treated as stricter, biasing toward limited/caution or external HOLD.

## Resolution Criteria (Collapse vs Block)
### What earns collapse out of internal HOLD zone
- Polarity-consistent evidence signal is present and non-contradictory at the evaluated scope.
- Temporal assessment returns usable grounded recall and projection context (even if asymmetric).
- Contradictions are bounded and explainable without hiding uncertainty.
- Dominant branch strength is sufficient for one of the non-HOLD output classes.

### What blocks collapse
- Insufficient evidence density after normalization.
- Unresolved contradiction across polarity branches in the active zone.
- Weak/missing prior context plus low-quality temporal support.
- Temporal asymmetry is too large to support honest branch commitment.

## Output-class Criteria
### resolved -1
- Internal HOLD collapse favors the `-1` polarity branch.
- `-1` evidence dominates with acceptable contradiction bounds.
- Temporal assessment does not invalidate `-1` dominance.

### resolved +1
- Internal HOLD collapse favors the `+1` polarity branch.
- `+1` evidence dominates with acceptable contradiction bounds.
- Temporal assessment does not invalidate `+1` dominance.

### conditional answer
- Collapse is earned, but branch commitment depends on explicit condition(s) that are surfaced.
- Condition set is narrow and testable; uncertainty remains bounded.

### limited/caution answer
- Directional signal exists, but quality/coverage is not strong enough for full answer confidence.
- Used when honesty requires explicit limitation rather than binary commitment.

### external HOLD
- Collapse not earned under current delta/evidence quality.
- Resolution node outputs HOLD and waits for new delta/evidence before retry.

## Evidence Weighting Notes
- Past Outcome Recall:
  - Grounded memory path; treated as stronger evidence weight.
- Future Outcome Projection:
  - Softer inference path; treated as lower evidence weight unless strongly anchored.
- Asymmetry rule:
  - Projection may support but should not override grounded recall when they conflict.
  - Large recall/projection mismatch biases toward limited/caution or external HOLD.

## Re-entry Behavior
- Internal HOLD zone does not "re-enter"; it is the active chamber itself.
- Re-entry occurs only from external HOLD when new delta/evidence appears.

## Relationship To Existing Build
- Durable ledger integrity audit = substrate truth check:
  - `get_durable_transition_ledger_integrity_audit()`
- Corrective learning artifacts = remembered wrongness inputs:
  - `CorrectiveLearningRecordV1a`
  - `get_corrective_learning_record_contract_v1a()`
  - `validate_corrective_learning_record_v1a(...)`
  - `build_corrective_learning_record_v1a(...)`
  - `format_corrective_learning_record_v1a(...)`
  - `map_durable_ledger_audit_findings_to_corrective_records_v1_2(...)`
- Decision loop remains spec-only in this step and is not runtime-coupled.

## Explicit Non-goals (v0.2 draft)
- No runtime implementation yet.
- No autonomous decision logic yet.
- No coupling into existing evidence/consumer surfaces yet.
- No confidence/posture rewrite behavior yet.
