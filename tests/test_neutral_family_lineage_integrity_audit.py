import json
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


def test_clean_lineage_state_passes_audit(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    report = mem.run_lineage_integrity_audit(max_depth=8)
    assert report["ok"] is True
    assert report["issue_count"] == 0
    assert report["issue_counts_by_category"]["record_issues"] == 0
    assert report["issue_counts_by_category"]["ledger_issues"] == 0
    assert report["issue_counts_by_category"]["cross_source_issues"] == 0


def test_duplicate_durable_event_ids_are_detected(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    events = mem.get_event_ledger()
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(events[0], sort_keys=True, separators=(",", ":")) + "\n")

    report = mem.run_lineage_integrity_audit(max_depth=8)
    issue_types = [x["issue_type"] for x in report["ledger_issues"]]
    assert "LEDGER_DUPLICATE_EVENT_ID" in issue_types


def test_inactive_family_with_active_members_is_detected(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    fam_01 = mem.get_family_record("fam_01")
    fam_01.member_symbol_ids = ["sym_f_0"]

    report = mem.run_lineage_integrity_audit(max_depth=8)
    issue_types = [x["issue_type"] for x in report["record_issues"]]
    assert "INACTIVE_FAMILY_HAS_ACTIVE_MEMBERS" in issue_types


def test_lineage_mismatch_between_family_record_and_ledger_is_detected(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    fam_04 = mem.get_family_record("fam_04")
    fam_04.lineage_parent_family_ids = ["fam_99"]

    report = mem.run_lineage_integrity_audit(max_depth=8)
    mismatch = [
        x for x in report["cross_source_issues"]
        if x["issue_type"] == "SUCCESSOR_PARENT_LINEAGE_MISMATCH" and x.get("family_id") == "fam_04"
    ]
    assert len(mismatch) >= 1


def test_one_family_only_violation_is_detected(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    # Inject same symbol into another family record to violate one-family-only.
    fam_01 = mem.get_family_record("fam_01")
    fam_01.member_symbol_ids = ["sym_f_0"]

    report = mem.run_lineage_integrity_audit(max_depth=8)
    issue_types = [x["issue_type"] for x in report["record_issues"]]
    assert "SYMBOL_MULTI_FAMILY_MEMBERSHIP_VIOLATION" in issue_types


def test_ancestry_loop_condition_is_detected_or_safely_reported(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    events = [
        {
            "event_id": "evt_cycle_0001",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_a"],
            "successor_family_ids": ["fam_b"],
            "gate_summary": {},
            "rationale": "cycle_a_to_b",
        },
        {
            "event_id": "evt_cycle_0002",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 2,
            "source_family_ids": ["fam_b"],
            "successor_family_ids": ["fam_a"],
            "gate_summary": {},
            "rationale": "cycle_b_to_a",
        },
    ]
    with ledger.open("w", encoding="utf-8") as f:
        for evt in events:
            f.write(json.dumps(evt, sort_keys=True, separators=(",", ":")) + "\n")

    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    report = mem.run_lineage_integrity_audit(max_depth=8)
    issue_types = [x["issue_type"] for x in report["cross_source_issues"]]
    assert "LINEAGE_LOOP_DETECTED" in issue_types


def test_audit_output_is_structured_and_deterministic(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    report_1 = mem.run_lineage_integrity_audit(max_depth=8)
    report_2 = mem.run_lineage_integrity_audit(max_depth=8)

    assert set(report_1.keys()) == {
        "ok",
        "issue_count",
        "checked_family_id",
        "family_known",
        "max_depth",
        "record_issues",
        "ledger_issues",
        "cross_source_issues",
        "issue_counts_by_category",
    }
    assert report_1 == report_2
