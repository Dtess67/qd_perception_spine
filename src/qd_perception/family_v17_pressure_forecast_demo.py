"""
Demo for Family Stability / Split-Pressure Forecast v1.

Shows:
- PRESSURE_STABLE
- PRESSURE_STRETCHED
- PRESSURE_DUAL_CENTER_RISK
- PRESSURE_FISSION_PRONE
- PRESSURE_UNCLEAR
"""

import json

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
    rec = mem.get_family_record("fam_01")
    rec.current_signature = mem._compute_group_centroid(member_ids)
    rec.current_spread = mem._compute_group_spread_avg(member_ids)


def _apply_elongated_geometry(mem: NeutralFamilyMemoryV1, member_ids: list[str]) -> None:
    for idx, sid in enumerate(member_ids):
        t = idx / float(max(len(member_ids) - 1, 1))
        a = 0.10 + (0.80 * t)
        mem._symbol_signatures[sid] = _sig(a, 0.50, 0.50, 0.50)
        mem._symbol_spreads[sid] = _spr(0.05)
    rec = mem.get_family_record("fam_01")
    rec.current_signature = mem._compute_group_centroid(member_ids)
    rec.current_spread = mem._compute_group_spread_avg(member_ids)


def _apply_dual_lobe_geometry(mem: NeutralFamilyMemoryV1, member_ids: list[str]) -> None:
    midpoint = len(member_ids) // 2
    for idx, sid in enumerate(member_ids):
        if idx < midpoint:
            mem._symbol_signatures[sid] = _sig(0.12, 0.12, 0.12, 0.12)
        else:
            mem._symbol_signatures[sid] = _sig(0.88, 0.88, 0.88, 0.88)
        mem._symbol_spreads[sid] = _spr(0.05)
    rec = mem.get_family_record("fam_01")
    rec.current_signature = mem._compute_group_centroid(member_ids)
    rec.current_spread = mem._compute_group_spread_avg(member_ids)


def _print_case(case_title: str, mem: NeutralFamilyMemoryV1, family_id: str) -> None:
    _divider(case_title)
    print(json.dumps(mem.get_family_pressure_forecast(family_id), indent=2, sort_keys=True))


def run_family_pressure_forecast_demo_v1() -> None:
    mem_stable = NeutralFamilyMemoryV1()
    fam_id, member_ids = _seed_family(mem_stable, "sym_ps", 6)
    _apply_compact_geometry(mem_stable, member_ids)
    _print_case("PRESSURE_STABLE Case", mem_stable, fam_id)

    mem_stretched = NeutralFamilyMemoryV1()
    fam_id, member_ids = _seed_family(mem_stretched, "sym_pt", 6)
    _apply_elongated_geometry(mem_stretched, member_ids)
    _print_case("PRESSURE_STRETCHED Case", mem_stretched, fam_id)

    mem_dual = NeutralFamilyMemoryV1()
    fam_id, member_ids = _seed_family(mem_dual, "sym_pd", 8)
    _apply_dual_lobe_geometry(mem_dual, member_ids)
    _print_case("PRESSURE_DUAL_CENTER_RISK Case", mem_dual, fam_id)

    mem_fission = NeutralFamilyMemoryV1()
    fam_id, member_ids = _seed_family(mem_fission, "sym_pf", 8)
    _apply_dual_lobe_geometry(mem_fission, member_ids)
    rec = mem_fission.get_family_record(fam_id)
    rec.subgroup_count = 2
    rec.subgroup_evidence_counter = mem_fission.SUBGROUP_PERSISTENCE_THRESHOLD
    rec.fracture_status = "FAMILY_SPLIT_READY"
    rec.fracture_counter = mem_fission.FRACTURE_PERSISTENCE_THRESHOLD
    rec.fission_candidate_counter = mem_fission.FISSION_PERSISTENCE_THRESHOLD
    for sid in member_ids:
        mem_fission._earned_boundary_statuses[sid] = "FAMILY_BRIDGE"
    _print_case("PRESSURE_FISSION_PRONE Case", mem_fission, fam_id)

    mem_unclear = NeutralFamilyMemoryV1()
    fam_id, member_ids = _seed_family(mem_unclear, "sym_pu", 3)
    _apply_compact_geometry(mem_unclear, member_ids)
    _print_case("PRESSURE_UNCLEAR Case", mem_unclear, fam_id)


if __name__ == "__main__":
    run_family_pressure_forecast_demo_v1()
