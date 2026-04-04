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


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return len([line for line in f if line.strip()])


def test_fission_writes_exactly_one_durable_ledger_event(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    _trigger_fission(mem)

    assert len(mem.get_fission_events()) == 1
    assert _line_count(ledger) == 1
    evt = mem.get_event_ledger()[0]
    assert evt["event_type"] == "FAMILY_FISSION_V1"
    assert evt["source_family_ids"] == ["fam_01"]
    assert len(evt["successor_family_ids"]) == 2


def test_reunion_writes_exactly_one_durable_ledger_event(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    _trigger_reunion(mem)

    assert len(mem.get_reunion_events()) == 1
    assert _line_count(ledger) == 1
    evt = mem.get_event_ledger()[0]
    assert evt["event_type"] == "FAMILY_REUNION_V1"
    assert evt["source_family_ids"] == ["fam_01", "fam_02"]
    assert evt["successor_family_ids"] == ["fam_03"]


def test_readback_and_query_for_family_id_returns_relevant_events(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"

    mem_f = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _trigger_fission(mem_f)
    mem_r = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _trigger_reunion(mem_r)

    read_mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    all_events = read_mem.get_event_ledger()
    assert len(all_events) == 2

    fam_01_events = read_mem.get_events_for_family("fam_01")
    assert len(fam_01_events) == 2
    assert set(evt["event_type"] for evt in fam_01_events) == {"FAMILY_FISSION_V1", "FAMILY_REUNION_V1"}


def test_duplicate_write_for_same_event_id_does_not_append_twice(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _trigger_fission(mem)
    assert len(mem.get_fission_events()) == 1

    evt = mem.get_fission_events()[0]
    before = _line_count(ledger)
    mem._append_durable_event(evt)
    after = _line_count(ledger)
    assert before == 1
    assert after == 1


def test_in_memory_lineage_behavior_remains_available_with_durable_ledger(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _trigger_reunion(mem)

    assert len(mem.get_reunion_events()) == 1
    evt = mem.get_reunion_events()[0]
    successor = evt["successor_family_id"]
    src_a, src_b = evt["source_family_ids"]

    rec_a = mem.get_family_record(src_a)
    rec_b = mem.get_family_record(src_b)
    rec_s = mem.get_family_record(successor)
    assert rec_a.lifecycle_status == "FAMILY_INACTIVE_SUCCESSOR_REUNION"
    assert rec_b.lifecycle_status == "FAMILY_INACTIVE_SUCCESSOR_REUNION"
    assert rec_s.lineage_parent_family_ids == [src_a, src_b]
