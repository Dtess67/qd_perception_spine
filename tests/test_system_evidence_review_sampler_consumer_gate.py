from unittest.mock import MagicMock

import pytest

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _mem(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("")
    return NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))


def _sampler_surface(*, mode: str, state: str, available: bool = True) -> dict:
    return {
        "review_available": available,
        "review_mode": mode,
        "review_state": state,
        "review_reason": "SAMPLER_REASON",
        "window_spec": {"applied_event_count": 3},
        "warnings": [],
        "lineage_mutation_performed": False,
        "event_creation_performed": False,
        "history_rewrite_performed": False,
    }


def _stage_lock_surface(*, mode: str, lock_state: str, audit_available: bool = True) -> dict:
    return {
        "audit_available": audit_available,
        "audit_mode": mode,
        "lock_state": lock_state,
        "reason": "STAGE_LOCK_REASON",
        "warnings": [],
        "lineage_mutation_performed": False,
        "event_creation_performed": False,
        "history_rewrite_performed": False,
    }


def test_consumer_gate_window_rely_happy_path(tmp_path):
    mem = _mem(tmp_path)
    mem.get_system_evidence_review_sampler_window = MagicMock(
        return_value=_sampler_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_WINDOW",
            state="SYSTEM_EVIDENCE_REVIEW_READY",
        )
    )
    mem.get_system_evidence_review_sampler_stage_lock_window = MagicMock(
        return_value=_stage_lock_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_WINDOW",
            lock_state="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_LOCKED",
        )
    )

    out = mem.get_system_evidence_review_sampler_consumer_gate_window(
        start_index=1,
        end_index=4,
        max_events=10,
    )

    assert out["gate_available"] is True
    assert out["gate_mode"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_CONSUMER_GATE_WINDOW"
    assert out["gate_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_GATE_RELY"
    assert out["gate_reason"] == "BOUNDED_SAMPLER_READY_AND_STAGE_LOCKED"
    assert out["consumer_posture"] == "RELY"
    mem.get_system_evidence_review_sampler_window.assert_called_once_with(
        start_index=1,
        end_index=4,
        max_events=10,
    )
    mem.get_system_evidence_review_sampler_stage_lock_window.assert_called_once_with(
        start_index=1,
        end_index=4,
        max_events=10,
    )


def test_consumer_gate_window_limited_path(tmp_path):
    mem = _mem(tmp_path)
    mem.get_system_evidence_review_sampler_window = MagicMock(
        return_value=_sampler_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_WINDOW",
            state="SYSTEM_EVIDENCE_REVIEW_PARTIAL",
        )
    )
    mem.get_system_evidence_review_sampler_stage_lock_window = MagicMock(
        return_value=_stage_lock_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_WINDOW",
            lock_state="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_LOCKED",
        )
    )

    out = mem.get_system_evidence_review_sampler_consumer_gate_window()

    assert out["gate_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_GATE_LIMITED"
    assert out["gate_reason"] == "BOUNDED_SAMPLER_PARTIAL_UNDER_STAGE_LOCK"
    assert out["consumer_posture"] == "LIMITED"


def test_consumer_gate_window_hold_on_unavailable_sampler(tmp_path):
    mem = _mem(tmp_path)
    mem.get_system_evidence_review_sampler_window = MagicMock(
        return_value=_sampler_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_WINDOW",
            state="SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE",
            available=False,
        )
    )
    mem.get_system_evidence_review_sampler_stage_lock_window = MagicMock(
        return_value=_stage_lock_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_WINDOW",
            lock_state="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_LOCKED",
        )
    )

    out = mem.get_system_evidence_review_sampler_consumer_gate_window()

    assert out["gate_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_GATE_HOLD"
    assert out["gate_reason"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_UNAVAILABLE"
    assert out["consumer_posture"] == "HOLD"


def test_consumer_gate_event_order_hold_on_inconsistent_stage_lock(tmp_path):
    mem = _mem(tmp_path)
    mem.get_system_evidence_review_sampler_event_order_window = MagicMock(
        return_value=_sampler_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
            state="SYSTEM_EVIDENCE_REVIEW_READY",
        )
    )
    mem.get_system_evidence_review_sampler_stage_lock_event_order_window = MagicMock(
        return_value=_stage_lock_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_EVENT_ORDER_WINDOW",
            lock_state="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_INCONSISTENT",
        )
    )

    out = mem.get_system_evidence_review_sampler_consumer_gate_event_order_window()

    assert out["gate_mode"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_CONSUMER_GATE_EVENT_ORDER_WINDOW"
    assert out["gate_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_GATE_HOLD"
    assert out["gate_reason"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_INCONSISTENT"
    assert out["consumer_posture"] == "HOLD"


@pytest.mark.parametrize(
    "fn_name,sampler_api,stage_lock_api,sampler_mode,stage_lock_mode,kwargs",
    [
        (
            "get_system_evidence_review_sampler_consumer_gate_window",
            "get_system_evidence_review_sampler_window",
            "get_system_evidence_review_sampler_stage_lock_window",
            "SYSTEM_EVIDENCE_REVIEW_WINDOW",
            "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_WINDOW",
            {"start_index": 1, "end_index": 4, "max_events": 10},
        ),
        (
            "get_system_evidence_review_sampler_consumer_gate_event_order_window",
            "get_system_evidence_review_sampler_event_order_window",
            "get_system_evidence_review_sampler_stage_lock_event_order_window",
            "SYSTEM_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
            "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_EVENT_ORDER_WINDOW",
            {"start_event_order": 10.0, "end_event_order": 30.0, "max_events": 10},
        ),
    ],
)
def test_no_hidden_dependency_outside_allowed_bounded_sampler_surfaces(
    tmp_path,
    fn_name,
    sampler_api,
    stage_lock_api,
    sampler_mode,
    stage_lock_mode,
    kwargs,
    monkeypatch,
):
    mem = _mem(tmp_path)
    setattr(
        mem,
        sampler_api,
        MagicMock(
            return_value=_sampler_surface(
                mode=sampler_mode,
                state="SYSTEM_EVIDENCE_REVIEW_READY",
            )
        ),
    )
    setattr(
        mem,
        stage_lock_api,
        MagicMock(
            return_value=_stage_lock_surface(
                mode=stage_lock_mode,
                lock_state="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_LOCKED",
            )
        ),
    )

    def _forbidden(*_args, **_kwargs):
        raise AssertionError("forbidden hidden dependency")

    forbidden_names = [
        "get_cross_band_evidence_review_summary_window",
        "get_cross_band_evidence_review_summary_event_order_window",
        "get_observability_evidence_review_summary_window",
        "get_observability_evidence_review_summary_event_order_window",
        "get_pressure_capture_quality_summary_window",
        "get_pressure_capture_quality_summary_event_order_window",
        "get_cross_band_self_check_summary_window",
        "get_cross_band_self_check_summary_event_order_window",
        "get_system_evidence_review_summary",
        "get_observability_evidence_review_summary",
        "get_cross_band_evidence_review_summary",
    ]
    for name in forbidden_names:
        monkeypatch.setattr(mem, name, _forbidden)

    out = getattr(mem, fn_name)(**kwargs)

    assert out["consumer_posture"] == "RELY"
    assert out["gate_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_GATE_RELY"


@pytest.mark.parametrize(
    "fn_name,sampler_api,stage_lock_api,sampler_mode,stage_lock_mode",
    [
        (
            "get_system_evidence_review_sampler_consumer_gate_window",
            "get_system_evidence_review_sampler_window",
            "get_system_evidence_review_sampler_stage_lock_window",
            "SYSTEM_EVIDENCE_REVIEW_WINDOW",
            "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_WINDOW",
        ),
        (
            "get_system_evidence_review_sampler_consumer_gate_event_order_window",
            "get_system_evidence_review_sampler_event_order_window",
            "get_system_evidence_review_sampler_stage_lock_event_order_window",
            "SYSTEM_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
            "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_EVENT_ORDER_WINDOW",
        ),
    ],
)
def test_guardrail_flags_remain_false(
    tmp_path,
    fn_name,
    sampler_api,
    stage_lock_api,
    sampler_mode,
    stage_lock_mode,
):
    mem = _mem(tmp_path)
    sampler = _sampler_surface(mode=sampler_mode, state="SYSTEM_EVIDENCE_REVIEW_READY")
    sampler["lineage_mutation_performed"] = True
    sampler["event_creation_performed"] = True
    sampler["history_rewrite_performed"] = True

    stage_lock = _stage_lock_surface(
        mode=stage_lock_mode,
        lock_state="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_LOCKED",
    )
    stage_lock["lineage_mutation_performed"] = True
    stage_lock["event_creation_performed"] = True
    stage_lock["history_rewrite_performed"] = True

    setattr(mem, sampler_api, MagicMock(return_value=sampler))
    setattr(mem, stage_lock_api, MagicMock(return_value=stage_lock))

    out = getattr(mem, fn_name)()

    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False


def test_cross_window_equivalence_ready_locked_yields_rely(tmp_path):
    mem = _mem(tmp_path)
    mem.get_system_evidence_review_sampler_window = MagicMock(
        return_value=_sampler_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_WINDOW",
            state="SYSTEM_EVIDENCE_REVIEW_READY",
        )
    )
    mem.get_system_evidence_review_sampler_event_order_window = MagicMock(
        return_value=_sampler_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
            state="SYSTEM_EVIDENCE_REVIEW_READY",
        )
    )
    mem.get_system_evidence_review_sampler_stage_lock_window = MagicMock(
        return_value=_stage_lock_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_WINDOW",
            lock_state="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_LOCKED",
        )
    )
    mem.get_system_evidence_review_sampler_stage_lock_event_order_window = MagicMock(
        return_value=_stage_lock_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_EVENT_ORDER_WINDOW",
            lock_state="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_LOCKED",
        )
    )

    out_index = mem.get_system_evidence_review_sampler_consumer_gate_window()
    out_event_order = mem.get_system_evidence_review_sampler_consumer_gate_event_order_window()

    assert out_index["consumer_posture"] == out_event_order["consumer_posture"]
    assert out_index["consumer_posture"] == "RELY"
    assert out_index["gate_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_GATE_RELY"
    assert out_event_order["gate_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_GATE_RELY"


def test_cross_window_equivalence_partial_locked_yields_limited(tmp_path):
    mem = _mem(tmp_path)
    mem.get_system_evidence_review_sampler_window = MagicMock(
        return_value=_sampler_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_WINDOW",
            state="SYSTEM_EVIDENCE_REVIEW_PARTIAL",
        )
    )
    mem.get_system_evidence_review_sampler_event_order_window = MagicMock(
        return_value=_sampler_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
            state="SYSTEM_EVIDENCE_REVIEW_PARTIAL",
        )
    )
    mem.get_system_evidence_review_sampler_stage_lock_window = MagicMock(
        return_value=_stage_lock_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_WINDOW",
            lock_state="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_LOCKED",
        )
    )
    mem.get_system_evidence_review_sampler_stage_lock_event_order_window = MagicMock(
        return_value=_stage_lock_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_EVENT_ORDER_WINDOW",
            lock_state="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_LOCKED",
        )
    )

    out_index = mem.get_system_evidence_review_sampler_consumer_gate_window()
    out_event_order = mem.get_system_evidence_review_sampler_consumer_gate_event_order_window()

    assert out_index["consumer_posture"] == out_event_order["consumer_posture"]
    assert out_index["consumer_posture"] == "LIMITED"
    assert out_index["gate_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_GATE_LIMITED"
    assert out_event_order["gate_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_GATE_LIMITED"


def test_cross_window_equivalence_inconsistent_stage_lock_yields_hold(tmp_path):
    mem = _mem(tmp_path)
    mem.get_system_evidence_review_sampler_window = MagicMock(
        return_value=_sampler_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_WINDOW",
            state="SYSTEM_EVIDENCE_REVIEW_READY",
        )
    )
    mem.get_system_evidence_review_sampler_event_order_window = MagicMock(
        return_value=_sampler_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
            state="SYSTEM_EVIDENCE_REVIEW_READY",
        )
    )
    mem.get_system_evidence_review_sampler_stage_lock_window = MagicMock(
        return_value=_stage_lock_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_WINDOW",
            lock_state="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_INCONSISTENT",
        )
    )
    mem.get_system_evidence_review_sampler_stage_lock_event_order_window = MagicMock(
        return_value=_stage_lock_surface(
            mode="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_EVENT_ORDER_WINDOW",
            lock_state="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_INCONSISTENT",
        )
    )

    out_index = mem.get_system_evidence_review_sampler_consumer_gate_window()
    out_event_order = mem.get_system_evidence_review_sampler_consumer_gate_event_order_window()

    assert out_index["consumer_posture"] == out_event_order["consumer_posture"]
    assert out_index["consumer_posture"] == "HOLD"
    assert out_index["gate_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_GATE_HOLD"
    assert out_event_order["gate_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_GATE_HOLD"
