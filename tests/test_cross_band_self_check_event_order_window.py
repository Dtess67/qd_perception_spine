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


def _write_cross_band_event_order_ledger(path: Path) -> None:
    _write_event(
        path,
        {
            "event_id": "evt_eo_01_align_fission",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_01"],
            "successor_family_ids": ["fam_02", "fam_03"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_01"], "PRESSURE_FISSION_PRONE"),
                "post_event_pressure": _pressure_payload(["fam_02", "fam_03"], "PRESSURE_STABLE"),
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "evt_eo_02_contradiction_fission",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 2,
            "source_family_ids": ["fam_10"],
            "successor_family_ids": ["fam_11", "fam_12"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_10"], "PRESSURE_STABLE"),
                "post_event_pressure": _pressure_payload(["fam_11", "fam_12"], "PRESSURE_STABLE"),
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "evt_eo_03_partial_reunion",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 3,
            "source_family_ids": ["fam_20", "fam_21"],
            "successor_family_ids": ["fam_22"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_20", "fam_21"], "PRESSURE_STRETCHED"),
                "post_event_pressure": _pressure_payload(["fam_22"], "PRESSURE_STABLE"),
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "evt_eo_04_unavailable",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 4,
            "source_family_ids": ["fam_30"],
            "successor_family_ids": ["fam_31", "fam_32"],
        },
    )
    _write_event(
        path,
        {
            "event_id": "evt_eo_05_align_reunion",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 5,
            "source_family_ids": ["fam_40", "fam_41"],
            "successor_family_ids": ["fam_42"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_40", "fam_41"], "PRESSURE_STABLE"),
                "post_event_pressure": _pressure_payload(["fam_42"], "PRESSURE_STABLE"),
            },
        },
    )


def test_cross_band_self_check_event_order_window_no_transition_events(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_event_order_window()
    assert out["summary_mode"] == "CROSS_BAND_SELF_CHECK_EVENT_ORDER_WINDOW"
    assert out["summary_available"] is True
    assert out["reason"] == "NO_TRANSITION_EVENTS"
    assert out["total_transition_events"] == 0
    assert out["total_event_order_eligible_events"] == 0
    assert out["window_event_count"] == 0
    assert out["auditable_event_count"] == 0


def test_cross_band_self_check_event_order_window_no_event_order_eligible_events(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_eo_none_01",
            "event_type": "FAMILY_FISSION_V1",
            "source_family_ids": ["fam_01"],
            "successor_family_ids": ["fam_02", "fam_03"],
        },
    )
    _write_event(
        ledger,
        {
            "event_id": "evt_eo_none_02",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": "bad_type",
            "source_family_ids": ["fam_10", "fam_11"],
            "successor_family_ids": ["fam_12"],
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_event_order_window()
    assert out["summary_available"] is False
    assert out["reason"] == "NO_EVENT_ORDER_ELIGIBLE_EVENTS"
    assert out["total_transition_events"] == 2
    assert out["total_event_order_eligible_events"] == 0
    assert "EVENT_ORDER_INELIGIBLE_EVENTS_SKIPPED" in out["warnings"]


def test_cross_band_self_check_event_order_window_invalid_bounds_fail_closed(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_event_order_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_event_order_window(start_event_order=5, end_event_order=2)
    assert out["summary_available"] is False
    assert out["reason"] == "INVALID_EVENT_ORDER_BOUNDS"
    assert "INVALID_EVENT_ORDER_BOUNDS" in out["warnings"]
    assert out["window_event_count"] == 0


def test_cross_band_self_check_event_order_window_empty_valid_selection(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_event_order_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_event_order_window(start_event_order=9, end_event_order=10)
    assert out["summary_available"] is True
    assert out["reason"] == "EMPTY_EVENT_ORDER_WINDOW_SELECTION"
    assert out["window_event_count"] == 0
    assert "EMPTY_EVENT_ORDER_WINDOW_SELECTION" in out["warnings"]


def test_cross_band_self_check_event_order_window_mixed_states(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_event_order_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_event_order_window(start_event_order=1, end_event_order=4)
    assert out["summary_available"] is True
    assert out["reason"] == "OK"
    assert out["window_event_count"] == 4
    assert out["auditable_event_count"] == 4
    assert out["self_check_state_counts"] == {
        "CROSS_BAND_ALIGNMENT_OBSERVED": 1,
        "CROSS_BAND_CONTRADICTION_OBSERVED": 1,
        "CROSS_BAND_PARTIAL": 1,
        "CROSS_BAND_UNAVAILABLE": 1,
    }


def test_cross_band_self_check_event_order_window_max_events_after_filtering(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_event_order_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_event_order_window(
        start_event_order=1,
        end_event_order=5,
        max_events=2,
    )
    assert out["summary_available"] is True
    assert out["window_event_count"] == 2
    assert out["auditable_event_count"] == 2
    assert out["window_spec"]["applied_start_event_order"] == 1.0
    assert out["window_spec"]["applied_end_event_order"] == 2.0
    assert out["event_type_counts"] == {"FAMILY_FISSION": 2}


def test_cross_band_self_check_event_order_window_deterministic_tie_behavior(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_eo_tie_01",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 10,
            "source_family_ids": ["fam_01", "fam_02"],
            "successor_family_ids": ["fam_03"],
        },
    )
    _write_event(
        ledger,
        {
            "event_id": "evt_eo_tie_02",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 10,
            "source_family_ids": ["fam_10"],
            "successor_family_ids": ["fam_11", "fam_12"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_10"], "PRESSURE_FISSION_PRONE"),
                "post_event_pressure": _pressure_payload(["fam_11", "fam_12"], "PRESSURE_STABLE"),
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_event_order_window(
        start_event_order=10,
        end_event_order=10,
        max_events=1,
    )
    assert out["summary_available"] is True
    assert out["window_event_count"] == 1
    assert out["event_type_counts"] == {"FAMILY_REUNION": 1}
    assert out["self_check_state_counts"] == {
        "CROSS_BAND_ALIGNMENT_OBSERVED": 0,
        "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
        "CROSS_BAND_PARTIAL": 0,
        "CROSS_BAND_UNAVAILABLE": 1,
    }


def test_cross_band_self_check_event_order_window_contradiction_flag_aggregation(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_event_order_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_event_order_window(start_event_order=1, end_event_order=5)
    flags = out["contradiction_flag_counts"]

    assert flags["PRESSURE_EVENT_DIRECTION_CONTRADICTION"] == 1
    assert flags["NO_CONTRADICTION_OBSERVED"] == 2
    assert flags["EVIDENCE_INSUFFICIENT"] == 2
    assert flags["TOPOLOGY_EVENT_DIRECTION_CONTRADICTION"] == 0


def test_cross_band_self_check_event_order_window_event_type_count_correctness(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_event_order_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_summary_event_order_window(start_event_order=2, end_event_order=4)
    assert out["event_type_counts"] == {
        "FAMILY_FISSION": 2,
        "FAMILY_REUNION": 1,
    }


def test_cross_band_self_check_event_order_window_read_only_no_mutation(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_event_order_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    families_before = copy.deepcopy(mem._families)
    symbol_to_family_before = dict(mem._symbol_to_family)
    fission_before = mem.get_fission_events()
    reunion_before = mem.get_reunion_events()
    ledger_before = mem.get_event_ledger()

    out = mem.get_cross_band_self_check_summary_event_order_window(start_event_order=1, end_event_order=5)

    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False
    assert mem._families == families_before
    assert mem._symbol_to_family == symbol_to_family_before
    assert mem.get_fission_events() == fission_before
    assert mem.get_reunion_events() == reunion_before
    assert mem.get_event_ledger() == ledger_before


def test_cross_band_self_check_event_order_window_no_repair_no_retrofit(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    legacy = {
        "event_id": "evt_eo_legacy_0001",
        "event_type": "FAMILY_REUNION_V1",
        "event_order": 7,
        "source_family_ids": ["fam_90", "fam_91"],
        "successor_family_ids": ["fam_92"],
    }
    _write_event(ledger, legacy)
    before = ledger.read_text(encoding="utf-8")

    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    out = mem.get_cross_band_self_check_summary_event_order_window(start_event_order=7, end_event_order=7)

    after = ledger.read_text(encoding="utf-8")
    persisted = mem.get_event_ledger()[0]
    assert out["summary_available"] is True
    assert out["window_event_count"] == 1
    assert out["self_check_state_counts"]["CROSS_BAND_UNAVAILABLE"] == 1
    assert before == after
    assert persisted == legacy
