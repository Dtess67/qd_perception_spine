"""
Demo for Genealogy / Ancestry Query Layer v1 in qd_perception_spine.

This demo reads durable ledger-backed transitions and shows:
- origin event query
- parent/source family query
- successor query
- shared ancestry query
- bounded lineage chain query
"""

import json
import os

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _divider(title: str) -> None:
    print("\n" + ("=" * 72))
    print(title)
    print(("=" * 72))


def _emit_fission_and_reunion_chain(mem: NeutralFamilyMemoryV1) -> tuple[str, str, str]:
    """
    Produces a coherent lineage chain in one memory instance:
    fam_01 -> (fission) -> fam_02, fam_03 -> (reunion) -> fam_04
    """
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
            break

    fission_evt = mem.get_fission_events()[0]
    fam_a, fam_b = fission_evt["successor_family_ids"]
    members_a = list(fission_evt["partition"]["group_1_member_ids"])
    members_b = list(fission_evt["partition"]["group_2_member_ids"])

    # Move both successor families into persistent compatible proximity for reunion.
    for _ in range(40):
        for sid in members_a:
            mem.join_or_create_family(sid, _sig(0.20), spread, 10)
        for sid in members_b:
            mem.join_or_create_family(sid, _sig(0.22), spread, 10)
        if mem.get_reunion_events():
            break

    if not mem.get_reunion_events():
        raise RuntimeError("Demo reunion chain not earned within bounded iterations.")

    reunion_evt = mem.get_reunion_events()[0]
    reunited = reunion_evt["successor_family_id"]
    return fam_a, fam_b, reunited


def run_family_ancestry_demo_v1() -> None:
    ledger_path = "runs/family_transition_event_ledger_ancestry_demo_v1.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)

    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    fam_a, fam_b, reunited = _emit_fission_and_reunion_chain(mem)

    _divider("Durable Ledger Readback")
    all_events = mem.get_event_ledger()
    print(f"ledger_path: {mem.get_durable_ledger_path()}")
    print(f"ledger_event_count: {len(all_events)}")
    print(json.dumps(all_events, indent=2, sort_keys=True))

    _divider("Origin Event Lookup")
    print(json.dumps(mem.get_family_origin(reunited), indent=2, sort_keys=True))

    _divider("Parent/Source Families Lookup")
    print(json.dumps(mem.get_family_parents(reunited), indent=2, sort_keys=True))

    _divider("Successor Lookup From Parent Family")
    print(json.dumps(mem.get_family_successors("fam_01", recursive=True, max_depth=4), indent=2, sort_keys=True))

    _divider("Shared Ancestry Query")
    print(json.dumps(mem.families_share_ancestry(fam_a, fam_b, max_depth=6), indent=2, sort_keys=True))

    _divider("Lineage Chain Query")
    print(json.dumps(mem.get_family_lineage(reunited, max_depth=6), indent=2, sort_keys=True))


if __name__ == "__main__":
    run_family_ancestry_demo_v1()
