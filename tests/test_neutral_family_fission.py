import pytest

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def test_fracture_alone_without_dual_center_does_not_fission():
    mem = NeutralFamilyMemoryV1()

    # Make the family persistently over-broad (fracture -> SPLIT_READY), but keep signatures identical
    # so subgroup detection stays off.
    broad = _spr(0.8)

    mem.join_or_create_family("sym_00", _sig(0.1), broad, 10)
    # Add enough members to exceed MIN_MEMBERS_FOR_FISSION while remaining a single cloud.
    for i in range(1, 7):
        sid = f"sym_{i:02d}"
        mem.join_or_create_family(sid, _sig(0.1), broad, 10)
        mem.join_or_create_family(sid, _sig(0.1), broad, 10)

    rec = mem.get_family_record("fam_01")
    assert rec is not None
    assert rec.fracture_status == "FAMILY_SPLIT_READY"
    assert rec.subgroup_count == 1
    assert len(mem.get_fission_events()) == 0
    assert len(mem._families) == 1


def test_subgroup_like_structure_without_split_ready_does_not_fission():
    mem = NeutralFamilyMemoryV1()
    mem.FRACTURE_PERSISTENCE_THRESHOLD = 999

    spread = _spr(0.05)

    # Establish enough members in a single family, then move two members apart.
    for i in range(8):
        sid = f"sym_init_{i}"
        for _ in range(2):
            mem.join_or_create_family(sid, _sig(0.5 + (i * 0.01)), spread, 10)

    # Drive dual-center subgroup evidence while refusing SPLIT_READY via threshold.
    for _ in range(10):
        for i in range(3):
            mem.join_or_create_family(f"sym_init_{i}", _sig(0.1), spread, 10)
        for i in range(5, 8):
            mem.join_or_create_family(f"sym_init_{i}", _sig(0.9), spread, 10)

    rec = mem.get_family_record("fam_01")
    assert rec is not None
    assert rec.subgroup_count == 2
    assert rec.fracture_status != "FAMILY_SPLIT_READY"
    assert rec.lifecycle_status == "FAMILY_ACTIVE"
    assert len(mem.get_fission_events()) == 0
    assert len(mem._families) == 1


def test_persistent_split_ready_plus_persistent_dual_center_does_fission():
    mem = NeutralFamilyMemoryV1()

    spread = _spr(0.05)

    # Establish enough members in a single family, then move two members apart.
    for i in range(8):
        sid = f"sym_init_{i}"
        for _ in range(2):
            mem.join_or_create_family(sid, _sig(0.5 + (i * 0.01)), spread, 10)

    # Repeatedly hit representatives to accumulate subgroup evidence, SPLIT_READY, and stable partition persistence.
    for _ in range(30):
        for i in range(3):
            mem.join_or_create_family(f"sym_init_{i}", _sig(0.1), spread, 10)
        for i in range(5, 8):
            mem.join_or_create_family(f"sym_init_{i}", _sig(0.9), spread, 10)
        if len(mem.get_fission_events()) > 0:
            break

    events = mem.get_fission_events()
    assert len(events) == 1
    evt = events[0]
    parent_id = evt["parent_family_id"]
    succ_ids = evt["successor_family_ids"]
    assert parent_id == "fam_01"
    assert len(succ_ids) == 2

    parent = mem.get_family_record(parent_id)
    assert parent is not None
    assert parent.lifecycle_status == "FAMILY_INACTIVE_SUCCESSOR_SPLIT"
    assert parent.member_symbol_ids == []
    assert len(parent.historical_member_symbol_ids) >= mem.MIN_MEMBERS_FOR_FISSION
    assert parent.lineage_successor_family_ids == succ_ids
    assert evt["event_id"] in parent.fission_event_ids

    # Successors preserve symbol IDs; only family membership changes.
    for sid in parent.historical_member_symbol_ids:
        assert mem.get_family_for_symbol(sid) in succ_ids
        assert mem.get_family_for_symbol(sid) != parent_id

    succ_1 = mem.get_family_record(succ_ids[0])
    succ_2 = mem.get_family_record(succ_ids[1])
    assert succ_1 is not None and succ_2 is not None
    assert succ_1.lifecycle_status == "FAMILY_ACTIVE"
    assert succ_2.lifecycle_status == "FAMILY_ACTIVE"
    assert succ_1.lineage_parent_family_id == parent_id
    assert succ_2.lineage_parent_family_id == parent_id
    assert succ_1.lineage_fission_event_id == evt["event_id"]
    assert succ_2.lineage_fission_event_id == evt["event_id"]
    assert evt["event_id"] in succ_1.fission_event_ids
    assert evt["event_id"] in succ_2.fission_event_ids

    # One-family-only membership rule: no symbol appears in both successor member lists.
    overlap = set(succ_1.member_symbol_ids) & set(succ_2.member_symbol_ids)
    assert overlap == set()
