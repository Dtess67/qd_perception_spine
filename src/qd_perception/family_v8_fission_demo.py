"""
Demo for Actual Family Fission / Successor Family Creation v1 in qd_perception_spine.

This demo is structural-only:
- Symbols remain primary identity units (IDs unchanged)
- Families are conservative structural groupings
- Actual fission is executed only under strong, persistent evidence
- Parent lineage/history is preserved explicitly (inactive parent + event log)
"""

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _divider(title: str) -> None:
    print("\n" + ("=" * 72))
    print(title)
    print(("=" * 72))


def run_family_fission_demo_v1() -> None:
    mem = NeutralFamilyMemoryV1()

    _divider("Scenario 1: Fracture / SPLIT_READY Alone (No Dual-Center) -> No Fission")
    broad = _spr(0.8)

    mem.join_or_create_family("sym_seed", _sig(0.1), broad, 10)
    for i in range(1, 9):
        sid = f"sym_single_{i:02d}"
        mem.join_or_create_family(sid, _sig(0.1), broad, 10)
        mem.join_or_create_family(sid, _sig(0.1), broad, 10)

    parent = mem.get_family_record("fam_01")
    print(f"Family: fam_01")
    print(f"  lifecycle_status: {parent.lifecycle_status}")
    print(f"  fracture_status: {parent.fracture_status} (counter={parent.fracture_counter})")
    print(f"  subgroup_count: {parent.subgroup_count} (evidence={parent.subgroup_evidence_counter})")
    print(f"  fission_events: {len(mem.get_fission_events())}")

    _divider("Scenario 2: SPLIT_READY + Persistent Dual-Center + Stable Partition -> Fission")
    mem2 = NeutralFamilyMemoryV1()

    spread = _spr(0.05)

    # Establish a single family with enough members under the default join thresholds,
    # then move two members apart to form two persistent internal centers.
    for i in range(8):
        sid = f"sym_init_{i}"
        for _ in range(2):
            mem2.join_or_create_family(sid, _sig(0.5 + (i * 0.01)), spread, 10)

    # Drive repeated observations to persist subgroup evidence + SPLIT_READY + stable partition
    for _ in range(30):
        for i in range(3):
            mem2.join_or_create_family(f"sym_init_{i}", _sig(0.1), spread, 10)
        for i in range(5, 8):
            mem2.join_or_create_family(f"sym_init_{i}", _sig(0.9), spread, 10)
        if len(mem2.get_fission_events()) > 0:
            break

    events = mem2.get_fission_events()
    print(f"Fission events: {len(events)}")
    if not events:
        print("  No fission executed (gate not met).")
        return

    evt = events[0]
    parent_id = evt["parent_family_id"]
    succ_ids = evt["successor_family_ids"]

    parent2 = mem2.get_family_record(parent_id)
    print(f"Parent: {parent_id}")
    print(f"  lifecycle_status: {parent2.lifecycle_status}")
    print(f"  successors: {parent2.lineage_successor_family_ids}")
    print(f"  historical_members: {len(parent2.historical_member_symbol_ids)}")
    print(f"  event_ids: {parent2.fission_event_ids}")
    print(f"Event: {evt['event_id']} (order={evt['event_order']})")
    print(f"  gate_summary: {evt['gate_summary']}")

    for succ_id in succ_ids:
        rec = mem2.get_family_record(succ_id)
        print(f"Successor: {succ_id}")
        print(f"  lineage_parent_family_id: {rec.lineage_parent_family_id}")
        print(f"  lineage_fission_event_id: {rec.lineage_fission_event_id}")
        print(f"  members: {rec.member_symbol_ids}")
        print(f"  mint_signature: {rec.mint_signature}")
        print(f"  mint_spread: {rec.mint_spread}")


if __name__ == "__main__":
    run_family_fission_demo_v1()
