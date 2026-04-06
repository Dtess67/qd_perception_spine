# QD Decision Loop v0.1

## Name
QD Decision Loop v0.1

## One-line Definition
Question -> Delta Split -> Polarity Evaluation -> Temporal Assessment -> Resolution

## Stage Definitions
- Question Node
  - Receives the explicit question/input to evaluate.
- Delta Ingress
  - Performs combined change framing:
    - change detection relative to prior state/context
    - normalization into explicit decision-comparable deltas
    - prior-state comparison anchor for assessment
- Polarity Split
  - Evaluates polarity branches explicitly (`-1` / `+1`).
  - Generates the internal HOLD zone (contact plane) where opposing polarity evidence co-exists.
- Assessment Chamber
  - Active tension/synthesis zone (not a post-tension evaluator).
  - Internal HOLD is a zone, not a node.
  - `0` is not null; `0` is the active synthesis / decision-boundary region.
- Past Outcome Recall
  - Lives inside the active internal HOLD zone.
  - Grounded memory path using durable/audit-backed outcomes.
- Future Outcome Projection
  - Lives inside the active internal HOLD zone.
  - Softer inference path using explicit assumptions/projections.
  - Not epistemically symmetric with past recall.
- Resolution Node
  - Collapses earned tension (not mere uncertainty) into one output class.
  - External HOLD is a node, not a zone.

## HOLD Geometry Clarification
- Internal HOLD:
  - shared equilibrium/contact plane where opposing polarity structures meet.
  - active work zone for synthesis and temporal assessment.
- External HOLD:
  - final output state when resolution is not earned with current delta/evidence.
  - return/wait posture until new delta/evidence arrives.

## Output Possibilities
- answer
- conditional answer
- limited/caution answer
- HOLD (external HOLD output node)

## Re-entry Behavior
- Internal HOLD does not re-enter; it is the active chamber where evaluation happens.
- External HOLD re-enters only when new delta/evidence is available for a new loop pass.

## Relationship To Current Build
- durable ledger integrity audit = root-truth substrate check
  - anchor surface: `get_durable_transition_ledger_integrity_audit()`
- corrective learning v1.0a/v1.1/v1.2 = remembered wrongness structure
  - contract: `CorrectiveLearningRecordV1a`
  - contract/validation: `get_corrective_learning_record_contract_v1a()`, `validate_corrective_learning_record_v1a(...)`
  - construction/formatting: `build_corrective_learning_record_v1a(...)`, `format_corrective_learning_record_v1a(...)`
  - mapping: `map_durable_ledger_audit_findings_to_corrective_records_v1_2(...)`
- decision loop = future behavioral control loop that can eventually use those artifacts

## Explicit Non-goals (v0.1)
- not implemented behavior yet
- no runtime coupling yet
- no autonomous learning yet
- no confidence/posture rewrite yet
