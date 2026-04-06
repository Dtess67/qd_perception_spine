# QD Decision Loop Prototype v0.0 - Manual Trace Resolver Plan

## Purpose
Define the smallest honest executable prototype plan that resolves explicit manual traces into output classes without autonomy, persistence, or hidden coupling.

## Scope (v0.0)
- Manual-input only.
- Deterministic resolution flow.
- No runtime coupling to existing evidence/consumer surfaces.
- No persistence, no background learning, no automatic invocation.

## Recommended Implementation Location (If Implemented)
- `src/qd_perception/decision_loop_prototype_v0_0.py`

Reason:
- Keeps prototype isolated from `neutral_family_memory_v1.py`.
- Prevents accidental coupling into locked evidence/consumer contracts.

## Recommended Prototype Shape
- Primary shape: pure function + lightweight typed records.
- No class hierarchy needed at v0.0.

Suggested callable:
- `resolve_manual_decision_trace_v0_0(trace_input: ManualTraceInputV0) -> ManualTraceResolutionV0`

## Minimal Manual Input Structure
`ManualTraceInputV0` should include exactly these required fields:
- `delta_description: str`
- `minus_branch_strength: BranchStrength`
- `plus_branch_strength: BranchStrength`
- `past_recall_status: TemporalStatus`
- `future_projection_status: TemporalStatus`
- `substrate_status: SubstrateStatus`
- `corrective_suppression_status: CorrectiveSuppressionStatus`
- `contradiction_pressure: ContradictionPressure`
- `prior_state_quality: PriorStateQuality`

Optional field for explicit conditional traces:
- `conditions: list[str]` (default empty)

### Enum Sets (Qualitative, No Numeric Certainty Theater)
- `BranchStrength`:
  - `none`
  - `weak`
  - `moderate`
  - `strong`
- `TemporalStatus`:
  - `minus_aligned`
  - `plus_aligned`
  - `mixed`
  - `sparse`
  - `conflicting`
- `SubstrateStatus`:
  - `usable`
  - `degraded`
  - `collapse_blocking`
- `CorrectiveSuppressionStatus`:
  - `advisory`
  - `caution_inducing`
  - `collapse_blocking`
- `ContradictionPressure`:
  - `low`
  - `medium`
  - `high`
  - `blocking`
- `PriorStateQuality`:
  - `strong`
  - `moderate`
  - `weak`
  - `missing`

## Minimal Resolver Output Structure
`ManualTraceResolutionV0` should include:
- `output_class: OutputClass`
- `resolution_reason: str`
- `applied_rules: list[str]`
- `blockers: list[str]`
- `conditions_used: list[str]`
- `input_echo: dict`

`OutputClass` values:
- `resolved_minus_1`
- `resolved_plus_1`
- `conditional_answer`
- `limited_caution_answer`
- `external_hold`

## Step-by-step Resolution Flow (Deterministic)
1. Validate shape and enum membership for all required fields.
2. Fail closed to `external_hold` on hard blockers:
   - `substrate_status == collapse_blocking`
   - `corrective_suppression_status == collapse_blocking`
   - `contradiction_pressure == blocking`
3. Compute directional candidate:
   - Candidate `minus` if minus strength exceeds plus strength and temporal signals do not strongly contradict `minus`.
   - Candidate `plus` if plus strength exceeds minus strength and temporal signals do not strongly contradict `plus`.
   - Otherwise no stable candidate.
4. Apply projection guardrail:
   - Strong future projection may support a candidate.
   - Projection cannot independently earn resolved output when past recall is `sparse` or `conflicting`.
5. Apply caution pressure modifiers:
   - `substrate_status == degraded` raises collapse strictness.
   - `corrective_suppression_status == caution_inducing` raises collapse strictness.
   - `prior_state_quality in {weak, missing}` raises collapse strictness.
6. Resolve class:
   - `resolved_minus_1` or `resolved_plus_1` only if candidate remains strong after strictness modifiers and non-blocking contradiction.
   - `conditional_answer` if candidate exists but requires explicit conditions to remain honest.
   - `limited_caution_answer` if signal exists but candidate is not stable enough for resolved.
   - `external_hold` if no meaningful non-blocked posture remains.
7. Return structured decision with explicit rule trail (`applied_rules`) and blockers.

## What Is Hard-coded vs Parameterized in v0.0
- Hard-coded:
  - Enum vocabularies.
  - Decision precedence/order.
  - Guardrail rules (blocking states force hold).
- Parameterized:
  - Manual trace values per case.
  - Optional explicit conditions list for conditional outputs.

## Hand-crafted Example Cases
### Case A - Resolved `-1`
- Input:
  - `minus_branch_strength=strong`
  - `plus_branch_strength=weak`
  - `past_recall_status=minus_aligned`
  - `future_projection_status=mixed`
  - `substrate_status=usable`
  - `corrective_suppression_status=advisory`
  - `contradiction_pressure=low`
  - `prior_state_quality=strong`
- Expected output:
  - `resolved_minus_1`

### Case B - Conditional Answer
- Input:
  - `minus_branch_strength=moderate`
  - `plus_branch_strength=strong`
  - `past_recall_status=sparse`
  - `future_projection_status=plus_aligned`
  - `substrate_status=degraded`
  - `corrective_suppression_status=caution_inducing`
  - `contradiction_pressure=medium`
  - `prior_state_quality=moderate`
  - `conditions=[\"projection-dependent\", \"requires substrate recovery\"]`
- Expected output:
  - `conditional_answer`

### Case C - External HOLD
- Input:
  - `minus_branch_strength=strong`
  - `plus_branch_strength=moderate`
  - `past_recall_status=minus_aligned`
  - `future_projection_status=plus_aligned`
  - `substrate_status=collapse_blocking`
  - `corrective_suppression_status=advisory`
  - `contradiction_pressure=high`
  - `prior_state_quality=strong`
- Expected output:
  - `external_hold`

### Optional Case D - Limited/Caution
- Input:
  - `minus_branch_strength=moderate`
  - `plus_branch_strength=moderate`
  - `past_recall_status=mixed`
  - `future_projection_status=mixed`
  - `substrate_status=usable`
  - `corrective_suppression_status=caution_inducing`
  - `contradiction_pressure=medium`
  - `prior_state_quality=weak`
- Expected output:
  - `limited_caution_answer`

## Explicit Non-goals (v0.0)
- No persistence or record storage.
- No autonomous or adaptive learning behavior.
- No automatic use of durable-ledger audits or corrective-learning mappings.
- No integration into existing evidence/consumer APIs.
- No confidence scoring theater beyond qualitative classes.

## Deferred to Later Versions
- Explicit calibration spec for branch-strength tie-breaks.
- Contract for optional persistence/write-path (if ever approved).
- Runtime coupling policy to durable-ledger/corrective artifacts.
- Any batch or automatic invocation entrypoint.
