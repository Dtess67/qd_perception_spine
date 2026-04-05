from unittest.mock import MagicMock

import pytest

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _mem(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("")
    return NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))


def _index_window_summary(*, auditable=3, valid=3, invalid=0, unavailable=0):
    return {
        "summary_available": True,
        "summary_mode": "LEDGER_READ_ONLY_WINDOWED",
        "reason": "OK",
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
        "pressure_snapshot_present_count": 3,
        "pressure_snapshot_missing_count": 0,
        "audit_state_counts": {
            "PRESSURE_CAPTURE_AUDIT_VALID": valid,
            "PRESSURE_CAPTURE_AUDIT_INVALID": invalid,
            "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": unavailable,
        },
        "capture_reason_counts": {
            "PRESSURE_CAPTURE_FULL": 2,
            "PRESSURE_CAPTURE_PARTIAL": 1,
            "PRESSURE_CAPTURE_FAILED": 0,
            "UNRECOGNIZED_CAPTURE_REASON": 0,
        },
        "recoverability_counts": {
            "FULLY_RECOVERABLE": 2,
            "PARTIALLY_RECOVERABLE": 1,
            "UNRECOVERABLE": 0,
        },
        "event_type_counts": {"FAMILY_FISSION": 2, "FAMILY_REUNION": 1},
        "warnings": [],
        "explanation_lines": ["Index observability window summary composed."],
    }


def _event_order_window_summary(*, auditable=3, valid=3, invalid=0, unavailable=0):
    return {
        "summary_available": True,
        "summary_mode": "LEDGER_READ_ONLY_EVENT_ORDER_WINDOWED",
        "reason": "OK",
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
        "pressure_snapshot_present_count": 3,
        "pressure_snapshot_missing_count": 0,
        "audit_state_counts": {
            "PRESSURE_CAPTURE_AUDIT_VALID": valid,
            "PRESSURE_CAPTURE_AUDIT_INVALID": invalid,
            "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": unavailable,
        },
        "capture_reason_counts": {
            "PRESSURE_CAPTURE_FULL": 2,
            "PRESSURE_CAPTURE_PARTIAL": 1,
            "PRESSURE_CAPTURE_FAILED": 0,
            "UNRECOGNIZED_CAPTURE_REASON": 0,
        },
        "recoverability_counts": {
            "FULLY_RECOVERABLE": 2,
            "PARTIALLY_RECOVERABLE": 1,
            "UNRECOVERABLE": 0,
        },
        "event_type_counts": {"FAMILY_FISSION": 2, "FAMILY_REUNION": 1},
        "warnings": [],
        "explanation_lines": ["Event-order observability window summary composed."],
    }


def _comparator_ok():
    return {
        "comparison_available": True,
        "comparison_mode": "LEDGER_READ_ONLY_WINDOW_COMPARATOR",
        "reason": "WINDOW_SUMMARIES_MATCH",
        "mismatch_flags": ["NO_MISMATCH_DETECTED"],
        "warnings": [],
    }


def _comparator_mismatch():
    return {
        "comparison_available": True,
        "comparison_mode": "LEDGER_READ_ONLY_WINDOW_COMPARATOR",
        "reason": "WINDOW_SUMMARIES_DIFFER",
        "mismatch_flags": ["WINDOW_COUNT_MISMATCH"],
        "warnings": [],
    }


def test_index_window_review_ready_path(tmp_path):
    mem = _mem(tmp_path)
    bounded = _index_window_summary()
    mem.get_pressure_capture_quality_summary_window = MagicMock(return_value=bounded)
    mem.get_pressure_capture_quality_window_comparator = MagicMock(return_value=_comparator_ok())

    out = mem.get_observability_evidence_review_summary_window(start_index=1, end_index=4, max_events=10)

    assert out["review_available"] is True
    assert out["review_mode"] == "OBSERVABILITY_EVIDENCE_REVIEW_WINDOW"
    assert out["review_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_READY"
    assert out["review_reason"] == "BOUNDED_FULLY_AUDITABLE_OBSERVABILITY_EVIDENCE"
    assert out["window_spec"] == bounded["window_spec"]
    assert out["evidence_scope"]["scope_equivalence"] == "BOUNDED_NOT_FULL_RANGE_EQUIVALENT"


def test_index_window_review_partial_path(tmp_path):
    mem = _mem(tmp_path)
    mem.get_pressure_capture_quality_summary_window = MagicMock(
        return_value=_index_window_summary(auditable=3, valid=2, invalid=1, unavailable=0)
    )
    mem.get_pressure_capture_quality_window_comparator = MagicMock(return_value=_comparator_ok())

    out = mem.get_observability_evidence_review_summary_window(start_index=1, end_index=4, max_events=10)

    assert out["review_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_PARTIAL"
    assert out["review_reason"] == "BOUNDED_LIMITED_OR_MIXED_OBSERVABILITY_EVIDENCE"


def test_index_window_unavailable_when_required_source_missing(tmp_path, monkeypatch):
    mem = _mem(tmp_path)
    monkeypatch.setattr(mem, "get_pressure_capture_quality_summary_window", None)

    out = mem.get_observability_evidence_review_summary_window(start_index=0, end_index=1, max_events=1)

    assert out["review_available"] is False
    assert out["review_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE"
    assert out["review_reason"] == "REQUIRED_SURFACE_MISSING"


@pytest.mark.parametrize(
    "summary, expected_state, expected_reason",
    [
        (
            _event_order_window_summary(),
            "OBSERVABILITY_EVIDENCE_REVIEW_READY",
            "BOUNDED_FULLY_AUDITABLE_OBSERVABILITY_EVIDENCE",
        ),
        (
            _event_order_window_summary(auditable=3, valid=1, invalid=1, unavailable=1),
            "OBSERVABILITY_EVIDENCE_REVIEW_PARTIAL",
            "BOUNDED_LIMITED_OR_MIXED_OBSERVABILITY_EVIDENCE",
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
    mem.get_pressure_capture_quality_summary_event_order_window = MagicMock(return_value=summary)
    mem.get_pressure_capture_quality_window_comparator = MagicMock(return_value=_comparator_ok())

    out = mem.get_observability_evidence_review_summary_event_order_window(
        start_event_order=10.0,
        end_event_order=30.0,
        max_events=10,
    )

    assert out["review_mode"] == "OBSERVABILITY_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW"
    assert out["review_state"] == expected_state
    assert out["review_reason"] == expected_reason


def test_event_order_window_unavailable_when_required_source_missing(tmp_path, monkeypatch):
    mem = _mem(tmp_path)
    monkeypatch.setattr(mem, "get_pressure_capture_quality_summary_event_order_window", None)

    out = mem.get_observability_evidence_review_summary_event_order_window(
        start_event_order=1.0,
        end_event_order=2.0,
        max_events=5,
    )

    assert out["review_available"] is False
    assert out["review_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE"
    assert out["review_reason"] == "REQUIRED_SURFACE_MISSING"


def test_no_hidden_dependency_outside_allowed_windowed_surfaces(tmp_path, monkeypatch):
    mem = _mem(tmp_path)
    mem.get_pressure_capture_quality_summary_window = MagicMock(return_value=_index_window_summary())
    mem.get_pressure_capture_quality_summary_event_order_window = MagicMock(
        return_value=_event_order_window_summary()
    )
    mem.get_pressure_capture_quality_window_comparator = MagicMock(return_value=_comparator_ok())

    def _forbidden(*_args, **_kwargs):
        raise AssertionError("forbidden hidden dependency")

    monkeypatch.setattr(mem, "get_observability_evidence_review_summary", _forbidden)
    monkeypatch.setattr(mem, "get_observability_stage_lock_audit", _forbidden)
    monkeypatch.setattr(mem, "get_cross_band_evidence_review_summary", _forbidden)
    monkeypatch.setattr(mem, "get_system_evidence_review_summary", _forbidden)
    monkeypatch.setattr(mem, "get_system_lock_gate_posture", _forbidden)

    out_index = mem.get_observability_evidence_review_summary_window()
    out_event = mem.get_observability_evidence_review_summary_event_order_window()

    assert out_index["review_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_READY"
    assert out_event["review_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_READY"


@pytest.mark.parametrize(
    "fn_name, kwargs, summary_builder",
    [
        (
            "get_observability_evidence_review_summary_window",
            {"start_index": 1, "end_index": 4, "max_events": 10},
            _index_window_summary,
        ),
        (
            "get_observability_evidence_review_summary_event_order_window",
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
    if summary["summary_mode"] == "LEDGER_READ_ONLY_WINDOWED":
        mem.get_pressure_capture_quality_summary_window = MagicMock(return_value=summary)
    else:
        mem.get_pressure_capture_quality_summary_event_order_window = MagicMock(return_value=summary)
    mem.get_pressure_capture_quality_window_comparator = MagicMock(return_value=_comparator_ok())

    out = getattr(mem, fn_name)(**kwargs)

    assert out["window_spec"] == summary["window_spec"]
    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False


@pytest.mark.parametrize(
    "fn_name, kwargs, summary_builder",
    [
        (
            "get_observability_evidence_review_summary_window",
            {"start_index": 1, "end_index": 4, "max_events": 10},
            _index_window_summary,
        ),
        (
            "get_observability_evidence_review_summary_event_order_window",
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
    if summary["summary_mode"] == "LEDGER_READ_ONLY_WINDOWED":
        mem.get_pressure_capture_quality_summary_window = MagicMock(return_value=summary)
    else:
        mem.get_pressure_capture_quality_summary_event_order_window = MagicMock(return_value=summary)

    mem.get_pressure_capture_quality_window_comparator = MagicMock(return_value=_comparator_ok())
    out_match = getattr(mem, fn_name)(**kwargs)

    mem.get_pressure_capture_quality_window_comparator = MagicMock(return_value=_comparator_mismatch())
    out_mismatch = getattr(mem, fn_name)(**kwargs)

    assert out_match["review_state"] == out_mismatch["review_state"]
    assert out_match["review_reason"] == out_mismatch["review_reason"]
    assert "COMPARATOR_CONTEXT_MISMATCH_FLAGS_PRESENT" in out_mismatch["warnings"]
