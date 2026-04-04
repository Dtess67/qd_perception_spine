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


def test_transition_cross_band_self_check_event_not_found(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_cross_band_self_check("evt_missing_0001")

    assert out["found"] is False
    assert out["audit_available"] is False
    assert out["self_check_state"] == "CROSS_BAND_UNAVAILABLE"
    assert out["reason"] == "EVENT_NOT_FOUND"
    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False


def test_transition_cross_band_self_check_insufficient_recoverable_evidence(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_no_snapshot_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_01"],
            "successor_family_ids": ["fam_02", "fam_03"],
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_cross_band_self_check("evt_no_snapshot_0001")

    assert out["found"] is True
    assert out["audit_available"] is True
    assert out["self_check_state"] == "CROSS_BAND_UNAVAILABLE"
    assert out["reason"] == "INSUFFICIENT_DIRECTIONAL_EVIDENCE"
    assert "EVIDENCE_INSUFFICIENT" in out["contradiction_flags"]


def test_transition_cross_band_self_check_split_pressure_aligned_with_fission(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_fission_aligned_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 2,
            "source_family_ids": ["fam_10"],
            "successor_family_ids": ["fam_11", "fam_12"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_10"], "PRESSURE_FISSION_PRONE"),
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
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_cross_band_self_check("evt_fission_aligned_0001")

    assert out["self_check_state"] == "CROSS_BAND_ALIGNMENT_OBSERVED"
    assert out["reason"] == "DIRECTIONAL_ALIGNMENT_OBSERVED"
    assert out["directional_alignment"]["pressure_alignment"] == "PRESSURE_ALIGNMENT_OBSERVED"
    assert out["evidence_surface"]["pre_event_directional_signal"] == "PRESSURE_SIGNAL_SPLIT_ORIENTED"
    assert "NO_CONTRADICTION_OBSERVED" in out["contradiction_flags"]


def test_transition_cross_band_self_check_non_split_pressure_contradicting_fission(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_fission_contradiction_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 3,
            "source_family_ids": ["fam_20"],
            "successor_family_ids": ["fam_21", "fam_22"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_20"], "PRESSURE_STABLE"),
                "post_event_pressure": _pressure_payload(["fam_21", "fam_22"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {"fam_20": "PRESSURE_CAPTURED"},
                "post_capture_status_by_family": {
                    "fam_21": "PRESSURE_CAPTURED",
                    "fam_22": "PRESSURE_CAPTURED",
                },
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_cross_band_self_check("evt_fission_contradiction_0001")

    assert out["self_check_state"] == "CROSS_BAND_CONTRADICTION_OBSERVED"
    assert out["reason"] == "DIRECTIONAL_CONTRADICTION_OBSERVED"
    assert out["directional_alignment"]["pressure_alignment"] == "PRESSURE_ALIGNMENT_CONTRADICTION"
    assert "PRESSURE_EVENT_DIRECTION_CONTRADICTION" in out["contradiction_flags"]


def test_transition_cross_band_self_check_recoverable_no_contradiction_observed(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_reunion_no_contradiction_0001",
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
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_cross_band_self_check("evt_reunion_no_contradiction_0001")

    assert out["self_check_state"] == "CROSS_BAND_ALIGNMENT_OBSERVED"
    assert out["directional_alignment"]["pressure_alignment"] == "PRESSURE_ALIGNMENT_OBSERVED"
    assert "PRESSURE_EVENT_DIRECTION_CONTRADICTION" not in out["contradiction_flags"]
    assert "NO_CONTRADICTION_OBSERVED" in out["contradiction_flags"]


def test_transition_cross_band_self_check_reunion_stretched_not_alignment(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_reunion_stretched_0001",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 5,
            "source_family_ids": ["fam_60", "fam_61"],
            "successor_family_ids": ["fam_62"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_60", "fam_61"], "PRESSURE_STRETCHED"),
                "post_event_pressure": _pressure_payload(["fam_62"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {
                    "fam_60": "PRESSURE_CAPTURED",
                    "fam_61": "PRESSURE_CAPTURED",
                },
                "post_capture_status_by_family": {"fam_62": "PRESSURE_CAPTURED"},
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_cross_band_self_check("evt_reunion_stretched_0001")

    assert out["self_check_state"] == "CROSS_BAND_PARTIAL"
    assert out["directional_alignment"]["pressure_alignment"] == "PRESSURE_ALIGNMENT_PARTIAL"
    assert out["evidence_surface"]["pre_event_directional_signal"] == "PRESSURE_SIGNAL_STRETCHED"
    assert "NO_CONTRADICTION_OBSERVED" not in out["contradiction_flags"]


def test_transition_cross_band_self_check_reunion_unclear_not_alignment(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_reunion_unclear_0001",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 6,
            "source_family_ids": ["fam_70", "fam_71"],
            "successor_family_ids": ["fam_72"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_70", "fam_71"], "PRESSURE_UNCLEAR"),
                "post_event_pressure": _pressure_payload(["fam_72"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {
                    "fam_70": "PRESSURE_CAPTURED",
                    "fam_71": "PRESSURE_CAPTURED",
                },
                "post_capture_status_by_family": {"fam_72": "PRESSURE_CAPTURED"},
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_cross_band_self_check("evt_reunion_unclear_0001")

    assert out["self_check_state"] == "CROSS_BAND_PARTIAL"
    assert out["directional_alignment"]["pressure_alignment"] == "PRESSURE_ALIGNMENT_PARTIAL"
    assert out["evidence_surface"]["pre_event_directional_signal"] == "PRESSURE_SIGNAL_UNCLEAR"


def test_transition_cross_band_self_check_fission_stretched_partial(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_fission_stretched_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 7,
            "source_family_ids": ["fam_80"],
            "successor_family_ids": ["fam_81", "fam_82"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_80"], "PRESSURE_STRETCHED"),
                "post_event_pressure": _pressure_payload(["fam_81", "fam_82"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {"fam_80": "PRESSURE_CAPTURED"},
                "post_capture_status_by_family": {
                    "fam_81": "PRESSURE_CAPTURED",
                    "fam_82": "PRESSURE_CAPTURED",
                },
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_transition_cross_band_self_check("evt_fission_stretched_0001")

    assert out["self_check_state"] == "CROSS_BAND_PARTIAL"
    assert out["directional_alignment"]["pressure_alignment"] == "PRESSURE_ALIGNMENT_PARTIAL"
    assert out["evidence_surface"]["pre_event_directional_signal"] == "PRESSURE_SIGNAL_STRETCHED"


def test_transition_cross_band_self_check_topology_only_contradiction_does_not_harden(tmp_path: Path, monkeypatch):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_topology_only_0001",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 8,
            "source_family_ids": ["fam_90", "fam_91"],
            "successor_family_ids": ["fam_92"],
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    def patched_topology(_event_id: str) -> dict:
        return {
            "event_id": "evt_topology_only_0001",
            "found": True,
            "topology_available": True,
            "topology_warnings": ["TOPOLOGY_COMPRESSION_RISK"],
            "event_identity": {
                "event_type": "FAMILY_REUNION_V1",
                "event_order": 8,
                "ledger_write_order": 1,
                "duplicate_event_id_count_in_ledger": 1,
            },
            "participants": {
                "source_family_ids": ["fam_90", "fam_91"],
                "successor_family_ids": ["fam_92"],
                "participant_family_ids": ["fam_90", "fam_91", "fam_92"],
            },
            "participant_topology": [
                {
                    "family_id": "fam_90",
                    "found": True,
                    "topology_available": True,
                    "shape_class": "SHAPE_DUAL_LOBE",
                    "compression_risk": True,
                }
            ],
            "compression_risk_family_ids": ["fam_90"],
        }

    monkeypatch.setattr(mem, "get_transition_topology_audit", patched_topology)
    out = mem.get_transition_cross_band_self_check("evt_topology_only_0001")

    assert out["self_check_state"] == "CROSS_BAND_PARTIAL"
    assert out["reason"] == "PARTIAL_DIRECTIONAL_EVIDENCE"
    assert "TOPOLOGY_EVENT_DIRECTION_CONTRADICTION" in out["contradiction_flags"]
    assert "PRESSURE_EVENT_DIRECTION_CONTRADICTION" not in out["contradiction_flags"]


def test_transition_cross_band_self_check_read_only_no_mutation(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    event_record = {
        "event_id": "evt_read_only_0001",
        "event_type": "FAMILY_FISSION_V1",
        "event_order": 5,
        "source_family_ids": ["fam_40"],
        "successor_family_ids": ["fam_41", "fam_42"],
    }
    _write_event(ledger, event_record)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    families_before = copy.deepcopy(mem._families)
    symbol_to_family_before = dict(mem._symbol_to_family)
    fission_before = mem.get_fission_events()
    reunion_before = mem.get_reunion_events()
    ledger_before = mem.get_event_ledger()

    out = mem.get_transition_cross_band_self_check("evt_read_only_0001")

    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False
    assert mem._families == families_before
    assert mem._symbol_to_family == symbol_to_family_before
    assert mem.get_fission_events() == fission_before
    assert mem.get_reunion_events() == reunion_before
    assert mem.get_event_ledger() == ledger_before


def test_transition_cross_band_self_check_no_repair_no_retrofit(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    legacy = {
        "event_id": "evt_legacy_no_snapshot_0001",
        "event_type": "FAMILY_REUNION_V1",
        "event_order": 6,
        "source_family_ids": ["fam_50", "fam_51"],
        "successor_family_ids": ["fam_52"],
    }
    _write_event(ledger, legacy)
    before = ledger.read_text(encoding="utf-8")
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    _ = mem.get_transition_cross_band_self_check("evt_legacy_no_snapshot_0001")

    after = ledger.read_text(encoding="utf-8")
    persisted = mem.get_event_ledger()[0]
    assert before == after
    assert persisted == legacy
