from qd_perception.neutral_family_memory_v1 import (
    CorrectiveLearningRecordV1a,
    get_corrective_learning_record_contract_v1a,
    validate_corrective_learning_record_v1a,
)


def _valid_record_dict() -> dict:
    return {
        "correction_id": "corr_0001",
        "wrongness_class": "LEDGER_SCHEMA_DRIFT",
        "wrongness_surface": "get_durable_transition_ledger_integrity_audit",
        "detection_source": "tests/test_durable_transition_ledger_integrity_audit.py",
        "affected_entity_ids": ["evt_0100", "fam_03"],
        "prior_state": {"review_state": "PARTIAL"},
        "corrected_state": {"review_state": "READY"},
        "reason_before": "LEDGER_INTEGRITY_LIMITED_OR_AMBIGUOUS",
        "reason_after": "ALL_LEDGER_INTEGRITY_CHECKS_PASSED",
        "evidence_delta": {"duplicate_event_id_count": {"before": 1, "after": 0}},
        "root_cause_class": "DUPLICATE_EVENT_ID",
        "future_guardrail": "REQUIRE_EVENT_ID_UNIQUENESS_PRECHECK",
        "hold_recommended_next_time": True,
        "notes": "Contract-only memory record; no autonomous behavior.",
    }


def test_corrective_learning_contract_shape_v1a():
    contract = get_corrective_learning_record_contract_v1a()

    assert contract["contract_available"] is True
    assert contract["contract_mode"] == "CORRECTIVE_LEARNING_RECORD_CONTRACT_V1A"
    assert contract["contract_only"] is True
    assert len(contract["required_fields"]) == 14
    assert contract["lineage_mutation_performed"] is False
    assert contract["event_creation_performed"] is False
    assert contract["history_rewrite_performed"] is False


def test_corrective_learning_validator_accepts_valid_dict():
    result = validate_corrective_learning_record_v1a(_valid_record_dict())

    assert result["validation_available"] is True
    assert result["validation_mode"] == "CORRECTIVE_LEARNING_RECORD_VALIDATION_V1A"
    assert result["valid"] is True
    assert result["reason"] == "CORRECTIVE_LEARNING_RECORD_VALID"
    assert result["errors"] == []
    assert result["normalized_record"]["correction_id"] == "corr_0001"


def test_corrective_learning_validator_accepts_dataclass_instance():
    rec = CorrectiveLearningRecordV1a(**_valid_record_dict())

    result = validate_corrective_learning_record_v1a(rec)

    assert result["valid"] is True
    assert result["normalized_record"]["wrongness_surface"] == "get_durable_transition_ledger_integrity_audit"


def test_corrective_learning_validator_rejects_missing_fields():
    record = _valid_record_dict()
    del record["wrongness_class"]

    result = validate_corrective_learning_record_v1a(record)

    assert result["valid"] is False
    assert result["reason"] == "CORRECTIVE_LEARNING_RECORD_INVALID"
    assert any("Missing required fields" in err for err in result["errors"])


def test_corrective_learning_validator_rejects_type_drift_and_extra_fields():
    record = _valid_record_dict()
    record["hold_recommended_next_time"] = "yes"
    record["affected_entity_ids"] = ["evt_0100", ""]
    record["evidence_delta"] = []
    record["unexpected"] = 123

    result = validate_corrective_learning_record_v1a(record)

    assert result["valid"] is False
    assert any("Unexpected fields present" in err for err in result["errors"])
    assert any("hold_recommended_next_time must be bool." in err for err in result["errors"])
    assert any("affected_entity_ids elements must be non-empty strings." in err for err in result["errors"])
    assert any("evidence_delta must be a dict." in err for err in result["errors"])
    assert result["normalized_record"] is None


def test_corrective_learning_validator_guardrail_flags_remain_false():
    result = validate_corrective_learning_record_v1a(_valid_record_dict())

    assert result["lineage_mutation_performed"] is False
    assert result["event_creation_performed"] is False
    assert result["history_rewrite_performed"] is False
