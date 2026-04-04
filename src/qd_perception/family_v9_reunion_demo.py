"""
Demo for Family Reunion / Re-merge v1 in qd_perception_spine.

This demo is structural-only:
- Reunion is conservative and persistence-based
- Reunion creates a NEW successor family ID
- Source families are preserved as inactive historical records
- Lineage and event audit remain explicit
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


def _seed_two_families(mem: NeutralFamilyMemoryV1, spread_value: float = 0.05) -> None:
    spread = _spr(spread_value)

    mem.join_or_create_family("sym_a0", _sig(0.10), spread, 10)
    mem.join_or_create_family("sym_a1", _sig(0.11), spread, 10)
    mem.join_or_create_family("sym_a1", _sig(0.11), spread, 10)

    mem.join_or_create_family("sym_b0", _sig(0.80), spread, 10)
    mem.join_or_create_family("sym_b1", _sig(0.81), spread, 10)
    mem.join_or_create_family("sym_b1", _sig(0.81), spread, 10)


def _nudge(mem: NeutralFamilyMemoryV1, symbols: list[str], value: float, spread_value: float = 0.05) -> None:
    for sid in symbols:
        mem.join_or_create_family(sid, _sig(value), _spr(spread_value), 10)


def run_family_reunion_demo_v1() -> None:
    _divider("Scenario 1: One Favorable Closeness Observation -> No Reunion")
    mem = NeutralFamilyMemoryV1()
    mem.REUNION_PERSISTENCE_THRESHOLD = 6
    _seed_two_families(mem)

    _nudge(mem, ["sym_a0", "sym_a1"], 0.20)
    _nudge(mem, ["sym_b0", "sym_b1"], 0.22)

    print(f"Reunion events: {len(mem.get_reunion_events())}")
    print(f"fam_01 lifecycle_status: {mem.get_family_record('fam_01').lifecycle_status}")
    print(f"fam_02 lifecycle_status: {mem.get_family_record('fam_02').lifecycle_status}")

    _divider("Scenario 2: Persistent Closeness + Coherence -> Reunion")
    mem2 = NeutralFamilyMemoryV1()
    _seed_two_families(mem2)

    for _ in range(12):
        _nudge(mem2, ["sym_a0", "sym_a1"], 0.20)
        _nudge(mem2, ["sym_b0", "sym_b1"], 0.22)
        if len(mem2.get_reunion_events()) > 0:
            break

    events = mem2.get_reunion_events()
    print(f"Reunion events: {len(events)}")
    if not events:
        print("  No reunion executed (gate not met).")
        return

    evt = events[0]
    src_a, src_b = evt["source_family_ids"]
    successor_id = evt["successor_family_id"]

    rec_a = mem2.get_family_record(src_a)
    rec_b = mem2.get_family_record(src_b)
    rec_s = mem2.get_family_record(successor_id)

    print(f"Event: {evt['event_id']} (order={evt['event_order']})")
    print(f"  source_family_ids: {evt['source_family_ids']}")
    print(f"  successor_family_id: {successor_id}")
    print(f"  gate_summary: {evt['gate_summary']}")
    print(f"{src_a} lifecycle_status: {rec_a.lifecycle_status}")
    print(f"{src_b} lifecycle_status: {rec_b.lifecycle_status}")
    print(f"{src_a} historical_member_symbol_ids: {rec_a.historical_member_symbol_ids}")
    print(f"{src_b} historical_member_symbol_ids: {rec_b.historical_member_symbol_ids}")
    print(f"{successor_id} lineage_parent_family_ids: {rec_s.lineage_parent_family_ids}")
    print(f"{successor_id} lineage_reunion_event_id: {rec_s.lineage_reunion_event_id}")
    print(f"{successor_id} members: {rec_s.member_symbol_ids}")
    print(f"{successor_id} mint_signature: {rec_s.mint_signature}")
    print(f"{successor_id} mint_spread: {rec_s.mint_spread}")


if __name__ == "__main__":
    run_family_reunion_demo_v1()
