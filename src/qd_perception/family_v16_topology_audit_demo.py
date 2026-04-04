"""
Demo for Topology Residual / Shape-Class Audit v1 in qd_perception_spine.

Shows:
- compact family topology
- elongated family topology
- dual-lobe family topology
- transition-level topology summary
"""

import json
import os

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(a: float, b: float, c: float, d: float) -> dict[str, float]:
    return {"axis_a": a, "axis_b": b, "axis_c": c, "axis_d": d}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _divider(title: str) -> None:
    print("\n" + ("=" * 72))
    print(title)
    print(("=" * 72))


def _seed_family(mem: NeutralFamilyMemoryV1, prefix: str, member_count: int) -> tuple[str, list[str]]:
    spread = _spr(0.05)
    base = _sig(0.50, 0.50, 0.50, 0.50)
    member_ids: list[str] = []
    for i in range(member_count):
        sid = f"{prefix}_{i}"
        member_ids.append(sid)
        mem.join_or_create_family(sid, base, spread, 10)
        if i > 0:
            mem.join_or_create_family(sid, base, spread, 10)
    return "fam_01", member_ids


def _apply_compact_geometry(mem: NeutralFamilyMemoryV1, member_ids: list[str]) -> None:
    points = [
        (0.49, 0.50, 0.51, 0.50),
        (0.51, 0.50, 0.49, 0.50),
        (0.50, 0.49, 0.50, 0.51),
        (0.50, 0.51, 0.50, 0.49),
        (0.495, 0.505, 0.495, 0.505),
        (0.505, 0.495, 0.505, 0.495),
    ]
    for idx, sid in enumerate(member_ids):
        a, b, c, d = points[idx % len(points)]
        mem._symbol_signatures[sid] = _sig(a, b, c, d)
        mem._symbol_spreads[sid] = _spr(0.05)


def _apply_elongated_geometry(mem: NeutralFamilyMemoryV1, member_ids: list[str]) -> None:
    for idx, sid in enumerate(member_ids):
        t = idx / float(max(len(member_ids) - 1, 1))
        a = 0.10 + (0.80 * t)
        mem._symbol_signatures[sid] = _sig(a, 0.50, 0.50, 0.50)
        mem._symbol_spreads[sid] = _spr(0.05)


def _apply_dual_lobe_geometry(mem: NeutralFamilyMemoryV1, member_ids: list[str]) -> None:
    midpoint = len(member_ids) // 2
    for idx, sid in enumerate(member_ids):
        if idx < midpoint:
            mem._symbol_signatures[sid] = _sig(0.12, 0.12, 0.12, 0.12)
        else:
            mem._symbol_signatures[sid] = _sig(0.88, 0.88, 0.88, 0.88)
        mem._symbol_spreads[sid] = _spr(0.05)


def _emit_fission_and_reunion_chain(mem: NeutralFamilyMemoryV1) -> None:
    spread = _spr(0.05)
    for i in range(8):
        sid = f"sym_f_{i}"
        for _ in range(2):
            mem.join_or_create_family(sid, _sig(0.5 + (i * 0.01), 0.5 + (i * 0.01), 0.5 + (i * 0.01), 0.5 + (i * 0.01)), spread, 10)

    for _ in range(30):
        for i in range(3):
            mem.join_or_create_family(f"sym_f_{i}", _sig(0.1, 0.1, 0.1, 0.1), spread, 10)
        for i in range(5, 8):
            mem.join_or_create_family(f"sym_f_{i}", _sig(0.9, 0.9, 0.9, 0.9), spread, 10)
        if mem.get_fission_events():
            break

    fission_evt = mem.get_fission_events()[0]
    g1 = list(fission_evt["partition"]["group_1_member_ids"])
    g2 = list(fission_evt["partition"]["group_2_member_ids"])
    for _ in range(40):
        for sid in g1:
            mem.join_or_create_family(sid, _sig(0.20, 0.20, 0.20, 0.20), spread, 10)
        for sid in g2:
            mem.join_or_create_family(sid, _sig(0.22, 0.22, 0.22, 0.22), spread, 10)
        if mem.get_reunion_events():
            break


def run_family_topology_audit_demo_v1() -> None:
    _divider("Compact Family Topology")
    mem_compact = NeutralFamilyMemoryV1()
    fam_id, member_ids = _seed_family(mem_compact, "sym_c", 6)
    _apply_compact_geometry(mem_compact, member_ids)
    print(json.dumps(mem_compact.get_family_topology_audit(fam_id), indent=2, sort_keys=True))

    _divider("Elongated Family Topology")
    mem_elongated = NeutralFamilyMemoryV1()
    fam_id, member_ids = _seed_family(mem_elongated, "sym_e", 6)
    _apply_elongated_geometry(mem_elongated, member_ids)
    print(json.dumps(mem_elongated.get_family_topology_audit(fam_id), indent=2, sort_keys=True))

    _divider("Dual-Lobe Family Topology")
    mem_dual = NeutralFamilyMemoryV1()
    fam_id, member_ids = _seed_family(mem_dual, "sym_d", 8)
    _apply_dual_lobe_geometry(mem_dual, member_ids)
    print(json.dumps(mem_dual.get_family_topology_audit(fam_id), indent=2, sort_keys=True))

    _divider("Transition Topology Summary")
    ledger_path = "runs/family_transition_topology_audit_demo_v1.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)
    mem_chain = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    _emit_fission_and_reunion_chain(mem_chain)
    fission_evt_id = mem_chain.get_fission_events()[0]["event_id"]
    reunion_evt_id = mem_chain.get_reunion_events()[0]["event_id"]
    print(json.dumps(mem_chain.get_transition_topology_audit(fission_evt_id), indent=2, sort_keys=True))
    print(json.dumps(mem_chain.get_transition_topology_audit(reunion_evt_id), indent=2, sort_keys=True))


if __name__ == "__main__":
    run_family_topology_audit_demo_v1()
