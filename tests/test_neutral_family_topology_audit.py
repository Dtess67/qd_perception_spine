from pathlib import Path

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(a: float, b: float, c: float, d: float) -> dict[str, float]:
    return {"axis_a": a, "axis_b": b, "axis_c": c, "axis_d": d}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _seed_family(mem: NeutralFamilyMemoryV1, member_count: int) -> tuple[str, list[str]]:
    spread = _spr(0.05)
    base = _sig(0.50, 0.50, 0.50, 0.50)
    member_ids: list[str] = []
    for i in range(member_count):
        sid = f"sym_t_{i}"
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
        (0.49, 0.505, 0.50, 0.505),
        (0.51, 0.495, 0.50, 0.495),
    ]
    for idx, sid in enumerate(member_ids):
        a, b, c, d = points[idx % len(points)]
        mem._symbol_signatures[sid] = _sig(a, b, c, d)
        mem._symbol_spreads[sid] = _spr(0.05)


def _apply_elongated_geometry(mem: NeutralFamilyMemoryV1, member_ids: list[str]) -> None:
    if len(member_ids) <= 1:
        return
    for idx, sid in enumerate(member_ids):
        t = idx / float(len(member_ids) - 1)
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


def test_compact_family_reports_compact_low_risk_topology(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, member_ids = _seed_family(mem, member_count=6)
    _apply_compact_geometry(mem, member_ids)

    topology = mem.get_family_topology_audit(fam_id)
    assert topology["found"] is True
    assert topology["topology_available"] is True
    assert topology["shape_class"] == "SHAPE_COMPACT"
    assert topology["compression_risk"] is False


def test_elongated_family_reports_elongated_topology(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, member_ids = _seed_family(mem, member_count=6)
    _apply_elongated_geometry(mem, member_ids)

    topology = mem.get_family_topology_audit(fam_id)
    assert topology["shape_class"] == "SHAPE_ELONGATED"
    assert topology["compression_risk"] is True
    assert "TOPOLOGY_COMPRESSION_RISK" in topology["topology_warnings"]


def test_dual_lobe_family_reports_dual_lobe_topology(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, member_ids = _seed_family(mem, member_count=8)
    _apply_dual_lobe_geometry(mem, member_ids)

    topology = mem.get_family_topology_audit(fam_id)
    assert topology["shape_class"] == "SHAPE_DUAL_LOBE"
    assert topology["topology_metrics"]["subgroup_detected"] is True
    assert topology["compression_risk"] is True


def test_small_family_reports_unknown_fail_closed_topology(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, member_ids = _seed_family(mem, member_count=3)
    _apply_compact_geometry(mem, member_ids)

    topology = mem.get_family_topology_audit(fam_id)
    assert topology["shape_class"] == "SHAPE_UNKNOWN"
    assert topology["topology_available"] is False
    assert topology["reason"] == "INSUFFICIENT_MEMBER_GEOMETRY_FOR_TOPOLOGY"


def test_topology_audit_is_separate_from_geometry_fit_status(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, member_ids = _seed_family(mem, member_count=6)
    _apply_elongated_geometry(mem, member_ids)

    rec = mem.get_family_record(fam_id)
    rec.current_signature = mem._compute_group_centroid(member_ids)
    rec.current_spread = mem._compute_group_spread_avg(member_ids)

    fit = mem.get_family_geometry_fit(fam_id)
    topology = mem.get_family_topology_audit(fam_id)

    assert fit["fit_status"] == "GEOMETRY_FIT_GOOD"
    assert topology["shape_class"] == "SHAPE_ELONGATED"


def test_dossier_includes_topology_summary_and_is_deterministic(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id, member_ids = _seed_family(mem, member_count=6)
    _apply_elongated_geometry(mem, member_ids)

    d1 = mem.get_family_dossier(fam_id, max_depth=4)
    d2 = mem.get_family_dossier(fam_id, max_depth=4)

    assert d1 == d2
    assert d1["topology_summary"]["shape_class"] == "SHAPE_ELONGATED"
