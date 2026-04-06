from qd_perception.decision_loop_prototype_v0_0 import (
    ManualTraceInputV0,
    resolve_manual_decision_trace_v0_0,
)


def _base_trace() -> dict:
    return {
        "delta_description": "manual case",
        "minus_branch_strength": "moderate",
        "plus_branch_strength": "weak",
        "past_recall_status": "minus_aligned",
        "future_projection_status": "mixed",
        "substrate_status": "usable",
        "corrective_suppression_status": "advisory",
        "contradiction_pressure": "low",
        "prior_state_quality": "strong",
        "named_conditions": [],
    }


def test_manual_trace_resolver_resolved_minus_1_strong_recall_usable_substrate():
    trace = _base_trace()
    trace["minus_branch_strength"] = "strong"
    trace["plus_branch_strength"] = "weak"
    trace["past_recall_status"] = "minus_aligned"
    trace["substrate_status"] = "usable"
    trace["contradiction_pressure"] = "low"

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] == "resolved_minus_1"
    assert result["collapse_allowed"] is True
    assert result["blocking_reasons"] == []
    assert result["lineage_mutation_performed"] is False
    assert result["event_creation_performed"] is False
    assert result["history_rewrite_performed"] is False


def test_manual_trace_resolver_conditional_projection_strong_sparse_recall_degraded_with_conditions():
    trace = _base_trace()
    trace["minus_branch_strength"] = "moderate"
    trace["plus_branch_strength"] = "strong"
    trace["past_recall_status"] = "sparse"
    trace["future_projection_status"] = "plus_aligned"
    trace["substrate_status"] = "degraded"
    trace["corrective_suppression_status"] = "caution_inducing"
    trace["contradiction_pressure"] = "medium"
    trace["named_conditions"] = ["projection-dependent", "requires substrate recovery"]

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] == "conditional_answer"
    assert result["collapse_allowed"] is False
    assert "PROJECTION_ALONE_UPGRADE_BLOCKED" in result["applied_weight_notes"]


def test_manual_trace_resolver_external_hold_on_collapse_blocking_substrate():
    trace = _base_trace()
    trace["substrate_status"] = "collapse_blocking"
    trace["contradiction_pressure"] = "low"

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] == "external_hold"
    assert result["collapse_allowed"] is False
    assert "SUBSTRATE_COLLAPSE_BLOCKING" in result["blocking_reasons"]


def test_manual_trace_resolver_limited_caution_for_mixed_weak_signals_and_caution_pressure():
    trace = _base_trace()
    trace["minus_branch_strength"] = "weak"
    trace["plus_branch_strength"] = "weak"
    trace["past_recall_status"] = "mixed"
    trace["future_projection_status"] = "mixed"
    trace["corrective_suppression_status"] = "caution_inducing"
    trace["contradiction_pressure"] = "medium"
    trace["prior_state_quality"] = "weak"

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] == "limited_caution_answer"
    assert result["collapse_allowed"] is False
    assert "CAUTION_PRESSURE_ACTIVE" in result["applied_weight_notes"]


def test_manual_trace_resolver_blocks_projection_only_upgrade_to_resolved_plus_1():
    trace = _base_trace()
    trace["minus_branch_strength"] = "weak"
    trace["plus_branch_strength"] = "strong"
    trace["past_recall_status"] = "sparse"
    trace["future_projection_status"] = "plus_aligned"
    trace["substrate_status"] = "degraded"
    trace["contradiction_pressure"] = "low"
    trace["named_conditions"] = []

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] != "resolved_plus_1"
    assert "PROJECTION_ALONE_UPGRADE_BLOCKED" in result["applied_weight_notes"]


def test_manual_trace_resolver_accepts_dataclass_input():
    trace = ManualTraceInputV0(
        delta_description="dataclass case",
        minus_branch_strength="strong",
        plus_branch_strength="weak",
        past_recall_status="minus_aligned",
        future_projection_status="mixed",
        substrate_status="usable",
        corrective_suppression_status="advisory",
        contradiction_pressure="low",
        prior_state_quality="strong",
        named_conditions=[],
    )

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] == "resolved_minus_1"


def test_edge_tieish_branch_pulls_usable_low_contradiction_yields_limited_caution():
    trace = _base_trace()
    trace["minus_branch_strength"] = "moderate"
    trace["plus_branch_strength"] = "moderate"
    trace["past_recall_status"] = "mixed"
    trace["future_projection_status"] = "mixed"
    trace["substrate_status"] = "usable"
    trace["contradiction_pressure"] = "low"

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] == "limited_caution_answer"
    assert result["collapse_allowed"] is False


def test_edge_usable_substrate_with_caution_inducing_suppression_yields_limited_caution():
    trace = _base_trace()
    trace["minus_branch_strength"] = "strong"
    trace["plus_branch_strength"] = "weak"
    trace["past_recall_status"] = "minus_aligned"
    trace["substrate_status"] = "usable"
    trace["corrective_suppression_status"] = "caution_inducing"
    trace["contradiction_pressure"] = "low"

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] == "limited_caution_answer"
    assert "CAUTION_PRESSURE_ACTIVE" in result["applied_weight_notes"]


def test_edge_degraded_substrate_with_strong_grounded_recall_can_still_resolve():
    trace = _base_trace()
    trace["minus_branch_strength"] = "strong"
    trace["plus_branch_strength"] = "weak"
    trace["past_recall_status"] = "minus_aligned"
    trace["future_projection_status"] = "minus_aligned"
    trace["substrate_status"] = "degraded"
    trace["corrective_suppression_status"] = "advisory"
    trace["contradiction_pressure"] = "low"
    trace["prior_state_quality"] = "strong"
    trace["named_conditions"] = []

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] == "resolved_minus_1"
    assert result["collapse_allowed"] is True


def test_edge_strong_projection_with_missing_prior_state_does_not_resolve_plus():
    trace = _base_trace()
    trace["minus_branch_strength"] = "weak"
    trace["plus_branch_strength"] = "strong"
    trace["past_recall_status"] = "sparse"
    trace["future_projection_status"] = "plus_aligned"
    trace["substrate_status"] = "usable"
    trace["prior_state_quality"] = "missing"
    trace["contradiction_pressure"] = "low"
    trace["named_conditions"] = []

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] != "resolved_plus_1"
    assert result["output_class"] == "limited_caution_answer"
    assert "PROJECTION_ALONE_UPGRADE_BLOCKED" in result["applied_weight_notes"]


def test_edge_contradictory_recall_projection_non_blocking_substrate_yields_limited_caution():
    trace = _base_trace()
    trace["minus_branch_strength"] = "weak"
    trace["plus_branch_strength"] = "strong"
    trace["past_recall_status"] = "minus_aligned"
    trace["future_projection_status"] = "plus_aligned"
    trace["substrate_status"] = "usable"
    trace["corrective_suppression_status"] = "advisory"
    trace["contradiction_pressure"] = "low"
    trace["prior_state_quality"] = "strong"
    trace["named_conditions"] = []

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] == "limited_caution_answer"
    assert result["collapse_allowed"] is False


def test_edge_named_conditions_present_vs_absent_for_conditional_trend_case():
    trace_with_conditions = _base_trace()
    trace_with_conditions["minus_branch_strength"] = "moderate"
    trace_with_conditions["plus_branch_strength"] = "strong"
    trace_with_conditions["past_recall_status"] = "sparse"
    trace_with_conditions["future_projection_status"] = "plus_aligned"
    trace_with_conditions["substrate_status"] = "degraded"
    trace_with_conditions["corrective_suppression_status"] = "caution_inducing"
    trace_with_conditions["contradiction_pressure"] = "medium"
    trace_with_conditions["named_conditions"] = ["requires substrate recovery"]

    trace_without_conditions = dict(trace_with_conditions)
    trace_without_conditions["named_conditions"] = []

    result_with_conditions = resolve_manual_decision_trace_v0_0(trace_with_conditions)
    result_without_conditions = resolve_manual_decision_trace_v0_0(trace_without_conditions)

    assert result_with_conditions["output_class"] == "conditional_answer"
    assert result_without_conditions["output_class"] == "limited_caution_answer"


def test_edge_precedence_collapse_blocking_substrate_beats_everything():
    trace = _base_trace()
    trace["substrate_status"] = "collapse_blocking"
    trace["corrective_suppression_status"] = "advisory"
    trace["contradiction_pressure"] = "low"
    trace["minus_branch_strength"] = "strong"
    trace["plus_branch_strength"] = "none"

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] == "external_hold"
    assert result["blocking_reasons"][0] == "SUBSTRATE_COLLAPSE_BLOCKING"


def test_edge_precedence_collapse_blocking_corrective_suppression_beats_non_blocking_inputs():
    trace = _base_trace()
    trace["substrate_status"] = "usable"
    trace["corrective_suppression_status"] = "collapse_blocking"
    trace["contradiction_pressure"] = "low"
    trace["minus_branch_strength"] = "strong"
    trace["plus_branch_strength"] = "none"

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] == "external_hold"
    assert "CORRECTIVE_SUPPRESSION_COLLAPSE_BLOCKING" in result["blocking_reasons"]


def test_edge_underspecified_input_fails_closed():
    trace = _base_trace()
    del trace["past_recall_status"]

    result = resolve_manual_decision_trace_v0_0(trace)

    assert result["output_class"] == "external_hold"
    assert result["collapse_allowed"] is False
    assert "INPUT_INVALID" in result["blocking_reasons"]
    assert result["lineage_mutation_performed"] is False
    assert result["event_creation_performed"] is False
    assert result["history_rewrite_performed"] is False
