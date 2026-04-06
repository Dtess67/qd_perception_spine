from pathlib import Path

from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1,
    map_durable_ledger_audit_findings_to_corrective_records_v1_2,
    validate_corrective_learning_record_v1a,
)


def _base_lineage_ok() -> dict:
    return {
        "ok": True,
        "issue_count": 0,
        "issue_counts_by_category": {
            "record_issues": 0,
            "ledger_issues": 0,
            "cross_source_issues": 0,
        },
    }


def _event(
    *,
    event_id: str,
    event_type: str = "FAMILY_FISSION_V1",
    source_family_ids=None,
    successor_family_ids=None,
    event_order: int = 1,
    ledger_write_order: int = 1,
):
    return {
        "event_id": event_id,
        "event_type": event_type,
        "source_family_ids": source_family_ids if source_family_ids is not None else ["fam_01"],
        "successor_family_ids": successor_family_ids if successor_family_ids is not None else ["fam_02"],
        "event_order": event_order,
        "ledger_write_order": ledger_write_order,
        "ledger_timestamp_utc": "2026-04-06T12:00:00Z",
    }


def _mapped_record_by_class(mapping: dict, wrongness_class: str) -> dict | None:
    for rec in mapping.get("corrective_records", []):
        if isinstance(rec, dict) and rec.get("wrongness_class") == wrongness_class:
            return rec
    return None


def test_mapping_duplicate_event_id_ambiguity_to_valid_corrective_record(tmp_path: Path):
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(tmp_path / "ledger.jsonl"))
    e1 = _event(event_id="evt_dup_001", event_order=1, ledger_write_order=1)
    e2 = _event(event_id="evt_dup_001", event_order=2, ledger_write_order=2)
    mem.get_event_ledger = lambda: [dict(e1), dict(e2)]  # type: ignore[assignment]
    mem.run_lineage_integrity_audit = lambda **_kwargs: _base_lineage_ok()  # type: ignore[assignment]
    mem.get_lineage_integrity_report = lambda **_kwargs: _base_lineage_ok()  # type: ignore[assignment]

    audit = mem.get_durable_transition_ledger_integrity_audit()
    mapping = map_durable_ledger_audit_findings_to_corrective_records_v1_2(audit)
    rec = _mapped_record_by_class(mapping, "LEDGER_EVENT_ID_AMBIGUITY")

    assert "DUPLICATE_EVENT_ID_DETECTED" in audit["warnings"]
    assert mapping["mapping_reason"] == "MAPPABLE_FINDINGS_CONVERTED"
    assert rec is not None
    assert validate_corrective_learning_record_v1a(rec)["valid"] is True


def test_mapping_ordering_issue_to_valid_corrective_record(tmp_path: Path):
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(tmp_path / "ledger.jsonl"))
    e1 = _event(event_id="evt_ord_001", event_order=1, ledger_write_order=2)
    e2 = _event(event_id="evt_ord_002", event_order=2, ledger_write_order=1)
    mem.get_event_ledger = lambda: [dict(e1), dict(e2)]  # type: ignore[assignment]
    mem.run_lineage_integrity_audit = lambda **_kwargs: _base_lineage_ok()  # type: ignore[assignment]
    mem.get_lineage_integrity_report = lambda **_kwargs: _base_lineage_ok()  # type: ignore[assignment]

    audit = mem.get_durable_transition_ledger_integrity_audit()
    mapping = map_durable_ledger_audit_findings_to_corrective_records_v1_2(audit)
    rec = _mapped_record_by_class(mapping, "LEDGER_ORDERING_INTEGRITY_DRIFT")

    assert "LEDGER_ORDERING_ISSUES_DETECTED" in audit["warnings"]
    assert rec is not None
    assert validate_corrective_learning_record_v1a(rec)["valid"] is True


def test_mapping_schema_issue_to_valid_corrective_record(tmp_path: Path):
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(tmp_path / "ledger.jsonl"))
    bad = _event(event_id="evt_schema_001", event_order=1, ledger_write_order=1)
    bad["event_type"] = ""
    bad["source_family_ids"] = "fam_01"
    bad["ledger_write_order"] = "not-int"
    mem.get_event_ledger = lambda: [dict(bad)]  # type: ignore[assignment]
    mem.run_lineage_integrity_audit = lambda **_kwargs: _base_lineage_ok()  # type: ignore[assignment]
    mem.get_lineage_integrity_report = lambda **_kwargs: _base_lineage_ok()  # type: ignore[assignment]

    audit = mem.get_durable_transition_ledger_integrity_audit()
    mapping = map_durable_ledger_audit_findings_to_corrective_records_v1_2(audit)
    rec = _mapped_record_by_class(mapping, "LEDGER_SCHEMA_CONFORMANCE_ISSUE")

    assert "LEDGER_SCHEMA_ISSUES_DETECTED" in audit["warnings"]
    assert rec is not None
    assert validate_corrective_learning_record_v1a(rec)["valid"] is True


def test_mapping_lineage_anchor_mismatch_to_valid_corrective_record(tmp_path: Path):
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(tmp_path / "ledger.jsonl"))
    mem.get_event_ledger = lambda: [dict(_event(event_id="evt_lin_001"))]  # type: ignore[assignment]
    mem.run_lineage_integrity_audit = lambda **_kwargs: _base_lineage_ok()  # type: ignore[assignment]
    mem.get_lineage_integrity_report = (  # type: ignore[assignment]
        lambda **_kwargs: {
            **_base_lineage_ok(),
            "shape_variant": "mismatch",
        }
    )

    audit = mem.get_durable_transition_ledger_integrity_audit()
    mapping = map_durable_ledger_audit_findings_to_corrective_records_v1_2(audit)
    rec = _mapped_record_by_class(mapping, "LINEAGE_ANCHOR_CONSISTENCY_ISSUE")

    assert "LINEAGE_ANCHOR_SURFACE_MISMATCH" in audit["warnings"]
    assert rec is not None
    assert validate_corrective_learning_record_v1a(rec)["valid"] is True


def test_mapping_no_findings_returns_empty_set_and_guardrails_false(tmp_path: Path):
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(tmp_path / "ledger.jsonl"))
    mem.get_event_ledger = lambda: [dict(_event(event_id="evt_ok_001"))]  # type: ignore[assignment]
    mem.run_lineage_integrity_audit = lambda **_kwargs: _base_lineage_ok()  # type: ignore[assignment]
    mem.get_lineage_integrity_report = lambda **_kwargs: _base_lineage_ok()  # type: ignore[assignment]

    audit = mem.get_durable_transition_ledger_integrity_audit()
    mapping = map_durable_ledger_audit_findings_to_corrective_records_v1_2(audit)

    assert audit["audit_state"] == "DURABLE_TRANSITION_LEDGER_AUDIT_READY"
    assert mapping["mapping_available"] is True
    assert mapping["mapping_reason"] == "NO_MAPPABLE_FINDINGS"
    assert mapping["record_count"] == 0
    assert mapping["lineage_mutation_performed"] is False
    assert mapping["event_creation_performed"] is False
    assert mapping["history_rewrite_performed"] is False
