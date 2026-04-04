import json
from pathlib import Path

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _write_event(path: Path, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def _pressure_payload(family_ids: list[str], state: str) -> dict:
    return {
        "family_ids": list(family_ids),
        "family_pressure_by_id": {
            fam_id: {
                "family_id": fam_id,
                "pressure_state": state,
                "forecast_available": True,
                "scorecard": {"diagnostic_scale": "0_to_1_comparative_not_probability"},
            }
            for fam_id in family_ids
        },
    }


def _write_mixed_transition_ledger(path: Path) -> None:
    _write_event(
        path,
        {
            "event_id": "evt_a_full_fission",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_01"],
            "successor_family_ids": ["fam_02", "fam_03"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_01"], "PRESSURE_FISSION_PRONE"),
                "post_event_pressure": _pressure_payload(["fam_02", "fam_03"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {"fam_01": "PRESSURE_CAPTURED"},
                "post_capture_status_by_family": {
                    "fam_02": "PRESSURE_CAPTURED",
                    "fam_03": "PRESSURE_CAPTURED",
                },
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "evt_b_partial_reunion",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 2,
            "source_family_ids": ["fam_04", "fam_05"],
            "successor_family_ids": ["fam_06"],
            "pressure_snapshot": {
                "pre_event_pressure": None,
                "post_event_pressure": _pressure_payload(["fam_06"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_PARTIAL",
                "pre_capture_status_by_family": {
                    "fam_04": "PRESSURE_UNAVAILABLE",
                    "fam_05": "PRESSURE_UNAVAILABLE",
                },
                "post_capture_status_by_family": {"fam_06": "PRESSURE_CAPTURED"},
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "evt_c_failed_fission",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 3,
            "source_family_ids": ["fam_07"],
            "successor_family_ids": ["fam_08", "fam_09"],
            "pressure_snapshot": {
                "pre_event_pressure": None,
                "post_event_pressure": None,
                "capture_attempted": True,
                "capture_succeeded": False,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FAILED",
                "pre_capture_status_by_family": {"fam_07": "PRESSURE_CAPTURE_EXCEPTION:RuntimeError"},
                "post_capture_status_by_family": {
                    "fam_08": "PRESSURE_CAPTURE_EXCEPTION:RuntimeError",
                    "fam_09": "PRESSURE_CAPTURE_EXCEPTION:RuntimeError",
                },
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "evt_d_invalid_reunion",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 4,
            "source_family_ids": ["fam_10", "fam_11"],
            "successor_family_ids": ["fam_12"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_10", "fam_11"], "PRESSURE_STABLE"),
                "post_event_pressure": None,
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {
                    "fam_10": "PRESSURE_CAPTURED",
                    "fam_11": "PRESSURE_CAPTURED",
                },
                "post_capture_status_by_family": {"fam_12": "PRESSURE_UNAVAILABLE"},
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "evt_e_missing_snapshot",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 5,
            "source_family_ids": ["fam_13"],
            "successor_family_ids": ["fam_14", "fam_15"],
        },
    )


def test_event_order_window_no_transition_events(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_summary_event_order_window()
    assert out["summary_mode"] == "LEDGER_READ_ONLY_EVENT_ORDER_WINDOWED"
    assert out["summary_available"] is True
    assert out["reason"] == "NO_TRANSITION_EVENTS"
    assert out["total_transition_events"] == 0
    assert out["total_event_order_eligible_events"] == 0
    assert out["window_event_count"] == 0


def test_event_order_window_no_event_order_eligible_transition_events(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_no_order_01",
            "event_type": "FAMILY_FISSION_V1",
            "source_family_ids": ["fam_01"],
            "successor_family_ids": ["fam_02", "fam_03"],
        },
    )
    _write_event(
        ledger,
        {
            "event_id": "evt_no_order_02",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": "not_numeric",
            "source_family_ids": ["fam_04", "fam_05"],
            "successor_family_ids": ["fam_06"],
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_summary_event_order_window()
    assert out["summary_available"] is False
    assert out["reason"] == "NO_EVENT_ORDER_ELIGIBLE_EVENTS"
    assert out["total_transition_events"] == 2
    assert out["total_event_order_eligible_events"] == 0
    assert out["window_event_count"] == 0
    assert "EVENT_ORDER_INELIGIBLE_EVENTS_SKIPPED" in out["warnings"]


def test_event_order_window_full_range_matches_v14_when_orders_present(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_mixed_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    base = mem.get_pressure_capture_quality_summary()
    out = mem.get_pressure_capture_quality_summary_event_order_window()

    assert out["summary_available"] is True
    assert out["reason"] == "OK"
    assert out["total_transition_events"] == 5
    assert out["total_event_order_eligible_events"] == 5
    assert out["window_event_count"] == 5
    assert out["auditable_event_count"] == base["auditable_event_count"]
    assert out["capture_reason_counts"] == base["capture_reason_counts"]
    assert out["audit_state_counts"] == base["audit_state_counts"]
    assert out["recoverability_counts"] == base["recoverability_counts"]


def test_event_order_window_bounded_mixed_counts(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_mixed_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_summary_event_order_window(start_event_order=2, end_event_order=4)
    assert out["summary_available"] is True
    assert out["reason"] == "OK"
    assert out["window_event_count"] == 3
    assert out["window_spec"]["applied_start_event_order"] == 2.0
    assert out["window_spec"]["applied_end_event_order"] == 4.0
    assert out["pressure_snapshot_present_count"] == 3
    assert out["pressure_snapshot_missing_count"] == 0
    assert out["capture_reason_counts"] == {
        "PRESSURE_CAPTURE_FULL": 1,
        "PRESSURE_CAPTURE_PARTIAL": 1,
        "PRESSURE_CAPTURE_FAILED": 1,
        "UNRECOGNIZED_CAPTURE_REASON": 0,
    }


def test_event_order_window_max_events_after_filtering(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_mixed_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_summary_event_order_window(
        start_event_order=1,
        end_event_order=5,
        max_events=2,
    )
    assert out["summary_available"] is True
    assert out["window_event_count"] == 2
    assert out["window_spec"]["applied_start_event_order"] == 1.0
    assert out["window_spec"]["applied_end_event_order"] == 2.0
    assert out["event_type_counts"] == {
        "FAMILY_FISSION": 1,
        "FAMILY_REUNION": 1,
    }


def test_event_order_window_invalid_bounds_fail_closed(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_mixed_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_summary_event_order_window(start_event_order=5, end_event_order=2)
    assert out["summary_available"] is False
    assert out["reason"] == "INVALID_EVENT_ORDER_BOUNDS"
    assert "INVALID_EVENT_ORDER_BOUNDS" in out["warnings"]
    assert out["window_event_count"] == 0
    assert out["auditable_event_count"] == 0


def test_event_order_window_deterministic_tie_behavior_duplicate_event_order(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    # Same event_order with different event types to prove stable tie behavior via ledger sequence.
    _write_event(
        ledger,
        {
            "event_id": "evt_tie_01",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 10,
            "source_family_ids": ["fam_01", "fam_02"],
            "successor_family_ids": ["fam_03"],
            "pressure_snapshot": {
                "pre_event_pressure": None,
                "post_event_pressure": _pressure_payload(["fam_03"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_PARTIAL",
                "pre_capture_status_by_family": {
                    "fam_01": "PRESSURE_UNAVAILABLE",
                    "fam_02": "PRESSURE_UNAVAILABLE",
                },
                "post_capture_status_by_family": {"fam_03": "PRESSURE_CAPTURED"},
            },
        },
    )
    _write_event(
        ledger,
        {
            "event_id": "evt_tie_02",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 10,
            "source_family_ids": ["fam_04"],
            "successor_family_ids": ["fam_05", "fam_06"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_04"], "PRESSURE_FISSION_PRONE"),
                "post_event_pressure": _pressure_payload(["fam_05", "fam_06"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {"fam_04": "PRESSURE_CAPTURED"},
                "post_capture_status_by_family": {
                    "fam_05": "PRESSURE_CAPTURED",
                    "fam_06": "PRESSURE_CAPTURED",
                },
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_summary_event_order_window(
        start_event_order=10,
        end_event_order=10,
        max_events=1,
    )
    assert out["summary_available"] is True
    assert out["window_event_count"] == 1
    # First ledger-sequence event should win tie -> reunion only.
    assert out["event_type_counts"] == {"FAMILY_REUNION": 1}
    assert out["capture_reason_counts"]["PRESSURE_CAPTURE_PARTIAL"] == 1


def test_event_order_window_per_event_type_breakdown_within_selected_range(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_mixed_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_summary_event_order_window(start_event_order=3, end_event_order=5)
    assert out["event_type_counts"] == {
        "FAMILY_FISSION": 2,
        "FAMILY_REUNION": 1,
    }
    fission = out["event_type_breakdown"]["FAMILY_FISSION"]
    reunion = out["event_type_breakdown"]["FAMILY_REUNION"]
    assert fission["total"] == 2
    assert fission["pressure_snapshot_missing"] == 1
    assert reunion["total"] == 1
    assert reunion["audit_state_counts"]["PRESSURE_CAPTURE_AUDIT_INVALID"] == 1


def test_event_order_window_read_only_no_repair_no_retrofit(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_legacy_0001",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 7,
            "source_family_ids": ["fam_20", "fam_21"],
            "successor_family_ids": ["fam_22"],
        },
    )
    before = ledger.read_text(encoding="utf-8")
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_summary_event_order_window(start_event_order=7, end_event_order=7)
    after = ledger.read_text(encoding="utf-8")
    assert out["summary_available"] is True
    assert out["window_event_count"] == 1
    assert out["pressure_snapshot_missing_count"] == 1
    assert out["audit_state_counts"]["PRESSURE_CAPTURE_AUDIT_UNAVAILABLE"] == 1
    assert before == after

