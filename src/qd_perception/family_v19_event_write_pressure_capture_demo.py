"""
Demo for Event-Write-Time Pressure Capture v1.2.

Shows:
- full capture
- partial capture
- capture failure (event still written with honest capture metadata)
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


def run_event_write_pressure_capture_demo_v1_2() -> None:
    _divider("Full Capture on Fission Event")
    path_full = "runs/family_v19_pressure_capture_full_demo.jsonl"
    if os.path.exists(path_full):
        os.remove(path_full)
    mem_full = NeutralFamilyMemoryV1(durable_ledger_path=path_full)
    fam_id, members = _seed_family(mem_full, "sym_full", 8)
    mem_full._execute_family_fission(fam_id, members[:4], members[4:], "demo full capture")
    evt_full = mem_full.get_fission_events()[0]
    print(json.dumps(evt_full["pressure_snapshot"], indent=2, sort_keys=True))
    print(json.dumps(mem_full.get_transition_pressure_snapshot(evt_full["event_id"]), indent=2, sort_keys=True))

    _divider("Partial Capture on Fission Event (3/3 successors)")
    path_partial = "runs/family_v19_pressure_capture_partial_demo.jsonl"
    if os.path.exists(path_partial):
        os.remove(path_partial)
    mem_partial = NeutralFamilyMemoryV1(durable_ledger_path=path_partial)
    fam_id, members = _seed_family(mem_partial, "sym_partial", 6)
    mem_partial._execute_family_fission(fam_id, members[:3], members[3:], "demo partial capture")
    evt_partial = mem_partial.get_fission_events()[0]
    print(json.dumps(evt_partial["pressure_snapshot"], indent=2, sort_keys=True))
    print(json.dumps(mem_partial.get_transition_pressure_snapshot(evt_partial["event_id"]), indent=2, sort_keys=True))

    _divider("Capture Failure Recorded Honestly")
    path_fail = "runs/family_v19_pressure_capture_failure_demo.jsonl"
    if os.path.exists(path_fail):
        os.remove(path_fail)
    mem_fail = NeutralFamilyMemoryV1(durable_ledger_path=path_fail)
    fam_id, members = _seed_family(mem_fail, "sym_fail", 8)
    original = mem_fail.get_family_pressure_forecast
    mem_fail.get_family_pressure_forecast = lambda _family_id: (_ for _ in ()).throw(RuntimeError("demo_capture_failure"))
    try:
        mem_fail._execute_family_fission(fam_id, members[:4], members[4:], "demo capture failure")
    finally:
        mem_fail.get_family_pressure_forecast = original
    evt_fail = mem_fail.get_fission_events()[0]
    print(json.dumps(evt_fail["pressure_snapshot"], indent=2, sort_keys=True))
    print(json.dumps(mem_fail.get_transition_pressure_snapshot(evt_fail["event_id"]), indent=2, sort_keys=True))


if __name__ == "__main__":
    run_event_write_pressure_capture_demo_v1_2()
