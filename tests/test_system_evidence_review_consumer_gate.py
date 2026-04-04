from unittest.mock import MagicMock

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


class TestSystemEvidenceReviewConsumerGate:
    def test_gate_rely_when_v1_1_ready_and_v1_2_locked(self, tmp_path):
        ledger = tmp_path / "system_evidence_consumer_gate_ready.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_system_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_READY",
                "review_reason": "COMPOSED_EVIDENCE_SURFACES_READY",
                "warnings": [],
                "explanation_lines": ["summary-ready"],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_system_evidence_review_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK",
                "lock_state": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCKED",
                "reason": "ALL_CONSISTENCY_CHECKS_PASSED",
                "warnings": [],
                "explanation_lines": ["stage-lock-locked"],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_system_evidence_review_consumer_gate()

        assert out["gate_available"] is True
        assert out["gate_mode"] == "SYSTEM_EVIDENCE_REVIEW_CONSUMER_GATE"
        assert out["gate_state"] == "SYSTEM_EVIDENCE_GATE_RELY"
        assert out["gate_reason"] == "SYSTEM_EVIDENCE_REVIEW_READY_AND_STAGE_LOCKED"
        mem.get_system_evidence_review_summary.assert_called_once()
        mem.get_system_evidence_review_stage_lock_audit.assert_called_once()

    def test_gate_limited_when_v1_1_partial_under_locked_v1_2(self, tmp_path):
        ledger = tmp_path / "system_evidence_consumer_gate_partial.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_system_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_PARTIAL",
                "review_reason": "LIMITED_OR_ASYMMETRIC_EVIDENCE_SURFACE",
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_system_evidence_review_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK",
                "lock_state": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCKED",
                "reason": "ALL_CONSISTENCY_CHECKS_PASSED",
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_system_evidence_review_consumer_gate()

        assert out["gate_state"] == "SYSTEM_EVIDENCE_GATE_LIMITED"
        assert out["gate_reason"] == "SYSTEM_EVIDENCE_REVIEW_PARTIAL_UNDER_STAGE_LOCK"

    def test_gate_hold_when_v1_2_inconsistent(self, tmp_path):
        ledger = tmp_path / "system_evidence_consumer_gate_inconsistent.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_system_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_READY",
                "review_reason": "COMPOSED_EVIDENCE_SURFACES_READY",
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_system_evidence_review_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK",
                "lock_state": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT",
                "reason": "CONSISTENCY_CHECK_FAILED",
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_system_evidence_review_consumer_gate()

        assert out["gate_state"] == "SYSTEM_EVIDENCE_GATE_HOLD"
        assert out["gate_reason"] == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT"

    def test_gate_hold_when_v1_2_unavailable(self, tmp_path):
        ledger = tmp_path / "system_evidence_consumer_gate_unavailable.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_system_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_READY",
                "review_reason": "COMPOSED_EVIDENCE_SURFACES_READY",
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_system_evidence_review_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": False,
                "audit_mode": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK",
                "lock_state": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE",
                "reason": "REQUIRED_SURFACE_UNUSABLE",
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_system_evidence_review_consumer_gate()

        assert out["gate_state"] == "SYSTEM_EVIDENCE_GATE_HOLD"
        assert out["gate_reason"] == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_AUDIT_UNAVAILABLE"

    def test_no_hidden_optional_surface_predicates_or_direct_calls(self, tmp_path):
        ledger = tmp_path / "system_evidence_consumer_gate_no_hidden_predicates.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        # Primary surfaces are mocked and intentionally include contradictory context values.
        mem.get_system_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_READY",
                "review_reason": "COMPOSED_EVIDENCE_SURFACES_READY",
                "evidence_scope": {
                    "system_gate_state": "SYSTEM_GATE_UNAVAILABLE",
                    "observability_stage_lock_state": "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE",
                },
                "supporting_surfaces": {
                    "observability_pressure_capture_quality_summary": {
                        "summary_available": False,
                        "auditable_event_count": 0,
                    }
                },
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_system_evidence_review_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK",
                "lock_state": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCKED",
                "reason": "ALL_CONSISTENCY_CHECKS_PASSED",
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        # Optional/context-only APIs must not be used directly by v1.3 gate.
        mem.get_pressure_capture_quality_summary = MagicMock()
        mem.get_observability_stage_lock_audit = MagicMock()
        mem.get_system_lock_gate_posture = MagicMock()
        mem.get_cross_band_evidence_review_summary = MagicMock()

        out = mem.get_system_evidence_review_consumer_gate()

        assert out["gate_state"] == "SYSTEM_EVIDENCE_GATE_RELY"
        assert out["gate_reason"] == "SYSTEM_EVIDENCE_REVIEW_READY_AND_STAGE_LOCKED"
        mem.get_pressure_capture_quality_summary.assert_not_called()
        mem.get_observability_stage_lock_audit.assert_not_called()
        mem.get_system_lock_gate_posture.assert_not_called()
        mem.get_cross_band_evidence_review_summary.assert_not_called()
