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
    group_1 = list(fission_evt["partition"]["group_1_member_ids"])
    group_2 = list(fission_evt["partition"]["group_2_member_ids"])

    for _ in range(40):
        for sid in group_1:
            mem.join_or_create_family(sid, _sig(0.20), spread, 10)
        for sid in group_2:
            mem.join_or_create_family(sid, _sig(0.22), spread, 10)
        if mem.get_reunion_events():
            break

    assert len(mem.get_fission_events()) == 1
    assert len(mem.get_reunion_events()) == 1


def test_fission_transition_report_has_identity_participants_and_gate_summary(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    evt = mem.get_fission_events()[0]
    report = mem.get_transition_report(evt["event_id"], max_depth=8)

    assert report["found"] is True
    assert report["event_identity"]["event_type"] == "FAMILY_FISSION_V1"
    assert report["participants"]["source_family_ids"] == ["fam_01"]
    assert sorted(report["participants"]["successor_family_ids"]) == ["fam_02", "fam_03"]
    assert report["structural_gate_rationale"]["gate_summary"]["requires_fracture_status"] == "FAMILY_SPLIT_READY"
    assert report["geometry_fit_summary"]["event_identity"]["event_type"] == "FAMILY_FISSION_V1"
    assert report["topology_summary"]["event_identity"]["event_type"] == "FAMILY_FISSION_V1"


def test_reunion_transition_report_has_identity_participants_and_gate_summary(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    evt = mem.get_reunion_events()[0]
    report = mem.get_event_dossier(evt["event_id"], max_depth=8)

    assert report["found"] is True
    assert report["event_identity"]["event_type"] == "FAMILY_REUNION_V1"
    assert sorted(report["participants"]["source_family_ids"]) == ["fam_02", "fam_03"]
    assert report["participants"]["successor_family_ids"] == ["fam_04"]
    assert (
        report["structural_gate_rationale"]["gate_summary"]["reunion_persistence_threshold"]
        == mem.REUNION_PERSISTENCE_THRESHOLD
    )
    assert report["geometry_fit_summary"]["event_identity"]["event_type"] == "FAMILY_REUNION_V1"
    assert report["topology_summary"]["event_identity"]["event_type"] == "FAMILY_REUNION_V1"


def test_transition_report_integrity_summary_matches_event_participants(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    reunion_evt = mem.get_reunion_events()[0]
    successor = reunion_evt["successor_family_id"]

    # Inject participant lineage mismatch so event-scoped integrity view must catch it.
    rec = mem.get_family_record(successor)
    rec.lineage_parent_family_ids = ["fam_99"]

    report = mem.get_transition_report(reunion_evt["event_id"], max_depth=8)
    assert report["integrity_summary"]["issue_count"] >= 1
    issue_types = [
        x["issue_type"]
        for x in report["integrity_summary"]["cross_source_issues"]
    ]
    assert "SUCCESSOR_PARENT_LINEAGE_MISMATCH" in issue_types


def test_transition_report_unknown_event_is_fail_closed(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    report = mem.get_transition_report("evt_unknown_0001", max_depth=8)
    assert report["found"] is False
    assert report["reason"] == "EVENT_NOT_FOUND"
    assert report["event_identity"] is None
    assert report["participants"] is None
    assert report["integrity_summary"] is None
    assert report["geometry_fit_summary"] is None
    assert report["topology_summary"] is None


def test_transition_report_output_shape_and_order_are_deterministic(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    evt_id = mem.get_fission_events()[0]["event_id"]
    report_1 = mem.get_transition_report(evt_id, max_depth=1)
    report_2 = mem.get_transition_report(evt_id, max_depth=1)

    assert set(report_1.keys()) == {
        "event_id",
        "found",
        "max_depth",
        "event_identity",
        "structural_gate_rationale",
        "participants",
        "before_after_family_state",
        "lineage_links",
        "integrity_summary",
        "geometry_fit_summary",
        "topology_summary",
    }
    assert report_1 == report_2
    edges = report_1["lineage_links"]["source_to_successor_edges"]
    assert edges == [
        {
            "source_family_id": "fam_01",
            "successor_family_id": "fam_02",
            "event_id": evt_id,
            "event_type": "FAMILY_FISSION_V1",
        },
        {
            "source_family_id": "fam_01",
            "successor_family_id": "fam_03",
            "event_id": evt_id,
            "event_type": "FAMILY_FISSION_V1",
        },
    ]
