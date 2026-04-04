import json
from pathlib import Path

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _trigger_fission(mem: NeutralFamilyMemoryV1) -> None:
    spread = _spr(0.05)
    for i in range(8):
        sid = f"sym_f_{i}"
        for _ in range(2):
            mem.join_or_create_family(sid, _sig(0.5 + (i * 0.01)), spread, 10)
    for _ in range(30):
        for i in range(3):
            mem.join_or_create_family(f"sym_f_{i}", _sig(0.1), spread, 10)
        for i in range(5, 8):
            mem.join_or_create_family(f"sym_f_{i}", _sig(0.9), spread, 10)
        if mem.get_fission_events():
            return


def _trigger_reunion(mem: NeutralFamilyMemoryV1) -> None:
    spread = _spr(0.05)
    mem.join_or_create_family("sym_ra0", _sig(0.10), spread, 10)
    mem.join_or_create_family("sym_ra1", _sig(0.11), spread, 10)
    mem.join_or_create_family("sym_ra1", _sig(0.11), spread, 10)
    mem.join_or_create_family("sym_rb0", _sig(0.80), spread, 10)
    mem.join_or_create_family("sym_rb1", _sig(0.81), spread, 10)
    mem.join_or_create_family("sym_rb1", _sig(0.81), spread, 10)
    for _ in range(12):
        mem.join_or_create_family("sym_ra0", _sig(0.20), spread, 10)
        mem.join_or_create_family("sym_ra1", _sig(0.20), spread, 10)
        mem.join_or_create_family("sym_rb0", _sig(0.22), spread, 10)
        mem.join_or_create_family("sym_rb1", _sig(0.22), spread, 10)
        if mem.get_reunion_events():
            return


def test_origin_query_for_fission_successor(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _trigger_fission(mem)

    origin = mem.get_family_origin("fam_02")
    assert origin["found"] is True
    assert origin["origin_event_type"] == "FAMILY_FISSION_V1"
    assert origin["parent_family_ids"] == ["fam_01"]


def test_origin_query_for_reunion_successor(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _trigger_reunion(mem)

    origin = mem.get_family_origin("fam_03")
    assert origin["found"] is True
    assert origin["origin_event_type"] == "FAMILY_REUNION_V1"
    assert origin["parent_family_ids"] == ["fam_01", "fam_02"]


def test_successor_query_for_fissioned_family(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _trigger_fission(mem)

    successors = mem.get_family_successors("fam_01", recursive=False)
    assert successors["direct_successor_family_ids"] == ["fam_02", "fam_03"]


def test_events_for_family_and_ancestry_results_are_consistent(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _trigger_fission(mem)

    event_records = mem.get_events_for_family("fam_02")
    transition = mem.get_family_transition_events("fam_02")
    assert len(event_records) == transition["event_count"] == 1
    assert event_records[0]["event_id"] == transition["events"][0]["event_id"]


def test_shared_ancestry_true_when_families_share_parent(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _trigger_fission(mem)

    shared = mem.families_share_ancestry("fam_02", "fam_03")
    assert shared["shares_ancestry"] is True
    assert "fam_01" in shared["shared_ancestor_ids"]


def test_shared_ancestry_false_when_families_do_not_share_lineage(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    spread = _spr(0.05)
    mem.join_or_create_family("sym_u0", _sig(0.10), spread, 10)
    mem.join_or_create_family("sym_u1", _sig(0.80), spread, 10)

    shared = mem.families_share_ancestry("fam_01", "fam_02")
    assert shared["shares_ancestry"] is False
    assert shared["shared_ancestor_ids"] == []


def test_lineage_traversal_obeys_max_depth_and_loop_guard(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    # Synthetic cyclic ledger records to verify loop guard behavior.
    events = [
        {
            "event_id": "evt_cycle_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_a"],
            "successor_family_ids": ["fam_b"],
            "gate_summary": {},
            "rationale": "cycle_a_to_b",
        },
        {
            "event_id": "evt_cycle_0002",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 2,
            "source_family_ids": ["fam_b"],
            "successor_family_ids": ["fam_a"],
            "gate_summary": {},
            "rationale": "cycle_b_to_a",
        },
    ]
    with ledger.open("w", encoding="utf-8") as f:
        for evt in events:
            f.write(json.dumps(evt, sort_keys=True, separators=(",", ":")) + "\n")

    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    lineage_depth_0 = mem.get_family_lineage("fam_b", max_depth=0)
    assert lineage_depth_0["truncated"] is True

    lineage_deep = mem.get_family_lineage("fam_b", max_depth=6)
    assert lineage_deep["loop_detected"] is True


def test_unknown_family_handling_is_fail_closed_and_explicit(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    origin = mem.get_family_origin("fam_unknown")
    lineage = mem.get_family_lineage("fam_unknown", max_depth=5)
    shared = mem.families_share_ancestry("fam_unknown", "fam_other_unknown")

    assert origin["found"] is False
    assert origin["family_known"] is False
    assert lineage["family_known"] is False
    assert lineage["lineage_nodes"] == []
    assert shared["shares_ancestry"] is False
    assert shared["family_a_known"] is False
