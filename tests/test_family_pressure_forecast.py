import copy
from pathlib import Path

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(a: float, b: float, c: float, d: float) -> dict[str, float]:
    return {"axis_a": a, "axis_b": b, "axis_c": c, "axis_d": d}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


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


def test_pressure_forecast_stable_case(tmp_path: Path):
    ledger = tmp_path / "family_pressure_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, member_ids = _seed_family(mem, "sym_ps", 6)
    _apply_compact_geometry(mem, member_ids)

    forecast = mem.get_family_pressure_forecast(fam_id)
    assert forecast["found"] is True
    assert forecast["forecast_available"] is True
    assert forecast["pressure_state"] == "PRESSURE_STABLE"
    assert forecast["scorecard"]["diagnostic_scale"] == "0_to_1_comparative_not_probability"


def test_pressure_forecast_stretched_case(tmp_path: Path):
    ledger = tmp_path / "family_pressure_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, member_ids = _seed_family(mem, "sym_pt", 6)
    _apply_elongated_geometry(mem, member_ids)

    forecast = mem.get_family_pressure_forecast(fam_id)
    assert forecast["pressure_state"] == "PRESSURE_STRETCHED"
    assert forecast["scorecard"]["stretch_pressure_index"] >= mem.PRESSURE_STRETCHED_THRESHOLD


def test_pressure_forecast_dual_center_risk_case(tmp_path: Path):
    ledger = tmp_path / "family_pressure_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, member_ids = _seed_family(mem, "sym_pd", 8)
    _apply_dual_lobe_geometry(mem, member_ids)

    forecast = mem.get_family_pressure_forecast(fam_id)
    assert forecast["pressure_state"] == "PRESSURE_DUAL_CENTER_RISK"
    assert forecast["scorecard"]["dual_center_pressure_index"] >= mem.PRESSURE_DUAL_CENTER_THRESHOLD


def test_pressure_forecast_fission_prone_case(tmp_path: Path):
    ledger = tmp_path / "family_pressure_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, member_ids = _seed_family(mem, "sym_pf", 8)
    _apply_dual_lobe_geometry(mem, member_ids)

    rec = mem.get_family_record(fam_id)
    rec.subgroup_count = 2
    rec.subgroup_evidence_counter = mem.SUBGROUP_PERSISTENCE_THRESHOLD
    rec.fracture_status = "FAMILY_SPLIT_READY"
    rec.fracture_counter = mem.FRACTURE_PERSISTENCE_THRESHOLD
    rec.fission_candidate_counter = mem.FISSION_PERSISTENCE_THRESHOLD
    for sid in member_ids:
        mem._earned_boundary_statuses[sid] = "FAMILY_BRIDGE"

    forecast = mem.get_family_pressure_forecast(fam_id)
    assert forecast["pressure_state"] == "PRESSURE_FISSION_PRONE"
    assert forecast["scorecard"]["fission_pressure_index"] >= mem.PRESSURE_FISSION_PRONE_THRESHOLD
    assert "FRACTURE_SPLIT_READY_PRESENT" in forecast["warnings"]


def test_pressure_forecast_unclear_for_insufficient_evidence(tmp_path: Path):
    ledger = tmp_path / "family_pressure_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, member_ids = _seed_family(mem, "sym_pu", 3)
    _apply_compact_geometry(mem, member_ids)

    forecast = mem.get_family_pressure_forecast(fam_id)
    assert forecast["pressure_state"] == "PRESSURE_UNCLEAR"
    assert forecast["forecast_available"] is False
    assert "INSUFFICIENT_MEMBER_GEOMETRY_FOR_PRESSURE_FORECAST" in forecast["warnings"]


def test_pressure_forecast_is_diagnostic_only_and_does_not_mutate_lineage(tmp_path: Path):
    ledger = tmp_path / "family_pressure_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, member_ids = _seed_family(mem, "sym_pg", 6)
    _apply_compact_geometry(mem, member_ids)

    families_before = copy.deepcopy(mem._families)
    symbol_to_family_before = dict(mem._symbol_to_family)
    fission_before = mem.get_fission_events()
    reunion_before = mem.get_reunion_events()
    ledger_before = mem.get_event_ledger()

    forecast = mem.get_family_pressure_forecast(fam_id)

    assert forecast["forecast_mode"] == "DIAGNOSTIC_ONLY"
    assert forecast["event_creation_performed"] is False
    assert forecast["lineage_mutation_performed"] is False
    assert mem._families == families_before
    assert mem._symbol_to_family == symbol_to_family_before
    assert mem.get_fission_events() == fission_before
    assert mem.get_reunion_events() == reunion_before
    assert mem.get_event_ledger() == ledger_before
