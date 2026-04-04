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


def _write_ordered_transition_ledger(path: Path) -> None:
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


def test_window_comparator_both_available_and_matching(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_window_comparator()
    assert out["comparison_available"] is True
    assert out["reason"] == "WINDOW_SUMMARIES_MATCH"
    assert out["mismatch_flags"] == ["NO_MISMATCH_DETECTED"]
    assert out["comparison"]["window_event_count_delta"] == 0
    assert out["comparison"]["auditable_event_count_delta"] == 0
    assert all(v == 0 for v in out["comparison"]["audit_state_count_deltas"].values())
    assert all(v == 0 for v in out["comparison"]["capture_reason_count_deltas"].values())
    assert all(v == 0 for v in out["comparison"]["recoverability_count_deltas"].values())
    assert all(v == 0 for v in out["comparison"]["event_type_count_deltas"].values())


def test_window_comparator_both_available_and_differing(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_window_comparator(
        start_index=0,
        end_index=2,
        start_event_order=4,
        end_event_order=5,
    )
    assert out["comparison_available"] is True
    assert out["reason"] == "WINDOW_SUMMARIES_DIFFER"
    assert "AUDIT_STATE_MISMATCH" in out["mismatch_flags"]
    assert "CAPTURE_REASON_MISMATCH" in out["mismatch_flags"]
    assert "RECOVERABILITY_MISMATCH" in out["mismatch_flags"]
    assert "NO_MISMATCH_DETECTED" not in out["mismatch_flags"]


def test_window_comparator_index_unavailable_event_order_available(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_window_comparator(
        start_index=4,
        end_index=2,
        start_event_order=1,
        end_event_order=5,
    )
    assert out["comparison_available"] is True
    assert out["reason"] == "INDEX_WINDOW_UNAVAILABLE"
    assert "INDEX_WINDOW_UNAVAILABLE" in out["mismatch_flags"]
    assert "EVENT_ORDER_WINDOW_UNAVAILABLE" not in out["mismatch_flags"]


def test_window_comparator_event_order_unavailable_index_available(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_window_comparator(
        start_index=0,
        end_index=5,
        start_event_order=5,
        end_event_order=2,
    )
    assert out["comparison_available"] is True
    assert out["reason"] == "EVENT_ORDER_WINDOW_UNAVAILABLE"
    assert "EVENT_ORDER_WINDOW_UNAVAILABLE" in out["mismatch_flags"]
    assert "INDEX_WINDOW_UNAVAILABLE" not in out["mismatch_flags"]


def test_window_comparator_both_unavailable(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_window_comparator(
        start_index=4,
        end_index=2,
        start_event_order=5,
        end_event_order=2,
    )
    assert out["comparison_available"] is False
    assert out["reason"] == "BOTH_WINDOWS_UNAVAILABLE"
    assert "INDEX_WINDOW_UNAVAILABLE" in out["mismatch_flags"]
    assert "EVENT_ORDER_WINDOW_UNAVAILABLE" in out["mismatch_flags"]


def test_window_comparator_delta_math_by_bucket(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_window_comparator(
        start_index=0,
        end_index=2,
        start_event_order=1,
        end_event_order=3,
    )

    # index window: events 1-2, event_order window: events 1-3
    assert out["comparison"]["window_event_count_delta"] == 1
    assert out["comparison"]["auditable_event_count_delta"] == 1
    assert out["comparison"]["pressure_snapshot_present_count_delta"] == 1
    assert out["comparison"]["pressure_snapshot_missing_count_delta"] == 0
    assert out["comparison"]["audit_state_count_deltas"] == {
        "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
        "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
        "PRESSURE_CAPTURE_AUDIT_VALID": 1,
    }
    assert out["comparison"]["capture_reason_count_deltas"] == {
        "PRESSURE_CAPTURE_FAILED": 1,
        "PRESSURE_CAPTURE_FULL": 0,
        "PRESSURE_CAPTURE_PARTIAL": 0,
        "UNRECOGNIZED_CAPTURE_REASON": 0,
    }
    assert out["comparison"]["recoverability_count_deltas"] == {
        "FULLY_RECOVERABLE": 0,
        "PARTIALLY_RECOVERABLE": 0,
        "UNRECOVERABLE": 1,
    }
    assert out["comparison"]["event_type_count_deltas"] == {
        "FAMILY_FISSION": 1,
        "FAMILY_REUNION": 0,
    }


def test_window_comparator_mismatch_flags_correctness(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out_match = mem.get_pressure_capture_quality_window_comparator()
    assert out_match["mismatch_flags"] == ["NO_MISMATCH_DETECTED"]

    out_diff = mem.get_pressure_capture_quality_window_comparator(
        start_index=0,
        end_index=2,
        start_event_order=4,
        end_event_order=5,
    )
    assert "NO_MISMATCH_DETECTED" not in out_diff["mismatch_flags"]


def test_window_comparator_read_only_no_repair_no_retrofit(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    before = ledger.read_text(encoding="utf-8")
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_window_comparator()
    after = ledger.read_text(encoding="utf-8")

    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False
    assert before == after
