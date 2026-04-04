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


def _check_result(out: dict, check_name: str) -> dict:
    for chk in out.get("check_results", []):
        if chk.get("check_name") == check_name:
            return chk
    return {}


def test_stage_lock_passes_on_current_green_state(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_observability_stage_lock_audit()
    assert out["audit_available"] is True
    assert out["audit_mode"] == "OBSERVABILITY_STAGE_LOCK"
    assert out["lock_state"] == "OBSERVABILITY_STAGE_LOCKED"
    assert out["checks_failed"] == 0
    assert out["checks_passed"] == out["checks_run"]


def test_stage_lock_inconsistent_when_comparator_delta_direction_wrong(tmp_path: Path, monkeypatch):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    original = mem.get_pressure_capture_quality_window_comparator

    def wrong_comparator(*args, **kwargs):
        out = original(*args, **kwargs)
        if isinstance(out.get("comparison"), dict):
            out["comparison"]["window_event_count_delta"] = -999
        return out

    monkeypatch.setattr(mem, "get_pressure_capture_quality_window_comparator", wrong_comparator)
    out = mem.get_observability_stage_lock_audit()

    assert out["audit_available"] is True
    assert out["lock_state"] == "OBSERVABILITY_STAGE_LOCK_INCONSISTENT"
    chk = _check_result(out, "COMPARATOR_DELTA_DIRECTION_AND_MATH")
    assert chk.get("passed") is False


def test_stage_lock_inconsistent_when_bucket_surfaces_drift(tmp_path: Path, monkeypatch):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    original = mem.get_pressure_capture_quality_summary

    def drifted_summary():
        out = original()
        out["audit_state_counts"]["DRIFT_BUCKET"] = 1
        return out

    monkeypatch.setattr(mem, "get_pressure_capture_quality_summary", drifted_summary)
    out = mem.get_observability_stage_lock_audit()

    assert out["audit_available"] is True
    assert out["lock_state"] == "OBSERVABILITY_STAGE_LOCK_INCONSISTENT"
    chk = _check_result(out, "BUCKET_SURFACE_STABILITY")
    assert chk.get("passed") is False


def test_stage_lock_unavailable_when_required_surface_missing(tmp_path: Path, monkeypatch):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    monkeypatch.setattr(mem, "get_pressure_capture_quality_summary_window", None)
    out = mem.get_observability_stage_lock_audit()

    assert out["audit_available"] is False
    assert out["lock_state"] == "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE"
    assert out["reason"] == "REQUIRED_SURFACE_MISSING"


def test_stage_lock_read_only_no_mutation(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_ordered_transition_ledger(ledger)
    before = ledger.read_text(encoding="utf-8")
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_observability_stage_lock_audit()
    after = ledger.read_text(encoding="utf-8")

    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False
    assert before == after


def test_stage_lock_no_repair_no_retrofit(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    legacy = {
        "event_id": "evt_legacy_missing_snapshot",
        "event_type": "FAMILY_REUNION_V1",
        "event_order": 7,
        "source_family_ids": ["fam_20", "fam_21"],
        "successor_family_ids": ["fam_22"],
    }
    _write_event(ledger, legacy)
    before = ledger.read_text(encoding="utf-8")
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    _ = mem.get_observability_stage_lock_audit()
    after = ledger.read_text(encoding="utf-8")
    persisted = mem.get_event_ledger()[0]

    assert before == after
    assert persisted == legacy
