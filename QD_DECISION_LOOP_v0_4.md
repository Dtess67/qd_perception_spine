# QD Decision Loop v0.4 - Worked Decision Traces

## Name
QD Decision Loop v0.4

## One-line Definition
Question -> Delta Split -> Polarity Evaluation -> Temporal Assessment -> Resolution

## Scope
- Declarative worked examples only.
- No executable logic and no runtime coupling.

## Trace 1 - Strong Past Recall / Weak Projection
### Input / Delta
- Input question: classify polarity under familiar recurring pattern.
- Delta ingress result: low novelty, high prior-state match.

### Polarity Split
- `-1` branch: strong aligned prior outcomes.
- `+1` branch: weak support.

### Internal HOLD State
- Active chamber enters low contradiction tension.

### Past Recall Contribution
- High-confidence grounded recall strongly favors `-1`.

### Future Projection Contribution
- Weak projection signal, slightly noisy, not contradictory.

### Substrate Integrity Contribution
- Substrate quality healthy; no degradation penalty.

### Corrective-learning Contribution
- No relevant remembered wrongness pressure for this pattern.

### Collapse vs Block Rationale
- Collapse earned because branch dominance is clear and contradiction pressure is low.

### Output Class
- resolved `-1`

---

## Trace 2 - Weak Past Recall / Strong Projection
### Input / Delta
- Input question: evaluate emerging pattern with limited grounded history.
- Delta ingress result: medium novelty, weak prior-state anchor.

### Polarity Split
- `-1` branch: weak grounded support.
- `+1` branch: strong projected support.

### Internal HOLD State
- Active chamber has moderate contradiction due to recall/projection asymmetry.

### Past Recall Contribution
- Weak and sparse; does not strongly support either branch.

### Future Projection Contribution
- Strong but inference-heavy toward `+1`.

### Substrate Integrity Contribution
- Substrate quality healthy.

### Corrective-learning Contribution
- Mild relevance from prior wrongness on similar over-projection episodes.

### Collapse vs Block Rationale
- Full directional collapse is not earned because projection is stronger than grounded recall.
- Honest output remains condition-bound.

### Output Class
- conditional answer

---

## Trace 3 - Substrate Degradation Forcing HOLD
### Input / Delta
- Input question: classify polarity during degraded substrate context.
- Delta ingress result: moderate novelty; prior-state context present but degraded.

### Polarity Split
- `-1` and `+1` both show moderate directional support.

### Internal HOLD State
- Active chamber has unresolved contradiction under degraded substrate trust.

### Past Recall Contribution
- Present, but downgraded by substrate integrity concerns.

### Future Projection Contribution
- Present, but also downgraded and uncertain.

### Substrate Integrity Contribution
- Degraded substrate quality applies strong reliability penalty.

### Corrective-learning Contribution
- Relevant wrongness history warns against collapse under degraded substrate.

### Collapse vs Block Rationale
- Blocked: substrate degradation plus contradiction pressure prevents honest collapse.

### Output Class
- external HOLD

---

## Trace 4 - Corrective-learning Relevance Suppressing Collapse
### Input / Delta
- Input question: classify polarity in a pattern class with repeated prior wrongness.
- Delta ingress result: moderate prior-state match with known wrongness class overlap.

### Polarity Split
- `+1` appears directionally stronger than `-1`.

### Internal HOLD State
- Active chamber retains elevated caution pressure from remembered wrongness relevance.

### Past Recall Contribution
- Mixed: some support for `+1`, but includes prior misclassification history.

### Future Projection Contribution
- Supports `+1`, but inherits caution due to wrongness overlap.

### Substrate Integrity Contribution
- Healthy substrate; no direct degradation block.

### Corrective-learning Contribution
- High relevance; strong suppression of premature collapse.

### Collapse vs Block Rationale
- Directional signal exists, but corrective relevance pressure prevents full resolve.

### Output Class
- limited/caution answer

---

## Trace 5 - Mixed Evidence Producing Limited/Caution Answer
### Input / Delta
- Input question: evaluate polarity with mixed moderate signals and partial context.
- Delta ingress result: partial prior-state anchor, moderate novelty.

### Polarity Split
- `-1` and `+1` both have non-trivial support; no clear dominance.

### Internal HOLD State
- Active chamber has sustained mid-level contradiction.

### Past Recall Contribution
- Moderately supports `-1`.

### Future Projection Contribution
- Moderately supports `+1`.

### Substrate Integrity Contribution
- Substrate mostly healthy but not pristine.

### Corrective-learning Contribution
- Moderate relevance suggests caution on forced binary collapse.

### Collapse vs Block Rationale
- No branch achieves clear honest dominance; contradiction is non-blocking but unresolved.

### Output Class
- limited/caution answer

---

## Ambiguity Notes Exposed by Worked Traces
- Exact threshold for when projection strength may upgrade `conditional` to resolved remains undefined.
- Boundary between `conditional answer` and `limited/caution answer` still requires explicit tie-break criteria.
- Magnitude of substrate degradation required to force external HOLD remains qualitative.
- Corrective-learning suppression severity is still classed qualitatively, not numerically fixed.

## Relationship To Existing Build
- Durable ledger integrity audit anchors substrate trust:
  - `get_durable_transition_ledger_integrity_audit()`
- Corrective-learning artifacts anchor remembered wrongness pressure:
  - `CorrectiveLearningRecordV1a`
  - `get_corrective_learning_record_contract_v1a()`
  - `validate_corrective_learning_record_v1a(...)`
  - `build_corrective_learning_record_v1a(...)`
  - `format_corrective_learning_record_v1a(...)`
  - `map_durable_ledger_audit_findings_to_corrective_records_v1_2(...)`
- Decision-loop traces remain design-only and non-executable.

## Explicit Non-goals (v0.4 draft)
- no runtime implementation
- no autonomous decision logic
- no hidden coupling into existing evidence/consumer code paths
- no executable scoring engine
