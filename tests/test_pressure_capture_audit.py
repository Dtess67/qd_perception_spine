import json
from pathlib import Path

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _write_event(path: Path, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def _valid_pressure_payload(family_ids: list[str], state: str) -> dict:
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


def test_pressure_capture_audit_event_not_found_unavailable(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_pressure_capture_audit("evt_missing_0001")
    assert out["found"] is False
    assert out["audit_available"] is False
    assert out["audit_state"] == "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE"
    assert out["reason"] == "EVENT_NOT_FOUND"


def test_pressure_capture_audit_event_with_no_snapshot_unavailable(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_legacy_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_01"],
            "successor_family_ids": ["fam_02", "fam_03"],
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_pressure_capture_audit("evt_legacy_0001")
    assert out["found"] is True
    assert out["audit_available"] is False
    assert out["audit_state"] == "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE"
    assert out["reason"] == "PRESSURE_SNAPSHOT_NOT_STORED"


def test_pressure_capture_audit_valid_full_block(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_full_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_10"],
            "successor_family_ids": ["fam_11", "fam_12"],
            "pressure_snapshot": {
                "pre_event_pressure": _valid_pressure_payload(["fam_10"], "PRESSURE_FISSION_PRONE"),
                "post_event_pressure": _valid_pressure_payload(["fam_11", "fam_12"], "PRESSURE_STABLE"),
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
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_pressure_capture_audit("evt_full_0001")
    assert out["audit_state"] == "PRESSURE_CAPTURE_AUDIT_VALID"
    assert out["structural_validity"]["ok"] is True
    assert out["metadata_consistency"]["ok"] is True
    assert out["payload_consistency"]["ok"] is True
    assert out["reader_consistency"]["ok"] is True


def test_pressure_capture_audit_valid_partial_block(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_partial_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 2,
            "source_family_ids": ["fam_20"],
            "successor_family_ids": ["fam_21", "fam_22"],
            "pressure_snapshot": {
                "pre_event_pressure": _valid_pressure_payload(["fam_20"], "PRESSURE_STABLE"),
                "post_event_pressure": None,
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_PARTIAL",
                "pre_capture_status_by_family": {"fam_20": "PRESSURE_CAPTURED"},
                "post_capture_status_by_family": {
                    "fam_21": "PRESSURE_UNAVAILABLE",
                    "fam_22": "PRESSURE_UNAVAILABLE",
                },
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_pressure_capture_audit("evt_partial_0001")
    assert out["audit_state"] == "PRESSURE_CAPTURE_AUDIT_VALID"


def test_pressure_capture_audit_valid_failed_block(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_failed_0001",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 3,
            "source_family_ids": ["fam_30", "fam_31"],
            "successor_family_ids": ["fam_32"],
            "pressure_snapshot": {
                "pre_event_pressure": None,
                "post_event_pressure": None,
                "capture_attempted": True,
                "capture_succeeded": False,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FAILED",
                "pre_capture_status_by_family": {
                    "fam_30": "PRESSURE_CAPTURE_EXCEPTION:RuntimeError",
                    "fam_31": "PRESSURE_CAPTURE_EXCEPTION:RuntimeError",
                },
                "post_capture_status_by_family": {"fam_32": "PRESSURE_CAPTURE_EXCEPTION:RuntimeError"},
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_pressure_capture_audit("evt_failed_0001")
    assert out["audit_state"] == "PRESSURE_CAPTURE_AUDIT_VALID"


def test_pressure_capture_audit_invalid_reason_payload_mismatch(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_invalid_reason_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 4,
            "source_family_ids": ["fam_40"],
            "successor_family_ids": ["fam_41", "fam_42"],
            "pressure_snapshot": {
                "pre_event_pressure": _valid_pressure_payload(["fam_40"], "PRESSURE_STABLE"),
                "post_event_pressure": None,
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {"fam_40": "PRESSURE_CAPTURED"},
                "post_capture_status_by_family": {
                    "fam_41": "PRESSURE_UNAVAILABLE",
                    "fam_42": "PRESSURE_UNAVAILABLE",
                },
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_pressure_capture_audit("evt_invalid_reason_0001")
    assert out["audit_state"] == "PRESSURE_CAPTURE_AUDIT_INVALID"
    assert "CAPTURE_REASON_FULL_REQUIRES_BOTH_SIDES" in out["metadata_consistency"]["issues"]


def test_pressure_capture_audit_invalid_capture_succeeded_mismatch(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_invalid_succeeded_0001",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 5,
            "source_family_ids": ["fam_50", "fam_51"],
            "successor_family_ids": ["fam_52"],
            "pressure_snapshot": {
                "pre_event_pressure": None,
                "post_event_pressure": None,
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FAILED",
                "pre_capture_status_by_family": {
                    "fam_50": "PRESSURE_CAPTURE_EXCEPTION:RuntimeError",
                    "fam_51": "PRESSURE_CAPTURE_EXCEPTION:RuntimeError",
                },
                "post_capture_status_by_family": {"fam_52": "PRESSURE_CAPTURE_EXCEPTION:RuntimeError"},
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_pressure_capture_audit("evt_invalid_succeeded_0001")
    assert out["audit_state"] == "PRESSURE_CAPTURE_AUDIT_INVALID"
    assert "CAPTURE_REASON_FAILED_REQUIRES_CAPTURE_SUCCEEDED_FALSE" in out["metadata_consistency"]["issues"]


def test_pressure_capture_audit_invalid_family_status_map_mismatch(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_invalid_map_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 6,
            "source_family_ids": ["fam_60"],
            "successor_family_ids": ["fam_61", "fam_62"],
            "pressure_snapshot": {
                "pre_event_pressure": _valid_pressure_payload(["fam_60"], "PRESSURE_STABLE"),
                "post_event_pressure": _valid_pressure_payload(["fam_61", "fam_62"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {
                    "fam_60": "PRESSURE_CAPTURED",
                    "fam_X": "PRESSURE_CAPTURED",
                },
                "post_capture_status_by_family": {
                    "fam_61": "PRESSURE_CAPTURED",
                    "fam_62": "NOT_A_VALID_STATUS",
                },
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_pressure_capture_audit("evt_invalid_map_0001")
    assert out["audit_state"] == "PRESSURE_CAPTURE_AUDIT_INVALID"
    assert "PRE_CAPTURE_STATUS_MAP_KEY_MISMATCH" in out["metadata_consistency"]["issues"]
    assert "POST_CAPTURE_STATUS_VALUE_UNRECOGNIZED" in out["metadata_consistency"]["issues"]


def test_pressure_capture_audit_reader_consistency_check(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_reader_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 7,
            "source_family_ids": ["fam_70"],
            "successor_family_ids": ["fam_71", "fam_72"],
            "pressure_snapshot": {
                "pre_event_pressure": _valid_pressure_payload(["fam_70"], "PRESSURE_STABLE"),
                "post_event_pressure": _valid_pressure_payload(["fam_71", "fam_72"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {"fam_70": "PRESSURE_CAPTURED"},
                "post_capture_status_by_family": {
                    "fam_71": "PRESSURE_CAPTURED",
                    "fam_72": "PRESSURE_CAPTURED",
                },
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    original_reader = mem.get_transition_pressure_snapshot
    mem.get_transition_pressure_snapshot = lambda _event_id: {
        "found": True,
        "snapshot_available": False,
        "pre_event_pressure": None,
        "post_event_pressure": None,
        "evidence_flags": {
            "pre_event_pressure_recoverable": False,
            "post_event_pressure_recoverable": False,
        },
    }
    try:
        out = mem.get_transition_pressure_capture_audit("evt_reader_0001")
    finally:
        mem.get_transition_pressure_snapshot = original_reader

    assert out["audit_state"] == "PRESSURE_CAPTURE_AUDIT_INVALID"
    assert "SNAPSHOT_READER_PRE_RECOVERABILITY_MISMATCH" in out["reader_consistency"]["issues"]
    assert "SNAPSHOT_READER_POST_RECOVERABILITY_MISMATCH" in out["reader_consistency"]["issues"]


def test_pressure_capture_audit_no_mutation_no_repair(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    bad_event = {
        "event_id": "evt_no_repair_0001",
        "event_type": "FAMILY_REUNION_V1",
        "event_order": 8,
        "source_family_ids": ["fam_80", "fam_81"],
        "successor_family_ids": ["fam_82"],
        "pressure_snapshot": {
            "pre_event_pressure": None,
            "post_event_pressure": _valid_pressure_payload(["fam_82"], "PRESSURE_STABLE"),
            "capture_attempted": True,
            "capture_succeeded": False,
            "capture_mode": "EVENT_WRITE_TIME",
            "capture_reason": "PRESSURE_CAPTURE_FAILED",
            "pre_capture_status_by_family": {
                "fam_80": "PRESSURE_UNAVAILABLE",
                "fam_81": "PRESSURE_UNAVAILABLE",
            },
            "post_capture_status_by_family": {"fam_82": "PRESSURE_CAPTURED"},
        },
    }
    _write_event(ledger, bad_event)
    before_text = ledger.read_text(encoding="utf-8")

    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    out = mem.get_transition_pressure_capture_audit("evt_no_repair_0001")
    after_text = ledger.read_text(encoding="utf-8")

    assert out["audit_state"] == "PRESSURE_CAPTURE_AUDIT_INVALID"
    assert before_text == after_text
    assert mem.get_event_ledger()[0] == bad_event
