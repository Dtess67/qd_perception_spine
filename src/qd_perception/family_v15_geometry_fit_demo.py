"""
Demo for Geometric Residual / Lineage Fit Audit v1 in qd_perception_spine.

Shows:
- family geometry fit (good)
- family geometry fit (poor after intentional distortion)
- fission/reunion transition geometry fit summaries
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


def _seed_small_family(mem: NeutralFamilyMemoryV1) -> str:
    spread = _spr(0.05)
    mem.join_or_create_family("sym_0", _sig(0.50), spread, 10)  # mint fam_01
    mem.join_or_create_family("sym_1", _sig(0.52), spread, 10)  # hold
    mem.join_or_create_family("sym_1", _sig(0.52), spread, 10)  # join
    mem.join_or_create_family("sym_2", _sig(0.48), spread, 10)  # hold
    mem.join_or_create_family("sym_2", _sig(0.48), spread, 10)  # join
    return "fam_01"


def _emit_fission_and_reunion_chain(mem: NeutralFamilyMemoryV1) -> None:
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
    g1 = list(fission_evt["partition"]["group_1_member_ids"])
    g2 = list(fission_evt["partition"]["group_2_member_ids"])
    for _ in range(40):
        for sid in g1:
            mem.join_or_create_family(sid, _sig(0.20), spread, 10)
        for sid in g2:
            mem.join_or_create_family(sid, _sig(0.22), spread, 10)
        if mem.get_reunion_events():
            break

    if not mem.get_reunion_events():
        raise RuntimeError("Demo chain failed to earn reunion.")


def run_family_geometry_fit_demo_v1() -> None:
    _divider("Family Geometry Fit: Good")
    mem_good = NeutralFamilyMemoryV1()
    fam_id = _seed_small_family(mem_good)
    print(json.dumps(mem_good.get_family_geometry_fit(fam_id), indent=2, sort_keys=True))

    _divider("Family Geometry Fit: Poor (Intentional Distortion)")
    rec = mem_good.get_family_record(fam_id)
    rec.current_signature = _sig(0.95)
    print(json.dumps(mem_good.get_family_geometry_fit(fam_id), indent=2, sort_keys=True))

    _divider("Transition Geometry Fit: Fission + Reunion")
    ledger_path = "runs/family_transition_geometry_fit_demo_v1.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)

    mem_chain = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    _emit_fission_and_reunion_chain(mem_chain)
    fission_evt_id = mem_chain.get_fission_events()[0]["event_id"]
    reunion_evt_id = mem_chain.get_reunion_events()[0]["event_id"]

    print(json.dumps(mem_chain.get_transition_geometry_fit(fission_evt_id), indent=2, sort_keys=True))
    print(json.dumps(mem_chain.get_transition_geometry_fit(reunion_evt_id), indent=2, sort_keys=True))


if __name__ == "__main__":
    run_family_geometry_fit_demo_v1()
