from unittest.mock import MagicMock

import pytest

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _mem(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("")
    return NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))


def _index_window_summary(*, auditable=3, alignment=3, contradiction=0, partial=0, unavailable=0):
    return {
        "summary_available": True,
        "summary_mode": "CROSS_BAND_SELF_CHECK_WINDOW",
        "reason": "WINDOW_SUMMARY_READY",
        "window_spec": {
            "start_index": 1,
            "end_index": 4,
            "max_events": 10,
            "applied_start_index": 1,
            "applied_end_index": 4,
            "applied_event_count": 3,
        },
        "total_transition_events": 8,
        "window_event_count": 3,
        "auditable_event_count": auditable,
        "self_check_state_counts": {
            "CROSS_BAND_ALIGNMENT_OBSERVED": alignment,
            "CROSS_BAND_CONTRADICTION_OBSERVED": contradiction,
            "CROSS_BAND_PARTIAL": partial,
            "CROSS_BAND_UNAVAILABLE": unavailable,
        },
        "contradiction_flag_counts": {"NO_CONTRADICTION_OBSERVED": alignment},
        "event_type_counts": {"FAMILY_FISSION": 2, "FAMILY_REUNION": 1},
        "warnings": [],
        "explanation_lines": ["Index window summary composed."],
    }


def _event_order_window_summary(
    *,
    auditable=3,
    alignment=3,
    contradiction=0,
    partial=0,
    unavailable=0,
):
    return {
        "summary_available": True,
        "summary_mode": "CROSS_BAND_SELF_CHECK_EVENT_ORDER_WINDOW",
        "reason": "EVENT_ORDER_WINDOW_SUMMARY_READY",
        "window_spec": {
            "start_event_order": 10.0,
            "end_event_order": 30.0,
            "max_events": 10,
            "applied_start_event_order": 10.0,
            "applied_end_event_order": 30.0,
            "applied_event_count": 3,
        },
        "total_transition_events": 8,
        "window_event_count": 3,
        "auditable_event_count": auditable,
        "self_check_state_counts": {
            "CROSS_BAND_ALIGNMENT_OBSERVED": alignment,
            "CROSS_BAND_CONTRADICTION_OBSERVED": contradiction,
            "CROSS_BAND_PARTIAL": partial,
            "CROSS_BAND_UNAVAILABLE": unavailable,
        },
        "contradiction_flag_counts": {"NO_CONTRADICTION_OBSERVED": alignment},
        "event_type_counts": {"FAMILY_FISSION": 2, "FAMILY_REUNION": 1},
        "warnings": [],
        "explanation_lines": ["Event-order window summary composed."],
    }


def _comparator_ok():
    return {
        "comparison_available": True,
        "comparison_mode": "CROSS_BAND_WINDOW_COMPARATOR",
        "reason": "WINDOW_SUMMARIES_MATCH",
        "mismatch_flags": ["NO_MISMATCH_DETECTED"],
        "warnings": [],
    }


def _comparator_mismatch():
    return {
        "comparison_available": True,
        "comparison_mode": "CROSS_BAND_WINDOW_COMPARATOR",
        "reason": "WINDOW_SUMMARIES_DIFFER",
        "mismatch_flags": ["WINDOW_COUNT_MISMATCH"],
        "warnings": [],
    }


def test_index_window_review_ready_path(tmp_path):
    mem = _mem(tmp_path)
    bounded = _index_window_summary()
    mem.get_cross_band_self_check_summary_window = MagicMock(return_value=bounded)
    mem.get_cross_band_self_check_window_comparator = MagicMock(return_value=_comparator_ok())

    out = mem.get_cross_band_evidence_review_summary_window(start_index=1, end_index=4, max_events=10)

    assert out["review_available"] is True
    assert out["review_mode"] == "CROSS_BAND_EVIDENCE_REVIEW_WINDOW"
    assert out["review_state"] == "CROSS_BAND_EVIDENCE_REVIEW_READY"
    assert out["review_reason"] == "BOUNDED_ALIGNMENT_OBSERVED_WITH_AUDITABLE_SURFACE"
    assert out["window_spec"] == bounded["window_spec"]
    assert out["evidence_scope"]["scope_equivalence"] == "BOUNDED_NOT_FULL_RANGE_EQUIVALENT"


def test_index_window_review_partial_path(tmp_path):
    mem = _mem(tmp_path)
    mem.get_cross_band_self_check_summary_window = MagicMock(
        return_value=_index_window_summary(auditable=3, alignment=2, contradiction=1)
    )
    mem.get_cross_band_self_check_window_comparator = MagicMock(return_value=_comparator_ok())

    out = mem.get_cross_band_evidence_review_summary_window(start_index=1, end_index=4, max_events=10)

    assert out["review_state"] == "CROSS_BAND_EVIDENCE_REVIEW_PARTIAL"
    assert out["review_reason"] == "BOUNDED_MIXED_OR_LIMITED_EVIDENCE_SURFACE"


def test_index_window_unavailable_when_required_source_missing(tmp_path, monkeypatch):
    mem = _mem(tmp_path)
    monkeypatch.setattr(mem, "get_cross_band_self_check_summary_window", None)

    out = mem.get_cross_band_evidence_review_summary_window(start_index=0, end_index=1, max_events=1)

    assert out["review_available"] is False
    assert out["review_state"] == "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE"
    assert out["review_reason"] == "REQUIRED_SURFACE_MISSING"


@pytest.mark.parametrize(
    "summary, expected_state, expected_reason",
    [
        (
            _event_order_window_summary(),
            "CROSS_BAND_EVIDENCE_REVIEW_READY",
            "BOUNDED_ALIGNMENT_OBSERVED_WITH_AUDITABLE_SURFACE",
        ),
        (
            _event_order_window_summary(auditable=3, alignment=1, partial=2),
            "CROSS_BAND_EVIDENCE_REVIEW_PARTIAL",
            "BOUNDED_MIXED_OR_LIMITED_EVIDENCE_SURFACE",
        ),
    ],
)
def test_event_order_window_ready_and_partial_paths(
    tmp_path,
    summary,
    expected_state,
    expected_reason,
):
    mem = _mem(tmp_path)
    mem.get_cross_band_self_check_summary_event_order_window = MagicMock(return_value=summary)
    mem.get_cross_band_self_check_window_comparator = MagicMock(return_value=_comparator_ok())

    out = mem.get_cross_band_evidence_review_summary_event_order_window(
        start_event_order=10.0,
        end_event_order=30.0,
        max_events=10,
    )

    assert out["review_mode"] == "CROSS_BAND_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW"
    assert out["review_state"] == expected_state
    assert out["review_reason"] == expected_reason


def test_event_order_window_unavailable_when_required_source_missing(tmp_path, monkeypatch):
    mem = _mem(tmp_path)
    monkeypatch.setattr(mem, "get_cross_band_self_check_summary_event_order_window", None)

    out = mem.get_cross_band_evidence_review_summary_event_order_window(
        start_event_order=1.0,
        end_event_order=2.0,
        max_events=5,
    )

    assert out["review_available"] is False
    assert out["review_state"] == "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE"
    assert out["review_reason"] == "REQUIRED_SURFACE_MISSING"


def test_no_hidden_dependency_outside_allowed_windowed_surfaces(tmp_path, monkeypatch):
    mem = _mem(tmp_path)
    mem.get_cross_band_self_check_summary_window = MagicMock(return_value=_index_window_summary())
    mem.get_cross_band_self_check_summary_event_order_window = MagicMock(
        return_value=_event_order_window_summary()
    )
    mem.get_cross_band_self_check_window_comparator = MagicMock(return_value=_comparator_ok())

    def _forbidden(*_args, **_kwargs):
        raise AssertionError("forbidden hidden dependency")

    monkeypatch.setattr(mem, "get_cross_band_evidence_review_summary", _forbidden)
    monkeypatch.setattr(mem, "get_observability_evidence_review_summary", _forbidden)
    monkeypatch.setattr(mem, "get_system_evidence_review_summary", _forbidden)
    monkeypatch.setattr(mem, "get_system_lock_gate_posture", _forbidden)

    out_index = mem.get_cross_band_evidence_review_summary_window()
    out_event = mem.get_cross_band_evidence_review_summary_event_order_window()

    assert out_index["review_state"] == "CROSS_BAND_EVIDENCE_REVIEW_READY"
    assert out_event["review_state"] == "CROSS_BAND_EVIDENCE_REVIEW_READY"


@pytest.mark.parametrize(
    "fn_name, kwargs, summary_builder",
    [
        (
            "get_cross_band_evidence_review_summary_window",
            {"start_index": 1, "end_index": 4, "max_events": 10},
            _index_window_summary,
        ),
        (
            "get_cross_band_evidence_review_summary_event_order_window",
            {"start_event_order": 10.0, "end_event_order": 30.0, "max_events": 10},
            _event_order_window_summary,
        ),
    ],
)
def test_guardrail_flags_false_and_window_spec_preserved(
    tmp_path,
    fn_name,
    kwargs,
    summary_builder,
):
    mem = _mem(tmp_path)
    summary = summary_builder()
    if summary["summary_mode"] == "CROSS_BAND_SELF_CHECK_WINDOW":
        mem.get_cross_band_self_check_summary_window = MagicMock(return_value=summary)
    else:
        mem.get_cross_band_self_check_summary_event_order_window = MagicMock(return_value=summary)
    mem.get_cross_band_self_check_window_comparator = MagicMock(return_value=_comparator_ok())

    out = getattr(mem, fn_name)(**kwargs)

    assert out["window_spec"] == summary["window_spec"]
    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False


@pytest.mark.parametrize(
    "fn_name, kwargs, summary_builder",
    [
        (
            "get_cross_band_evidence_review_summary_window",
            {"start_index": 1, "end_index": 4, "max_events": 10},
            _index_window_summary,
        ),
        (
            "get_cross_band_evidence_review_summary_event_order_window",
            {"start_event_order": 10.0, "end_event_order": 30.0, "max_events": 10},
            _event_order_window_summary,
        ),
    ],
)
def test_comparator_is_supporting_context_not_posture_predicate(
    tmp_path,
    fn_name,
    kwargs,
    summary_builder,
):
    mem = _mem(tmp_path)
    summary = summary_builder()
    if summary["summary_mode"] == "CROSS_BAND_SELF_CHECK_WINDOW":
        mem.get_cross_band_self_check_summary_window = MagicMock(return_value=summary)
    else:
        mem.get_cross_band_self_check_summary_event_order_window = MagicMock(return_value=summary)

    mem.get_cross_band_self_check_window_comparator = MagicMock(return_value=_comparator_ok())
    out_match = getattr(mem, fn_name)(**kwargs)

    mem.get_cross_band_self_check_window_comparator = MagicMock(return_value=_comparator_mismatch())
    out_mismatch = getattr(mem, fn_name)(**kwargs)

    assert out_match["review_state"] == out_mismatch["review_state"]
    assert out_match["review_reason"] == out_mismatch["review_reason"]
    assert "COMPARATOR_CONTEXT_MISMATCH_FLAGS_PRESENT" in out_mismatch["warnings"]
