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


def _lineage_ok_report() -> dict:
    return {
        "ok": True,
        "issue_count": 0,
        "issue_counts_by_category": {
            "record_issues": 0,
            "ledger_issues": 0,
            "cross_source_issues": 0,
        },
    }


def test_durable_transition_ledger_audit_ready_path(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    report = mem.get_durable_transition_ledger_integrity_audit()

    assert report["audit_available"] is True
    assert report["audit_mode"] == "DURABLE_TRANSITION_LEDGER_INTEGRITY"
    assert report["audit_state"] == "DURABLE_TRANSITION_LEDGER_AUDIT_READY"
    assert report["audit_reason"] == "ALL_LEDGER_INTEGRITY_CHECKS_PASSED"
    assert report["integrity_counts"]["total_records"] > 0
    assert all(check["passed"] is True for check in report["check_results"])


def test_durable_transition_ledger_audit_partial_on_duplicate_event_ids(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    _emit_fission_and_reunion_chain(mem)

    events = mem.get_event_ledger()
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(events[0], sort_keys=True, separators=(",", ":")) + "\n")

    report = mem.get_durable_transition_ledger_integrity_audit()

    assert report["audit_available"] is True
    assert report["audit_state"] == "DURABLE_TRANSITION_LEDGER_AUDIT_PARTIAL"
    assert report["audit_reason"] == "LEDGER_INTEGRITY_LIMITED_OR_AMBIGUOUS"
    assert report["integrity_counts"]["duplicate_event_id_count"] >= 1
    assert report["integrity_counts"]["ambiguous_lookup_event_id_count"] >= 1
    assert "DUPLICATE_EVENT_ID_DETECTED" in report["warnings"]


def test_durable_transition_ledger_audit_unavailable_when_required_surface_missing(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    mem.get_event_ledger = None  # type: ignore[assignment]

    report = mem.get_durable_transition_ledger_integrity_audit()

    assert report["audit_available"] is False
    assert report["audit_state"] == "DURABLE_TRANSITION_LEDGER_AUDIT_UNAVAILABLE"
    assert report["audit_reason"] == "REQUIRED_SURFACE_MISSING"
    assert "REQUIRED_SURFACE_MISSING" in report["warnings"]


def test_durable_transition_ledger_audit_uses_only_allowed_surfaces(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    events = [
        {
            "event_id": "evt_0001",
            "event_type": "FAMILY_FISSION_V1",
            "source_family_ids": ["fam_01"],
            "successor_family_ids": ["fam_02", "fam_03"],
            "event_order": 1,
            "ledger_write_order": 1,
            "ledger_timestamp_utc": "2026-04-06T12:00:00Z",
        }
    ]

    def _forbidden(*_args, **_kwargs):
        raise AssertionError("unexpected direct call to non-audit schema anchor surface")

    mem.get_event_ledger = lambda: list(events)  # type: ignore[assignment]
    mem._get_ledger_event_by_id = lambda _event_id: (events[0], 1)  # type: ignore[assignment]
    mem.run_lineage_integrity_audit = lambda **_kwargs: _lineage_ok_report()  # type: ignore[assignment]
    mem.get_lineage_integrity_report = lambda **_kwargs: _lineage_ok_report()  # type: ignore[assignment]

    mem.get_transition_report = _forbidden  # type: ignore[assignment]
    mem.get_event_dossier = _forbidden  # type: ignore[assignment]
    mem.get_family_dossier = _forbidden  # type: ignore[assignment]

    report = mem.get_durable_transition_ledger_integrity_audit()

    assert report["audit_available"] is True
    assert report["audit_state"] == "DURABLE_TRANSITION_LEDGER_AUDIT_READY"
    assert report["audit_reason"] == "ALL_LEDGER_INTEGRITY_CHECKS_PASSED"


def test_durable_transition_ledger_audit_guardrail_flags_remain_false(tmp_path: Path):
    ledger = tmp_path / "family_event_ledger.jsonl"
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
    mem.get_event_ledger = lambda: []  # type: ignore[assignment]
    mem._get_ledger_event_by_id = lambda _event_id: (None, 0)  # type: ignore[assignment]
    mem.run_lineage_integrity_audit = lambda **_kwargs: _lineage_ok_report()  # type: ignore[assignment]
    mem.get_lineage_integrity_report = lambda **_kwargs: _lineage_ok_report()  # type: ignore[assignment]

    report = mem.get_durable_transition_ledger_integrity_audit()

    assert report["audit_state"] == "DURABLE_TRANSITION_LEDGER_AUDIT_PARTIAL"
    assert report["audit_reason"] == "LEDGER_EMPTY_NO_TRANSITION_RECORDS"
    assert report["lineage_mutation_performed"] is False
    assert report["event_creation_performed"] is False
    assert report["history_rewrite_performed"] is False
