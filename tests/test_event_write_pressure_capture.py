import json
from pathlib import Path

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _seed_family(mem: NeutralFamilyMemoryV1, prefix: str, member_count: int) -> tuple[str, list[str]]:
    spread = _spr(0.05)
    members: list[str] = []
    for i in range(member_count):
        sid = f"{prefix}_{i}"
        members.append(sid)
        mem.join_or_create_family(sid, _sig(0.50), spread, 10)
        if i > 0:
            mem.join_or_create_family(sid, _sig(0.50), spread, 10)
    return "fam_01", members


def _write_jsonl(path: Path, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def test_new_fission_event_writes_full_pressure_capture_when_both_sides_available(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, members = _seed_family(mem, "sym_full", 8)

    mem._execute_family_fission(fam_id, members[:4], members[4:], "test full capture")
    evt = mem.get_fission_events()[0]
    snap = evt["pressure_snapshot"]

    assert snap["capture_attempted"] is True
    assert snap["capture_succeeded"] is True
    assert snap["capture_mode"] == "EVENT_WRITE_TIME"
    assert snap["capture_reason"] == "PRESSURE_CAPTURE_FULL"
    assert snap["pre_event_pressure"] is not None
    assert snap["post_event_pressure"] is not None


def test_new_fission_event_writes_partial_capture_when_only_one_side_available(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, members = _seed_family(mem, "sym_partial", 6)

    mem._execute_family_fission(fam_id, members[:3], members[3:], "test partial capture")
    evt = mem.get_fission_events()[0]
    snap = evt["pressure_snapshot"]

    assert snap["capture_attempted"] is True
    assert snap["capture_succeeded"] is True
    assert snap["capture_reason"] == "PRESSURE_CAPTURE_PARTIAL"
    assert snap["pre_event_pressure"] is not None
    assert snap["post_event_pressure"] is None


def test_event_is_written_when_capture_fails_and_failure_is_recorded(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, members = _seed_family(mem, "sym_fail", 8)

    original = mem.get_family_pressure_forecast
    mem.get_family_pressure_forecast = lambda _family_id: (_ for _ in ()).throw(RuntimeError("simulated_capture_failure"))
    try:
        mem._execute_family_fission(fam_id, members[:4], members[4:], "test capture failure")
    finally:
        mem.get_family_pressure_forecast = original

    assert len(mem.get_fission_events()) == 1
    evt = mem.get_fission_events()[0]
    snap = evt["pressure_snapshot"]
    assert snap["capture_attempted"] is True
    assert snap["capture_succeeded"] is False
    assert snap["capture_reason"] == "PRESSURE_CAPTURE_FAILED"
    assert snap["pre_event_pressure"] is None
    assert snap["post_event_pressure"] is None
    assert any("PRESSURE_CAPTURE_EXCEPTION" in v for v in snap["pre_capture_status_by_family"].values())


def test_transition_snapshot_reader_recovers_event_write_time_pressure_block(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, members = _seed_family(mem, "sym_reader", 8)

    mem._execute_family_fission(fam_id, members[:4], members[4:], "test reader recoverability")
    evt = mem.get_fission_events()[0]
    report = mem.get_transition_pressure_snapshot(evt["event_id"])

    assert report["found"] is True
    assert report["snapshot_available"] is True
    assert report["pre_event_pressure"] is not None
    assert report["post_event_pressure"] is not None
    assert report["capture_metadata"]["capture_mode"] == "EVENT_WRITE_TIME"
    assert report["evidence_flags"]["event_pressure_snapshot_field_present"] is True


def test_old_events_are_not_retrofitted_or_mutated(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    old_record = {
        "event_id": "legacy_evt_0001",
        "event_type": "FAMILY_FISSION_V1",
        "event_order": 1,
        "source_family_ids": ["fam_00"],
        "successor_family_ids": ["fam_01", "fam_02"],
        "gate_summary": {"legacy": True},
    }
    _write_jsonl(ledger, old_record)

    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, members = _seed_family(mem, "sym_new", 8)
    mem._execute_family_fission(fam_id, members[:4], members[4:], "new event after legacy")

    events = mem.get_event_ledger()
    assert events[0] == old_record
    assert "pressure_snapshot" not in events[0]
    assert "pressure_snapshot" in events[1]


def test_pressure_capture_does_not_change_lineage_outcome(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, members = _seed_family(mem, "sym_outcome", 8)

    symbol_to_family_before = dict(mem._symbol_to_family)
    mem._execute_family_fission(fam_id, members[:4], members[4:], "lineage outcome unchanged")

    assert len(mem.get_fission_events()) == 1
    parent = mem.get_family_record("fam_01")
    succ_a = mem.get_family_record("fam_02")
    succ_b = mem.get_family_record("fam_03")
    assert parent.lifecycle_status == "FAMILY_INACTIVE_SUCCESSOR_SPLIT"
    assert parent.member_symbol_ids == []
    assert sorted(parent.historical_member_symbol_ids) == sorted(members)
    assert succ_a is not None and succ_b is not None
    assert succ_a.lifecycle_status == "FAMILY_ACTIVE"
    assert succ_b.lifecycle_status == "FAMILY_ACTIVE"
    assert sorted(succ_a.member_symbol_ids + succ_b.member_symbol_ids) == sorted(members)
    for sid in members:
        assert mem._symbol_to_family[sid] in {"fam_02", "fam_03"}
    assert set(symbol_to_family_before.keys()).issubset(set(mem._symbol_to_family.keys()))
