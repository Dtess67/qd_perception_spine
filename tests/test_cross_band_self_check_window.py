import copy
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


def _write_cross_band_window_ledger(path: Path) -> None:
    _write_event(
        path,
        {
            "event_id": "evt_w_01_align_fission",
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
            "event_id": "evt_w_02_contradict_fission",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 2,
            "source_family_ids": ["fam_10"],
            "successor_family_ids": ["fam_11", "fam_12"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_10"], "PRESSURE_STABLE"),
                "post_event_pressure": _pressure_payload(["fam_11", "fam_12"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {"fam_10": "PRESSURE_CAPTURED"},
                "post_capture_status_by_family": {
                    "fam_11": "PRESSURE_CAPTURED",
                    "fam_12": "PRESSURE_CAPTURED",
                },
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "evt_w_03_partial_reunion",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 3,
            "source_family_ids": ["fam_20", "fam_21"],
            "successor_family_ids": ["fam_22"],
        },
    )
    _write_event(
        path,
        {
            "event_id": "evt_w_04_align_reunion",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 4,
            "source_family_ids": ["fam_30", "fam_31"],
            "successor_family_ids": ["fam_32"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_30", "fam_31"], "PRESSURE_STABLE"),
                "post_event_pressure": _pressure_payload(["fam_32"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {
                    "fam_30": "PRESSURE_CAPTURED",
                    "fam_31": "PRESSURE_CAPTURED",
                },
                "post_capture_status_by_family": {"fam_32": "PRESSURE_CAPTURED"},
            },
        },
    )


def test_cross_band_self_check_window_no_transition_events(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_window()
    assert out["summary_mode"] == "CROSS_BAND_SELF_CHECK_WINDOW"
    assert out["summary_available"] is True
    assert out["reason"] == "NO_TRANSITION_EVENTS"
    assert out["total_transition_events"] == 0
    assert out["window_event_count"] == 0
    assert out["auditable_event_count"] == 0
    assert out["self_check_state_counts"] == {
        "CROSS_BAND_ALIGNMENT_OBSERVED": 0,
        "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
        "CROSS_BAND_PARTIAL": 0,
        "CROSS_BAND_UNAVAILABLE": 0,
    }


def test_cross_band_self_check_window_invalid_bounds_fail_closed(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_window_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_window(start_index=3, end_index=1)
    assert out["summary_available"] is False
    assert out["reason"] == "INVALID_WINDOW_BOUNDS"
    assert "INVALID_WINDOW_BOUNDS" in out["warnings"]
    assert out["window_event_count"] == 0
    assert out["auditable_event_count"] == 0


def test_cross_band_self_check_window_empty_valid_slice(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_window_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_window(start_index=2, end_index=2)
    assert out["summary_available"] is True
    assert out["reason"] == "EMPTY_WINDOW_SELECTION"
    assert out["window_event_count"] == 0
    assert "EMPTY_WINDOW_SELECTION" in out["warnings"]


def test_cross_band_self_check_window_mixed_alignment_contradiction_partial_unavailable(tmp_path: Path, monkeypatch):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_window_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    original = mem.get_transition_cross_band_self_check

    def patched(event_id: str):
        if event_id == "evt_w_04_align_reunion":
            return {
                "event_id": event_id,
                "found": True,
                "audit_available": False,
                "audit_mode": "CROSS_BAND_SELF_CHECK",
                "self_check_state": "CROSS_BAND_UNAVAILABLE",
                "reason": "PATCHED_UNAVAILABLE_FOR_WINDOW_TEST",
                "event_type": "FAMILY_REUNION_V1",
                "participant_family_ids": ["fam_30", "fam_31", "fam_32"],
                "evidence_surface": {
                    "pressure_available": False,
                    "topology_available": False,
                    "event_snapshot_available": False,
                    "pre_event_directional_signal": "PRESSURE_SIGNAL_UNAVAILABLE",
                    "post_event_outcome_signal": "OUTCOME_REUNION",
                    "recoverability_notes": ["PATCHED_UNAVAILABLE"],
                },
                "directional_alignment": {
                    "pressure_alignment": "PRESSURE_ALIGNMENT_UNAVAILABLE",
                    "topology_alignment": "TOPOLOGY_ALIGNMENT_UNAVAILABLE",
                    "overall_alignment": "OVERALL_ALIGNMENT_UNAVAILABLE",
                    "confidence_posture": "CONFIDENCE_NONE",
                },
                "contradiction_flags": ["EVIDENCE_INSUFFICIENT"],
                "warnings": ["PATCHED_UNAVAILABLE"],
                "explanation_lines": ["Patched unavailable state for mixed-window aggregation test."],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        return original(event_id)

    monkeypatch.setattr(mem, "get_transition_cross_band_self_check", patched)
    out = mem.get_cross_band_self_check_summary_window(start_index=0, end_index=4)

    assert out["summary_available"] is True
    assert out["reason"] == "OK"
    assert out["window_event_count"] == 4
    assert out["auditable_event_count"] == 4
    assert out["self_check_state_counts"] == {
        "CROSS_BAND_ALIGNMENT_OBSERVED": 1,
        "CROSS_BAND_CONTRADICTION_OBSERVED": 1,
        "CROSS_BAND_PARTIAL": 0,
        "CROSS_BAND_UNAVAILABLE": 2,
    }


def test_cross_band_self_check_window_max_events_limiting_behavior(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_window_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_window(start_index=0, end_index=4, max_events=2)
    assert out["summary_available"] is True
    assert out["window_event_count"] == 2
    assert out["auditable_event_count"] == 2
    assert out["window_spec"]["applied_start_index"] == 0
    assert out["window_spec"]["applied_end_index"] == 2
    assert out["event_type_counts"] == {"FAMILY_FISSION": 2}


def test_cross_band_self_check_window_contradiction_flag_count_aggregation(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_window_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_window(start_index=0, end_index=4)
    flags = out["contradiction_flag_counts"]

    assert flags["PRESSURE_EVENT_DIRECTION_CONTRADICTION"] == 1
    assert flags["NO_CONTRADICTION_OBSERVED"] == 2
    assert flags["EVIDENCE_INSUFFICIENT"] == 1
    assert flags["TOPOLOGY_EVENT_DIRECTION_CONTRADICTION"] == 0


def test_cross_band_self_check_window_event_type_count_correctness(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_window_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_window(start_index=1, end_index=4)
    assert out["event_type_counts"] == {
        "FAMILY_FISSION": 1,
        "FAMILY_REUNION": 2,
    }


def test_cross_band_self_check_window_read_only_no_mutation_behavior(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_window_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    families_before = copy.deepcopy(mem._families)
    symbol_to_family_before = dict(mem._symbol_to_family)
    fission_before = mem.get_fission_events()
    reunion_before = mem.get_reunion_events()
    ledger_before = mem.get_event_ledger()

    out = mem.get_cross_band_self_check_summary_window(start_index=0, end_index=4)

    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False
    assert mem._families == families_before
    assert mem._symbol_to_family == symbol_to_family_before
    assert mem.get_fission_events() == fission_before
    assert mem.get_reunion_events() == reunion_before
    assert mem.get_event_ledger() == ledger_before


def test_cross_band_self_check_window_no_repair_no_retrofit_behavior(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    legacy = {
        "event_id": "evt_legacy_window_no_snapshot_0001",
        "event_type": "FAMILY_FISSION_V1",
        "event_order": 1,
        "source_family_ids": ["fam_90"],
        "successor_family_ids": ["fam_91", "fam_92"],
    }
    _write_event(ledger, legacy)
    before = ledger.read_text(encoding="utf-8")

    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    out = mem.get_cross_band_self_check_summary_window(start_index=0, end_index=1)

    after = ledger.read_text(encoding="utf-8")
    persisted = mem.get_event_ledger()[0]

    assert out["summary_available"] is True
    assert out["window_event_count"] == 1
    assert out["self_check_state_counts"]["CROSS_BAND_UNAVAILABLE"] == 1
    assert before == after
    assert persisted == legacy
