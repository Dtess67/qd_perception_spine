"""
Demo for Durable Family Event Ledger v1 in qd_perception_spine.

Shows:
- fission event durable write
- reunion event durable write
- full ledger readback
- family-specific ledger query
"""

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


def _run_one_fission(ledger_path: str) -> None:
    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
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


def _run_one_reunion(ledger_path: str) -> None:
    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
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


def run_family_event_ledger_demo_v1() -> None:
    ledger_path = "runs/family_transition_event_ledger_demo_v1.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)

    _divider("Trigger Fission Event -> Durable Ledger")
    _run_one_fission(ledger_path)
    mem_f = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    print(f"Ledger path: {mem_f.get_durable_ledger_path()}")
    print(f"Events after fission phase: {len(mem_f.get_event_ledger())}")

    _divider("Trigger Reunion Event -> Durable Ledger")
    _run_one_reunion(ledger_path)
    mem_r = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    all_events = mem_r.get_event_ledger()
    print(f"Events after reunion phase: {len(all_events)}")
    for evt in all_events:
        print(
            f"event_id={evt.get('event_id')} "
            f"type={evt.get('event_type')} "
            f"sources={evt.get('source_family_ids')} "
            f"successors={evt.get('successor_family_ids')}"
        )

    _divider("Query Durable Ledger For One Family ID")
    query_family_id = "fam_01"
    queried = mem_r.get_events_for_family(query_family_id)
    print(f"query_family_id={query_family_id} matched_events={len(queried)}")
    for evt in queried:
        print(
            f"matched event_id={evt.get('event_id')} "
            f"type={evt.get('event_type')} "
            f"order={evt.get('event_order')}"
        )


if __name__ == "__main__":
    run_family_event_ledger_demo_v1()
