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
    # A: valid FULL (fission)
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
    # B: valid PARTIAL (reunion)
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
    # C: valid FAILED (fission)
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
    # D: INVALID mismatch (reunion, reason FULL but only pre payload)
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
    # E: unavailable legacy event (fission)
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


def test_capture_quality_summary_empty_or_no_transition_events(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    # Non-transition record should be skipped.
    _write_event(
        ledger,
        {
            "event_id": "non_transition_0001",
            "event_type": "NOT_A_TRANSITION",
            "event_order": 1,
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_summary()
    assert out["summary_available"] is True
    assert out["summary_mode"] == "LEDGER_READ_ONLY"
    assert out["total_transition_events"] == 0
    assert out["auditable_event_count"] == 0
    assert out["pressure_snapshot_present_count"] == 0
    assert out["pressure_snapshot_missing_count"] == 0
    assert out["audit_state_counts"]["PRESSURE_CAPTURE_AUDIT_VALID"] == 0
    assert out["recoverability_counts"]["UNRECOVERABLE"] == 0
    assert "NON_TRANSITION_LEDGER_RECORDS_SKIPPED" in out["warnings"]


def test_capture_quality_summary_mixed_counts_and_breakdown(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_mixed_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_pressure_capture_quality_summary()
    assert out["total_transition_events"] == 5
    assert out["auditable_event_count"] == 5
    assert out["pressure_snapshot_present_count"] == 4
    assert out["pressure_snapshot_missing_count"] == 1

    assert out["audit_state_counts"] == {
        "PRESSURE_CAPTURE_AUDIT_VALID": 3,
        "PRESSURE_CAPTURE_AUDIT_INVALID": 1,
        "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 1,
    }
    assert out["capture_reason_counts"] == {
        "PRESSURE_CAPTURE_FULL": 2,
        "PRESSURE_CAPTURE_PARTIAL": 1,
        "PRESSURE_CAPTURE_FAILED": 1,
        "UNRECOGNIZED_CAPTURE_REASON": 0,
    }
    assert out["recoverability_counts"] == {
        "FULLY_RECOVERABLE": 1,
        "PARTIALLY_RECOVERABLE": 2,
        "UNRECOVERABLE": 2,
    }
    assert out["event_type_counts"] == {
        "FAMILY_FISSION": 3,
        "FAMILY_REUNION": 2,
    }

    fission = out["event_type_breakdown"]["FAMILY_FISSION"]
    reunion = out["event_type_breakdown"]["FAMILY_REUNION"]
    assert fission["total"] == 3
    assert fission["pressure_snapshot_present"] == 2
    assert fission["pressure_snapshot_missing"] == 1
    assert fission["audit_state_counts"]["PRESSURE_CAPTURE_AUDIT_VALID"] == 2
    assert fission["recoverability_counts"]["UNRECOVERABLE"] == 2

    assert reunion["total"] == 2
    assert reunion["pressure_snapshot_present"] == 2
    assert reunion["pressure_snapshot_missing"] == 0
    assert reunion["audit_state_counts"]["PRESSURE_CAPTURE_AUDIT_INVALID"] == 1
    assert reunion["recoverability_counts"]["PARTIALLY_RECOVERABLE"] == 2


def test_capture_quality_summary_read_only_no_repair_no_retrofit(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    legacy = {
        "event_id": "evt_legacy_0001",
        "event_type": "FAMILY_REUNION_V1",
        "event_order": 1,
        "source_family_ids": ["fam_20", "fam_21"],
        "successor_family_ids": ["fam_22"],
    }
    _write_event(ledger, legacy)
    before = ledger.read_text(encoding="utf-8")

    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    out = mem.get_pressure_capture_quality_summary()
    after = ledger.read_text(encoding="utf-8")

    assert out["total_transition_events"] == 1
    assert out["pressure_snapshot_missing_count"] == 1
    assert out["audit_state_counts"]["PRESSURE_CAPTURE_AUDIT_UNAVAILABLE"] == 1
    assert before == after
    assert mem.get_event_ledger()[0] == legacy
