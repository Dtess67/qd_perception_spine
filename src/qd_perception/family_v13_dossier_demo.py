"""
Demo for Ancestry Report / Family Dossier v1 in qd_perception_spine.

Shows dossier output for:
- active family (reunion successor)
- inactive historical family (fission parent)
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


def run_family_dossier_demo_v1() -> None:
    ledger_path = "runs/family_transition_dossier_demo_v1.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)

    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    _emit_fission_and_reunion_chain(mem)

    _divider("Active Family Dossier (Reunion Successor)")
    print(json.dumps(mem.get_family_dossier("fam_04", max_depth=8), indent=2, sort_keys=True))

    _divider("Historical Family Dossier (Fission Parent)")
    print(json.dumps(mem.get_family_dossier("fam_01", max_depth=8), indent=2, sort_keys=True))

    _divider("Unknown Family Dossier")
    print(json.dumps(mem.get_family_dossier("fam_unknown", max_depth=8), indent=2, sort_keys=True))


if __name__ == "__main__":
    run_family_dossier_demo_v1()
