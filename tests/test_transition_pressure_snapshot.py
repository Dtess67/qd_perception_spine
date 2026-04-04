import copy
import json
from pathlib import Path

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _emit_fission_and_reunion_chain(mem: NeutralFamilyMemoryV1) -> None:
    spread = _spr(0.05)
    for i in range(8):
        sid = f"sym_t_{i}"
        for _ in range(2):
            mem.join_or_create_family(sid, _sig(0.5 + (i * 0.01)), spread, 10)

    for _ in range(30):
        for i in range(3):
            mem.join_or_create_family(f"sym_t_{i}", _sig(0.1), spread, 10)
        for i in range(5, 8):
            mem.join_or_create_family(f"sym_t_{i}", _sig(0.9), spread, 10)
        if mem.get_fission_events():
            break

    fission_evt = mem.get_fission_events()[0]
    g1 = list(fission_evt["partition"]["group_1_member_ids"])
    g2 = list(fission_evt["partition"]["group_2_member_ids"])
    for _ in range(40):
        for sid in g1:
            mem.join_or_create_family(sid, _sig(0.20), spread, 10)
        for sid in g2:
            mem.join_or_create_family(sid, _sig(0.22), spread, 10)
        if mem.get_reunion_events():
            break


def _write_event(path: Path, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def test_transition_pressure_snapshot_event_not_found(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    snap = mem.get_transition_pressure_snapshot("evt_unknown_0001")
    assert snap["found"] is False
    assert snap["snapshot_available"] is False
    assert snap["reason"] == "EVENT_NOT_FOUND"
    assert snap["pre_event_pressure"] is None
    assert snap["post_event_pressure"] is None
    assert snap["lineage_mutation_performed"] is False
    assert snap["event_creation_performed"] is False
    assert snap["history_rewrite_performed"] is False


def test_transition_pressure_snapshot_event_found_but_unrecoverable(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "legacy_evt_unrecoverable_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_01"],
            "successor_family_ids": ["fam_02", "fam_03"],
            "gate_summary": {"legacy_without_pressure_snapshot": True},
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    snap = mem.get_transition_pressure_snapshot("legacy_evt_unrecoverable_0001")
    assert snap["found"] is True
    assert snap["snapshot_available"] is False
    assert snap["reason"] == "PRESSURE_SNAPSHOT_UNRECOVERABLE"
    assert snap["pre_event_pressure"] is None
    assert snap["post_event_pressure"] is None
    assert "EVENT_PRESSURE_SNAPSHOT_NOT_STORED" in snap["warnings"]
    assert "PRE_EVENT_PRESSURE_UNRECOVERABLE" in snap["warnings"]
    assert "POST_EVENT_PRESSURE_UNRECOVERABLE" in snap["warnings"]


def test_transition_pressure_snapshot_partial_recoverability(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_partial_0001",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_10", "fam_11"],
            "successor_family_ids": ["fam_12"],
            "pressure_snapshot": {
                "post_event_pressure": {
                    "family_pressure_by_id": {
                        "fam_12": {"pressure_state": "PRESSURE_STABLE"}
                    }
                }
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    snap = mem.get_transition_pressure_snapshot("evt_partial_0001")
    assert snap["found"] is True
    assert snap["snapshot_available"] is True
    assert snap["reason"] == "PRESSURE_SNAPSHOT_PARTIAL"
    assert snap["pre_event_pressure"] is None
    assert snap["post_event_pressure"] is not None
    assert snap["evidence_flags"]["pre_event_pressure_recoverable"] is False
    assert snap["evidence_flags"]["post_event_pressure_recoverable"] is True


def test_transition_pressure_snapshot_full_recoverability(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_event(
        ledger,
        {
            "event_id": "evt_full_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 2,
            "source_family_ids": ["fam_20"],
            "successor_family_ids": ["fam_21", "fam_22"],
            "pressure_snapshot": {
                "pre_event_pressure": {
                    "family_pressure_by_id": {
                        "fam_20": {"pressure_state": "PRESSURE_FISSION_PRONE"}
                    }
                },
                "post_event_pressure": {
                    "family_pressure_by_id": {
                        "fam_21": {"pressure_state": "PRESSURE_STABLE"},
                        "fam_22": {"pressure_state": "PRESSURE_STRETCHED"},
                    }
                },
            },
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    snap = mem.get_transition_pressure_snapshot("evt_full_0001")
    assert snap["found"] is True
    assert snap["snapshot_available"] is True
    assert snap["reason"] == "PRESSURE_SNAPSHOT_RECOVERED"
    assert snap["pre_event_pressure"] is not None
    assert snap["post_event_pressure"] is not None
    assert snap["evidence_flags"]["pre_event_pressure_recoverable"] is True
    assert snap["evidence_flags"]["post_event_pressure_recoverable"] is True


def test_transition_pressure_snapshot_is_diagnostic_only_no_mutation_no_inference(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)
    evt_id = mem.get_fission_events()[0]["event_id"]

    families_before = copy.deepcopy(mem._families)
    symbol_to_family_before = dict(mem._symbol_to_family)
    fission_before = mem.get_fission_events()
    reunion_before = mem.get_reunion_events()
    ledger_before = mem.get_event_ledger()

    snap = mem.get_transition_pressure_snapshot(evt_id)

    assert snap["evidence_flags"]["inferred_from_current_family_state"] is False
    assert snap["lineage_mutation_performed"] is False
    assert snap["event_creation_performed"] is False
    assert snap["history_rewrite_performed"] is False

    assert mem._families == families_before
    assert mem._symbol_to_family == symbol_to_family_before
    assert mem.get_fission_events() == fission_before
    assert mem.get_reunion_events() == reunion_before
    assert mem.get_event_ledger() == ledger_before
