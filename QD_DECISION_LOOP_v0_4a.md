# QD Decision Loop v0.4a - Ambiguity Closure Notes

## Name
QD Decision Loop v0.4a

## One-line Definition
Question -> Delta Split -> Polarity Evaluation -> Temporal Assessment -> Resolution

## Scope
- Narrow ambiguity-closure addendum to v0.4 worked traces.
- Spec-only; no runtime behavior and no coupling changes.

## 1) Conditional Answer vs Limited/Caution Answer Boundary
- `conditional answer`:
  - A directional collapse candidate exists (`-1` or `+1`) and remains non-blocked.
  - The output depends on explicit, named condition(s) that are inspectable.
  - Conditions are the reason for non-finality, not absence of directional structure.
- `limited/caution answer`:
  - Direction exists only as weak or mixed tendency, not as a stable collapse candidate.
  - Limitation comes from evidence quality or contradiction pressure, not from explicit external conditions alone.
  - Output is caution-first posture, not condition-first posture.

## 2) When Strong Projection Supports vs Upgrades Toward Resolved
- Strong projection may support collapse when it reinforces an already-grounded branch signal.
- Strong projection may not, by itself, upgrade to resolved when grounded recall is weak, contradictory, or substrate quality is degraded.
- Projection can legitimately help upgrade toward resolved only when all are true:
  - grounded recall is at least minimally coherent with the same branch,
  - substrate is not in collapse-blocking state,
  - corrective-learning suppression is not collapse-blocking,
  - contradiction pressure is non-blocking.

## 3) Qualitative Substrate Degradation Bands
- `usable`:
  - Substrate integrity does not force downgrade.
  - Resolved collapse remains eligible if other criteria are earned.
- `degraded`:
  - Reliability penalty applies.
  - Resolved collapse requires stronger grounded support; otherwise route to conditional or limited/caution.
- `collapse-blocking`:
  - Substrate integrity is insufficient for honest collapse.
  - External HOLD is forced regardless of directional projection strength.

## 4) Qualitative Corrective-learning Suppression Bands
- `advisory`:
  - Adds caution context but does not block collapse by itself.
- `caution-inducing`:
  - Suppresses aggressive collapse.
  - Biases outcome toward conditional or limited/caution unless branch dominance is strongly grounded.
- `collapse-blocking`:
  - Active remembered-wrongness risk is severe enough to block collapse.
  - External HOLD is required until new evidence/delta reduces suppression pressure.

## Closure Precedence (Draft)
- If substrate band is `collapse-blocking` -> external HOLD.
- Else if corrective-learning band is `collapse-blocking` -> external HOLD.
- Else if directional collapse candidate exists but depends on explicit conditions -> conditional answer.
- Else if directional signal remains mixed/weak under caution pressure -> limited/caution answer.
- Else resolved output remains eligible under v0.2/v0.3 criteria.

## Relationship To Existing Build
- Durable ledger integrity audit anchors substrate trust context:
  - `get_durable_transition_ledger_integrity_audit()`
- Corrective-learning artifacts anchor suppression context:
  - `CorrectiveLearningRecordV1a`
  - `get_corrective_learning_record_contract_v1a()`
  - `validate_corrective_learning_record_v1a(...)`
  - `build_corrective_learning_record_v1a(...)`
  - `format_corrective_learning_record_v1a(...)`
  - `map_durable_ledger_audit_findings_to_corrective_records_v1_2(...)`

## Explicit Non-goals (v0.4a)
- no runtime implementation
- no tests required for this spec-only closure pass
- no autonomous decision logic
- no coupling into current evidence/consumer runtime surfaces
