from pathlib import Path

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


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

    assert len(mem.get_fission_events()) == 1
    assert len(mem.get_reunion_events()) == 1


def test_well_fit_family_reports_low_residual_and_good_fit(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id = _seed_small_family(mem)

    fit = mem.get_family_geometry_fit(fam_id)
    assert fit["found"] is True
    assert fit["fit_available"] is True
    assert fit["fit_status"] == "GEOMETRY_FIT_GOOD"
    assert fit["residuals"]["center_residual"] <= mem.GEOMETRY_FIT_CENTER_RESIDUAL_MAX


def test_poor_fit_family_reports_elevated_residual_and_weak_fit(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id = _seed_small_family(mem)
    rec = mem.get_family_record(fam_id)

    rec.current_signature = _sig(0.95)
    fit = mem.get_family_geometry_fit(fam_id)
    assert fit["fit_status"] == "FIT_RESIDUAL_HIGH"
    assert "FIT_RESIDUAL_HIGH_CENTER" in fit["fit_warnings"]


def test_fit_distinguishes_broad_but_honest_from_geometrically_misleading(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    fam_id = _seed_small_family(mem)
    rec = mem.get_family_record(fam_id)

    # Force broad member placement while keeping family geometry honest.
    mem._symbol_signatures["sym_0"] = _sig(0.10)
    mem._symbol_signatures["sym_1"] = _sig(0.50)
    mem._symbol_signatures["sym_2"] = _sig(0.90)
    mem._symbol_spreads["sym_0"] = _spr(0.05)
    mem._symbol_spreads["sym_1"] = _spr(0.05)
    mem._symbol_spreads["sym_2"] = _spr(0.05)
    rec.current_signature = _sig(0.50)
    rec.current_spread = _spr(0.05)

    honest = mem.get_family_geometry_fit(fam_id)
    assert honest["fit_status"] == "GEOMETRY_FIT_GOOD"

    rec.current_signature = _sig(0.12)
    misleading = mem.get_family_geometry_fit(fam_id)
    assert misleading["fit_status"] == "FIT_RESIDUAL_HIGH"
    assert misleading["fit_score"] > honest["fit_score"]


def test_fission_successor_fit_is_reported(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    fission_evt_id = mem.get_fission_events()[0]["event_id"]
    fit = mem.get_transition_geometry_fit(fission_evt_id)
    assert fit["found"] is True
    assert fit["fit_available"] is True
    assert fit["event_identity"]["event_type"] == "FAMILY_FISSION_V1"
    successor_ids = fit["participants"]["successor_family_ids"]
    assert sorted(successor_ids) == ["fam_02", "fam_03"]
    fit_family_ids = sorted([x["family_id"] for x in fit["participant_family_fits"]])
    assert "fam_02" in fit_family_ids
    assert "fam_03" in fit_family_ids


def test_reunion_successor_fit_is_reported(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    reunion_evt_id = mem.get_reunion_events()[0]["event_id"]
    fit = mem.get_transition_geometry_fit(reunion_evt_id)
    assert fit["found"] is True
    assert fit["fit_available"] is True
    assert fit["event_identity"]["event_type"] == "FAMILY_REUNION_V1"
    assert fit["participants"]["successor_family_ids"] == ["fam_04"]
    fit_by_id = {x["family_id"]: x for x in fit["participant_family_fits"]}
    assert fit_by_id["fam_04"]["fit_available"] is True


def test_geometry_fit_output_is_structured_and_deterministic(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    fam_fit_1 = mem.get_family_geometry_fit("fam_04")
    fam_fit_2 = mem.get_family_geometry_fit("fam_04")
    assert fam_fit_1 == fam_fit_2

    evt_id = mem.get_reunion_events()[0]["event_id"]
    evt_fit_1 = mem.get_transition_geometry_fit(evt_id)
    evt_fit_2 = mem.get_transition_geometry_fit(evt_id)
    assert evt_fit_1 == evt_fit_2
