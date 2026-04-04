from pathlib import Path

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


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

    assert len(mem.get_fission_events()) == 1
    assert len(mem.get_reunion_events()) == 1


def test_dossier_for_fission_successor_has_origin_and_parent(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    dossier = mem.get_family_dossier("fam_02", max_depth=8)
    assert dossier["found"] is True
    origin = dossier["origin_lineage"]["origin"]
    assert origin["origin_event_type"] == "FAMILY_FISSION_V1"
    assert origin["parent_family_ids"] == ["fam_01"]


def test_dossier_for_reunion_successor_has_two_parents(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    dossier = mem.get_family_ancestry_report("fam_04", max_depth=8)
    origin = dossier["origin_lineage"]["origin"]
    assert origin["origin_event_type"] == "FAMILY_REUNION_V1"
    assert sorted(origin["parent_family_ids"]) == ["fam_02", "fam_03"]


def test_dossier_for_inactive_historical_family_includes_successors_and_events(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    dossier = mem.get_family_dossier("fam_01", max_depth=8)
    assert dossier["identity"]["lifecycle_status"] == "FAMILY_INACTIVE_SUCCESSOR_SPLIT"
    direct = dossier["descendants"]["direct_successor_family_ids"]
    assert direct == ["fam_02", "fam_03"]
    assert dossier["event_history"]["event_count"] >= 1


def test_dossier_integrity_summary_matches_per_family_audit(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    dossier = mem.get_family_dossier("fam_04", max_depth=8)
    audit = mem.run_lineage_integrity_audit(family_id="fam_04", max_depth=8)
    assert dossier["integrity_summary"]["issue_count"] == audit["issue_count"]
    assert dossier["integrity_summary"]["issue_counts_by_category"] == audit["issue_counts_by_category"]


def test_dossier_unknown_family_returns_structured_not_found(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    dossier = mem.get_family_dossier("fam_unknown", max_depth=8)
    assert dossier["found"] is False
    assert dossier["reason"] == "FAMILY_NOT_FOUND"
    assert dossier["identity"] is None
    assert dossier["origin_lineage"] is None
    assert dossier["descendants"] is None
    assert dossier["integrity_summary"] is None


def test_dossier_lineage_respects_max_depth_and_is_deterministic(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    d1 = mem.get_family_dossier("fam_04", max_depth=1)
    d2 = mem.get_family_dossier("fam_04", max_depth=1)
    assert d1 == d2
    lineage = d1["origin_lineage"]["lineage_chain"]
    depths = [node["depth"] for node in lineage["lineage_nodes"]]
    assert max(depths) <= 1
