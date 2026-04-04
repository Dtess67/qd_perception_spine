from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _setup_two_active_families(mem: NeutralFamilyMemoryV1, spread_value: float = 0.05) -> tuple[str, str]:
    spread = _spr(spread_value)

    mem.join_or_create_family("sym_a0", _sig(0.10), spread, 10)
    mem.join_or_create_family("sym_a1", _sig(0.11), spread, 10)
    mem.join_or_create_family("sym_a1", _sig(0.11), spread, 10)

    mem.join_or_create_family("sym_b0", _sig(0.80), spread, 10)
    mem.join_or_create_family("sym_b1", _sig(0.81), spread, 10)
    mem.join_or_create_family("sym_b1", _sig(0.81), spread, 10)

    return "fam_01", "fam_02"


def _drive_family_toward(mem: NeutralFamilyMemoryV1, symbol_ids: list[str], target_value: float, spread_value: float = 0.05) -> None:
    for sid in symbol_ids:
        mem.join_or_create_family(sid, _sig(target_value), _spr(spread_value), 10)


def test_one_favorable_observation_alone_does_not_trigger_reunion():
    mem = NeutralFamilyMemoryV1()
    mem.REUNION_PERSISTENCE_THRESHOLD = 6

    fam_a, fam_b = _setup_two_active_families(mem)

    # One favorable closeness step only.
    _drive_family_toward(mem, ["sym_a0", "sym_a1"], 0.20)
    _drive_family_toward(mem, ["sym_b0", "sym_b1"], 0.22)

    assert len(mem.get_reunion_events()) == 0
    assert mem.get_family_record(fam_a).lifecycle_status == "FAMILY_ACTIVE"
    assert mem.get_family_record(fam_b).lifecycle_status == "FAMILY_ACTIVE"


def test_repeated_structural_closeness_with_compatible_spreads_triggers_reunion():
    mem = NeutralFamilyMemoryV1()

    _setup_two_active_families(mem)

    for _ in range(10):
        _drive_family_toward(mem, ["sym_a0", "sym_a1"], 0.20)
        _drive_family_toward(mem, ["sym_b0", "sym_b1"], 0.22)
        if len(mem.get_reunion_events()) > 0:
            break

    events = mem.get_reunion_events()
    assert len(events) == 1
    evt = events[0]
    assert evt["source_family_ids"] == ["fam_01", "fam_02"]
    assert evt["successor_family_id"] == "fam_03"


def test_reunion_creates_new_successor_family_without_overwriting_sources():
    mem = NeutralFamilyMemoryV1()
    _setup_two_active_families(mem)

    for _ in range(10):
        _drive_family_toward(mem, ["sym_a0", "sym_a1"], 0.20)
        _drive_family_toward(mem, ["sym_b0", "sym_b1"], 0.22)
        if len(mem.get_reunion_events()) > 0:
            break

    evt = mem.get_reunion_events()[0]
    successor_id = evt["successor_family_id"]
    assert successor_id not in ["fam_01", "fam_02"]
    assert mem.get_family_record("fam_01") is not None
    assert mem.get_family_record("fam_02") is not None
    assert mem.get_family_record(successor_id) is not None


def test_source_families_remain_traceable_and_not_silently_active_after_reunion():
    mem = NeutralFamilyMemoryV1()
    _setup_two_active_families(mem)

    for _ in range(10):
        _drive_family_toward(mem, ["sym_a0", "sym_a1"], 0.20)
        _drive_family_toward(mem, ["sym_b0", "sym_b1"], 0.22)
        if len(mem.get_reunion_events()) > 0:
            break

    evt = mem.get_reunion_events()[0]
    successor_id = evt["successor_family_id"]

    src_a = mem.get_family_record("fam_01")
    src_b = mem.get_family_record("fam_02")
    successor = mem.get_family_record(successor_id)

    assert src_a.lifecycle_status == "FAMILY_INACTIVE_SUCCESSOR_REUNION"
    assert src_b.lifecycle_status == "FAMILY_INACTIVE_SUCCESSOR_REUNION"
    assert src_a.member_symbol_ids == []
    assert src_b.member_symbol_ids == []
    assert len(src_a.historical_member_symbol_ids) == 2
    assert len(src_b.historical_member_symbol_ids) == 2
    assert src_a.lineage_successor_family_ids == [successor_id]
    assert src_b.lineage_successor_family_ids == [successor_id]
    assert evt["event_id"] in src_a.reunion_event_ids
    assert evt["event_id"] in src_b.reunion_event_ids

    assert successor.lineage_parent_family_ids == ["fam_01", "fam_02"]
    assert successor.lineage_reunion_event_id == evt["event_id"]
    assert evt["event_id"] in successor.reunion_event_ids


def test_symbol_identity_intact_and_one_family_only_after_reunion():
    mem = NeutralFamilyMemoryV1()
    _setup_two_active_families(mem)

    for _ in range(10):
        _drive_family_toward(mem, ["sym_a0", "sym_a1"], 0.20)
        _drive_family_toward(mem, ["sym_b0", "sym_b1"], 0.22)
        if len(mem.get_reunion_events()) > 0:
            break

    evt = mem.get_reunion_events()[0]
    successor_id = evt["successor_family_id"]
    successor = mem.get_family_record(successor_id)

    symbols = ["sym_a0", "sym_a1", "sym_b0", "sym_b1"]
    for sid in symbols:
        assert mem.get_family_for_symbol(sid) == successor_id

    # One-family-only: no duplicate symbol assignment can exist inside successor membership.
    assert sorted(successor.member_symbol_ids) == sorted(symbols)
    assert len(set(successor.member_symbol_ids)) == len(successor.member_symbol_ids)


def test_reunion_does_not_occur_if_combined_structure_remains_incoherent():
    mem = NeutralFamilyMemoryV1()
    mem.REUNION_CENTER_DISTANCE_THRESHOLD = 1.0
    mem.REUNION_SPREAD_DELTA_THRESHOLD = 1.0
    mem.REUNION_PERSISTENCE_THRESHOLD = 2
    mem.REUNION_COMBINED_MAX_INTERNAL_DISTANCE = 0.15

    _setup_two_active_families(mem, spread_value=0.50)

    # Keep families far apart while permissive proximity gates are enabled.
    # Combined coherence gate must still block reunion.
    for _ in range(12):
        _drive_family_toward(mem, ["sym_a0", "sym_a1"], 0.10, spread_value=0.50)
        _drive_family_toward(mem, ["sym_b0", "sym_b1"], 0.80, spread_value=0.50)

    assert len(mem.get_reunion_events()) == 0
    assert mem.get_family_record("fam_01").lifecycle_status == "FAMILY_ACTIVE"
    assert mem.get_family_record("fam_02").lifecycle_status == "FAMILY_ACTIVE"
