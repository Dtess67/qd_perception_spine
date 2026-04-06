import pytest

from qd_perception.neutral_family_memory_v1 import (
    CorrectiveLearningRecordV1a,
    build_corrective_learning_record_v1a,
    format_corrective_learning_record_v1a,
    get_corrective_learning_record_contract_v1a,
    validate_corrective_learning_record_v1a,
)


def _builder_kwargs() -> dict:
    return {
        "correction_id": "corr_0101",
        "wrongness_class": "EVIDENCE_SCOPE_MISMATCH",
        "wrongness_surface": "get_system_evidence_review_summary",
        "detection_source": "tests/test_system_evidence_review.py",
        "affected_entity_ids": ["evt_1001", "fam_10"],
        "prior_state": {"review_state": "SYSTEM_EVIDENCE_REVIEW_PARTIAL"},
        "corrected_state": {"review_state": "SYSTEM_EVIDENCE_REVIEW_READY"},
        "reason_before": "OBSERVABILITY_REVIEW_SURFACE_MISSING_OR_UNUSABLE",
        "reason_after": "COMPOSED_EVIDENCE_SURFACES_READY",
        "evidence_delta": {"observability_review_available": {"before": False, "after": True}},
        "root_cause_class": "MISSING_REVIEW_SURFACE",
        "future_guardrail": "REQUIRE_OBSERVABILITY_REVIEW_READY_FOR_READY_STATE",
        "hold_recommended_next_time": True,
        "notes": "Builder/formatter usage path only; no autonomous learning behavior.",
    }


def test_builder_constructs_valid_record_v1a():
    record = build_corrective_learning_record_v1a(**_builder_kwargs())

    assert isinstance(record, CorrectiveLearningRecordV1a)
    assert record.correction_id == "corr_0101"
    assert record.wrongness_class == "EVIDENCE_SCOPE_MISMATCH"
    assert record.hold_recommended_next_time is True


def test_builder_rejects_invalid_input_via_contract_validation():
    bad = _builder_kwargs()
    bad["hold_recommended_next_time"] = "true"

    with pytest.raises(ValueError) as exc:
        build_corrective_learning_record_v1a(**bad)

    assert "hold_recommended_next_time must be bool." in str(exc.value)


def test_formatter_produces_stable_export_shape():
    record = build_corrective_learning_record_v1a(**_builder_kwargs())
    report_1 = format_corrective_learning_record_v1a(record)
    report_2 = format_corrective_learning_record_v1a(record)

    contract = get_corrective_learning_record_contract_v1a()
    required_fields = contract["required_fields"]

    assert report_1 == report_2
    assert report_1["report_available"] is True
    assert report_1["report_mode"] == "CORRECTIVE_LEARNING_RECORD_REPORT_V1A"
    assert report_1["report_reason"] == "CORRECTIVE_LEARNING_RECORD_FORMATTED"
    assert report_1["field_order"] == required_fields
    assert list(report_1["record"].keys()) == required_fields


def test_formatter_output_is_validation_compatible_with_v1a():
    record = build_corrective_learning_record_v1a(**_builder_kwargs())
    report = format_corrective_learning_record_v1a(record)

    validation_from_record = validate_corrective_learning_record_v1a(record)
    validation_from_export = validate_corrective_learning_record_v1a(report["record"])

    assert validation_from_record["valid"] is True
    assert validation_from_export["valid"] is True
    assert validation_from_export["reason"] == "CORRECTIVE_LEARNING_RECORD_VALID"


def test_formatter_guardrail_flags_remain_false():
    record = build_corrective_learning_record_v1a(**_builder_kwargs())
    report = format_corrective_learning_record_v1a(record)

    assert report["lineage_mutation_performed"] is False
    assert report["event_creation_performed"] is False
    assert report["history_rewrite_performed"] is False
