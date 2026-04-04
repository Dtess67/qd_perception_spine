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


def _write_cross_band_comparator_ledger(path: Path) -> None:
    _write_event(
        path,
        {
            "event_id": "evt_cmp_01_align_fission",
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
            "event_id": "evt_cmp_02_contradict_fission",
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
            "event_id": "evt_cmp_03_partial_reunion",
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
            "event_id": "evt_cmp_04_unavailable",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 4,
            "source_family_ids": ["fam_30"],
            "successor_family_ids": ["fam_31", "fam_32"],
        },
    )
    _write_event(
        path,
        {
            "event_id": "evt_cmp_05_align_reunion",
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


def test_cross_band_window_comparator_both_available_and_matching(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_comparator_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_window_comparator()
    assert out["comparison_available"] is True
    assert out["reason"] == "WINDOW_SUMMARIES_MATCH"
    assert out["mismatch_flags"] == ["NO_MISMATCH_DETECTED"]
    assert out["comparison"]["window_event_count_delta"] == 0
    assert out["comparison"]["auditable_event_count_delta"] == 0
    assert all(v == 0 for v in out["comparison"]["self_check_state_count_deltas"].values())
    assert all(v == 0 for v in out["comparison"]["contradiction_flag_count_deltas"].values())
    assert all(v == 0 for v in out["comparison"]["event_type_count_deltas"].values())


def test_cross_band_window_comparator_both_available_and_differing(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_comparator_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_window_comparator(
        start_index=0,
        end_index=2,
        start_event_order=3,
        end_event_order=5,
    )
    assert out["comparison_available"] is True
    assert out["reason"] == "WINDOW_SUMMARIES_DIFFER"
    assert "WINDOW_COUNT_MISMATCH" in out["mismatch_flags"]
    assert "SELF_CHECK_STATE_MISMATCH" in out["mismatch_flags"]
    assert "CONTRADICTION_FLAG_MISMATCH" in out["mismatch_flags"]
    assert "EVENT_TYPE_MISMATCH" in out["mismatch_flags"]
    assert "NO_MISMATCH_DETECTED" not in out["mismatch_flags"]


def test_cross_band_window_comparator_index_unavailable_event_order_available(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_comparator_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_window_comparator(
        start_index=4,
        end_index=1,
        start_event_order=1,
        end_event_order=5,
    )
    assert out["comparison_available"] is True
    assert out["reason"] == "INDEX_WINDOW_UNAVAILABLE"
    assert "INDEX_WINDOW_UNAVAILABLE" in out["mismatch_flags"]
    assert "EVENT_ORDER_WINDOW_UNAVAILABLE" not in out["mismatch_flags"]


def test_cross_band_window_comparator_event_order_unavailable_index_available(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_comparator_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_window_comparator(
        start_index=0,
        end_index=5,
        start_event_order=5,
        end_event_order=2,
    )
    assert out["comparison_available"] is True
    assert out["reason"] == "EVENT_ORDER_WINDOW_UNAVAILABLE"
    assert "EVENT_ORDER_WINDOW_UNAVAILABLE" in out["mismatch_flags"]
    assert "INDEX_WINDOW_UNAVAILABLE" not in out["mismatch_flags"]


def test_cross_band_window_comparator_both_unavailable(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_comparator_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_window_comparator(
        start_index=4,
        end_index=1,
        start_event_order=5,
        end_event_order=2,
    )
    assert out["comparison_available"] is False
    assert out["reason"] == "BOTH_WINDOWS_UNAVAILABLE"
    assert "INDEX_WINDOW_UNAVAILABLE" in out["mismatch_flags"]
    assert "EVENT_ORDER_WINDOW_UNAVAILABLE" in out["mismatch_flags"]


def test_cross_band_window_comparator_delta_math_by_bucket(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_comparator_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_window_comparator(
        start_index=0,
        end_index=2,
        start_event_order=1,
        end_event_order=3,
    )

    # index window: events 1-2, event_order window: events 1-3
    assert out["comparison"]["window_event_count_delta"] == 1
    assert out["comparison"]["auditable_event_count_delta"] == 1
    assert out["comparison"]["self_check_state_count_deltas"] == {
        "CROSS_BAND_ALIGNMENT_OBSERVED": 0,
        "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
        "CROSS_BAND_PARTIAL": 1,
        "CROSS_BAND_UNAVAILABLE": 0,
    }
    assert out["comparison"]["contradiction_flag_count_deltas"] == {
        "EVIDENCE_INSUFFICIENT": 1,
        "NO_CONTRADICTION_OBSERVED": 0,
        "PRESSURE_EVENT_DIRECTION_CONTRADICTION": 0,
        "TOPOLOGY_EVENT_DIRECTION_CONTRADICTION": 0,
    }
    assert out["comparison"]["event_type_count_deltas"] == {
        "FAMILY_FISSION": 0,
        "FAMILY_REUNION": 1,
    }


def test_cross_band_window_comparator_mismatch_flags_correctness(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_comparator_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out_match = mem.get_cross_band_self_check_window_comparator()
    assert out_match["mismatch_flags"] == ["NO_MISMATCH_DETECTED"]

    out_diff = mem.get_cross_band_self_check_window_comparator(
        start_index=0,
        end_index=2,
        start_event_order=3,
        end_event_order=5,
    )
    assert "NO_MISMATCH_DETECTED" not in out_diff["mismatch_flags"]


def test_cross_band_window_comparator_read_only_no_repair_no_retrofit(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_cross_band_comparator_ledger(ledger)
    before = ledger.read_text(encoding="utf-8")
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_self_check_window_comparator()
    after = ledger.read_text(encoding="utf-8")

    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False
    assert before == after
