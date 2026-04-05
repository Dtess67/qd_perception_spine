from unittest.mock import MagicMock

import pytest

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _mem(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("")
    return NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))


def _index_window_spec():
    return {
        "start_index": 1,
        "end_index": 4,
        "max_events": 10,
        "applied_start_index": 1,
        "applied_end_index": 4,
        "applied_event_count": 3,
    }


def _event_order_window_spec():
    return {
        "start_event_order": 10.0,
        "end_event_order": 30.0,
        "max_events": 10,
        "applied_start_event_order": 10.0,
        "applied_end_event_order": 30.0,
        "applied_event_count": 3,
    }


def _cross_window_review(*, state, auditable, window_spec):
    return {
        "review_available": True,
        "review_mode": "CROSS_BAND_EVIDENCE_REVIEW_WINDOW",
        "review_state": state,
        "review_reason": "CROSS_REASON",
        "window_spec": dict(window_spec),
        "evidence_scope": {
            "bounded_scope": "INDEX_WINDOW",
            "bounded_summary_mode": "CROSS_BAND_SELF_CHECK_WINDOW",
            "coverage_notes": ["cross coverage"],
            "total_auditable_events": auditable,
        },
        "evidence_counts": {
            "total_auditable_events": auditable,
            "window_event_count": 3,
        },
        "warnings": [],
    }


def _cross_event_order_review(*, state, auditable, window_spec):
    return {
        "review_available": True,
        "review_mode": "CROSS_BAND_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
        "review_state": state,
        "review_reason": "CROSS_EVENT_ORDER_REASON",
        "window_spec": dict(window_spec),
        "evidence_scope": {
            "bounded_scope": "EVENT_ORDER_WINDOW",
            "bounded_summary_mode": "CROSS_BAND_SELF_CHECK_EVENT_ORDER_WINDOW",
            "coverage_notes": ["cross event-order coverage"],
            "total_auditable_events": auditable,
        },
        "evidence_counts": {
            "total_auditable_events": auditable,
            "window_event_count": 3,
        },
        "warnings": [],
    }


def _obs_window_review(*, state, auditable, window_spec):
    return {
        "review_available": True,
        "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW_WINDOW",
        "review_state": state,
        "review_reason": "OBS_REASON",
        "window_spec": dict(window_spec),
        "evidence_scope": {
            "bounded_scope": "INDEX_WINDOW",
            "bounded_summary_mode": "LEDGER_READ_ONLY_WINDOWED",
            "coverage_notes": ["obs coverage"],
            "total_auditable_events": auditable,
        },
        "evidence_counts": {
            "total_auditable_events": auditable,
            "window_event_count": 3,
        },
        "warnings": [],
    }


def _obs_event_order_review(*, state, auditable, window_spec):
    return {
        "review_available": True,
        "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
        "review_state": state,
        "review_reason": "OBS_EVENT_ORDER_REASON",
        "window_spec": dict(window_spec),
        "evidence_scope": {
            "bounded_scope": "EVENT_ORDER_WINDOW",
            "bounded_summary_mode": "LEDGER_READ_ONLY_EVENT_ORDER_WINDOWED",
            "coverage_notes": ["obs event-order coverage"],
            "total_auditable_events": auditable,
        },
        "evidence_counts": {
            "total_auditable_events": auditable,
            "window_event_count": 3,
        },
        "warnings": [],
    }


def test_index_window_sampler_ready_path(tmp_path):
    mem = _mem(tmp_path)
    window_spec = _index_window_spec()
    mem.get_cross_band_evidence_review_summary_window = MagicMock(
        return_value=_cross_window_review(
            state="CROSS_BAND_EVIDENCE_REVIEW_READY",
            auditable=3,
            window_spec=window_spec,
        )
    )
    mem.get_observability_evidence_review_summary_window = MagicMock(
        return_value=_obs_window_review(
            state="OBSERVABILITY_EVIDENCE_REVIEW_READY",
            auditable=3,
            window_spec=window_spec,
        )
    )

    out = mem.get_system_evidence_review_sampler_window(start_index=1, end_index=4, max_events=10)

    assert out["review_available"] is True
    assert out["review_mode"] == "SYSTEM_EVIDENCE_REVIEW_WINDOW"
    assert out["review_state"] == "SYSTEM_EVIDENCE_REVIEW_READY"
    assert out["review_reason"] == "BOUNDED_COMPOSED_EVIDENCE_SURFACES_READY"
    assert out["window_spec"] == window_spec
    assert out["evidence_scope"]["scope_equivalence"] == "BOUNDED_NOT_FULL_RANGE_EQUIVALENT"


def test_index_window_sampler_partial_path(tmp_path):
    mem = _mem(tmp_path)
    window_spec = _index_window_spec()
    mem.get_cross_band_evidence_review_summary_window = MagicMock(
        return_value=_cross_window_review(
            state="CROSS_BAND_EVIDENCE_REVIEW_PARTIAL",
            auditable=2,
            window_spec=window_spec,
        )
    )
    mem.get_observability_evidence_review_summary_window = MagicMock(
        return_value=_obs_window_review(
            state="OBSERVABILITY_EVIDENCE_REVIEW_READY",
            auditable=3,
            window_spec=window_spec,
        )
    )

    out = mem.get_system_evidence_review_sampler_window(start_index=1, end_index=4, max_events=10)

    assert out["review_state"] == "SYSTEM_EVIDENCE_REVIEW_PARTIAL"
    assert out["review_reason"] == "BOUNDED_LIMITED_OR_MIXED_EVIDENCE_SURFACE"


def test_index_window_sampler_unavailable_when_required_source_missing(tmp_path, monkeypatch):
    mem = _mem(tmp_path)
    monkeypatch.setattr(mem, "get_cross_band_evidence_review_summary_window", None)

    out = mem.get_system_evidence_review_sampler_window(start_index=1, end_index=4, max_events=10)

    assert out["review_available"] is False
    assert out["review_state"] == "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"
    assert out["review_reason"] == "REQUIRED_SURFACE_MISSING"


@pytest.mark.parametrize(
    "cross_state,cross_auditable,obs_state,obs_auditable,expected_state,expected_reason",
    [
        (
            "CROSS_BAND_EVIDENCE_REVIEW_READY",
            3,
            "OBSERVABILITY_EVIDENCE_REVIEW_READY",
            3,
            "SYSTEM_EVIDENCE_REVIEW_READY",
            "BOUNDED_COMPOSED_EVIDENCE_SURFACES_READY",
        ),
        (
            "CROSS_BAND_EVIDENCE_REVIEW_PARTIAL",
            2,
            "OBSERVABILITY_EVIDENCE_REVIEW_READY",
            3,
            "SYSTEM_EVIDENCE_REVIEW_PARTIAL",
            "BOUNDED_LIMITED_OR_MIXED_EVIDENCE_SURFACE",
        ),
        (
            "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE",
            0,
            "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE",
            0,
            "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE",
            "NO_MEANINGFUL_BOUNDED_EVIDENCE_SURFACE",
        ),
    ],
)
def test_event_order_window_sampler_ready_partial_unavailable_paths(
    tmp_path,
    cross_state,
    cross_auditable,
    obs_state,
    obs_auditable,
    expected_state,
    expected_reason,
):
    mem = _mem(tmp_path)
    window_spec = _event_order_window_spec()
    mem.get_cross_band_evidence_review_summary_event_order_window = MagicMock(
        return_value=_cross_event_order_review(
            state=cross_state,
            auditable=cross_auditable,
            window_spec=window_spec,
        )
    )
    mem.get_observability_evidence_review_summary_event_order_window = MagicMock(
        return_value=_obs_event_order_review(
            state=obs_state,
            auditable=obs_auditable,
            window_spec=window_spec,
        )
    )

    out = mem.get_system_evidence_review_sampler_event_order_window(
        start_event_order=10.0,
        end_event_order=30.0,
        max_events=10,
    )

    assert out["review_mode"] == "SYSTEM_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW"
    assert out["review_state"] == expected_state
    assert out["review_reason"] == expected_reason


def test_event_order_window_sampler_unavailable_when_required_source_missing(tmp_path, monkeypatch):
    mem = _mem(tmp_path)
    monkeypatch.setattr(mem, "get_observability_evidence_review_summary_event_order_window", None)

    out = mem.get_system_evidence_review_sampler_event_order_window(
        start_event_order=10.0,
        end_event_order=30.0,
        max_events=10,
    )

    assert out["review_available"] is False
    assert out["review_state"] == "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"
    assert out["review_reason"] == "REQUIRED_SURFACE_MISSING"


def test_no_hidden_dependency_outside_allowed_bounded_review_surfaces(tmp_path, monkeypatch):
    mem = _mem(tmp_path)
    index_spec = _index_window_spec()
    event_order_spec = _event_order_window_spec()
    mem.get_cross_band_evidence_review_summary_window = MagicMock(
        return_value=_cross_window_review(
            state="CROSS_BAND_EVIDENCE_REVIEW_READY",
            auditable=2,
            window_spec=index_spec,
        )
    )
    mem.get_observability_evidence_review_summary_window = MagicMock(
        return_value=_obs_window_review(
            state="OBSERVABILITY_EVIDENCE_REVIEW_READY",
            auditable=2,
            window_spec=index_spec,
        )
    )
    mem.get_cross_band_evidence_review_summary_event_order_window = MagicMock(
        return_value=_cross_event_order_review(
            state="CROSS_BAND_EVIDENCE_REVIEW_READY",
            auditable=2,
            window_spec=event_order_spec,
        )
    )
    mem.get_observability_evidence_review_summary_event_order_window = MagicMock(
        return_value=_obs_event_order_review(
            state="OBSERVABILITY_EVIDENCE_REVIEW_READY",
            auditable=2,
            window_spec=event_order_spec,
        )
    )

    def _forbidden(*_args, **_kwargs):
        raise AssertionError("forbidden hidden dependency")

    monkeypatch.setattr(mem, "get_cross_band_self_check_summary_window", _forbidden)
    monkeypatch.setattr(mem, "get_cross_band_self_check_summary_event_order_window", _forbidden)
    monkeypatch.setattr(mem, "get_pressure_capture_quality_summary_window", _forbidden)
    monkeypatch.setattr(mem, "get_pressure_capture_quality_summary_event_order_window", _forbidden)
    monkeypatch.setattr(mem, "get_cross_band_evidence_review_summary", _forbidden)
    monkeypatch.setattr(mem, "get_observability_evidence_review_summary", _forbidden)
    monkeypatch.setattr(mem, "get_system_evidence_review_summary", _forbidden)
    monkeypatch.setattr(mem, "get_system_lock_gate_posture", _forbidden)

    out_index = mem.get_system_evidence_review_sampler_window()
    out_event_order = mem.get_system_evidence_review_sampler_event_order_window()

    assert out_index["review_state"] == "SYSTEM_EVIDENCE_REVIEW_READY"
    assert out_event_order["review_state"] == "SYSTEM_EVIDENCE_REVIEW_READY"


@pytest.mark.parametrize(
    "fn_name,kwargs,cross_builder,obs_builder,window_spec",
    [
        (
            "get_system_evidence_review_sampler_window",
            {"start_index": 1, "end_index": 4, "max_events": 10},
            _cross_window_review,
            _obs_window_review,
            _index_window_spec(),
        ),
        (
            "get_system_evidence_review_sampler_event_order_window",
            {"start_event_order": 10.0, "end_event_order": 30.0, "max_events": 10},
            _cross_event_order_review,
            _obs_event_order_review,
            _event_order_window_spec(),
        ),
    ],
)
def test_guardrail_flags_false_and_window_semantics_preserved(
    tmp_path,
    fn_name,
    kwargs,
    cross_builder,
    obs_builder,
    window_spec,
):
    mem = _mem(tmp_path)
    cross = cross_builder(
        state="CROSS_BAND_EVIDENCE_REVIEW_READY",
        auditable=2,
        window_spec=window_spec,
    )
    obs = obs_builder(
        state="OBSERVABILITY_EVIDENCE_REVIEW_READY",
        auditable=2,
        window_spec=window_spec,
    )
    if "event_order" in fn_name:
        mem.get_cross_band_evidence_review_summary_event_order_window = MagicMock(return_value=cross)
        mem.get_observability_evidence_review_summary_event_order_window = MagicMock(return_value=obs)
    else:
        mem.get_cross_band_evidence_review_summary_window = MagicMock(return_value=cross)
        mem.get_observability_evidence_review_summary_window = MagicMock(return_value=obs)

    out = getattr(mem, fn_name)(**kwargs)

    assert out["window_spec"] == window_spec
    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False


@pytest.mark.parametrize(
    "fn_name,kwargs,cross_api_name,obs_api_name,cross_builder,obs_builder,window_spec",
    [
        (
            "get_system_evidence_review_sampler_window",
            {"start_index": 1, "end_index": 4, "max_events": 10},
            "get_cross_band_evidence_review_summary_window",
            "get_observability_evidence_review_summary_window",
            _cross_window_review,
            _obs_window_review,
            _index_window_spec(),
        ),
        (
            "get_system_evidence_review_sampler_event_order_window",
            {"start_event_order": 10.0, "end_event_order": 30.0, "max_events": 10},
            "get_cross_band_evidence_review_summary_event_order_window",
            "get_observability_evidence_review_summary_event_order_window",
            _cross_event_order_review,
            _obs_event_order_review,
            _event_order_window_spec(),
        ),
    ],
)
def test_full_range_surfaces_not_used_as_posture_predicates(
    tmp_path,
    fn_name,
    kwargs,
    cross_api_name,
    obs_api_name,
    cross_builder,
    obs_builder,
    window_spec,
    monkeypatch,
):
    mem = _mem(tmp_path)
    cross = cross_builder(
        state="CROSS_BAND_EVIDENCE_REVIEW_READY",
        auditable=3,
        window_spec=window_spec,
    )
    obs = obs_builder(
        state="OBSERVABILITY_EVIDENCE_REVIEW_READY",
        auditable=3,
        window_spec=window_spec,
    )
    setattr(mem, cross_api_name, MagicMock(return_value=cross))
    setattr(mem, obs_api_name, MagicMock(return_value=obs))

    full_cross = MagicMock(return_value={"review_state": "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE"})
    full_obs = MagicMock(return_value={"review_state": "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE"})
    full_sys = MagicMock(return_value={"review_state": "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"})
    monkeypatch.setattr(mem, "get_cross_band_evidence_review_summary", full_cross)
    monkeypatch.setattr(mem, "get_observability_evidence_review_summary", full_obs)
    monkeypatch.setattr(mem, "get_system_evidence_review_summary", full_sys)

    out = getattr(mem, fn_name)(**kwargs)

    assert out["review_state"] == "SYSTEM_EVIDENCE_REVIEW_READY"
    full_cross.assert_not_called()
    full_obs.assert_not_called()
    full_sys.assert_not_called()
