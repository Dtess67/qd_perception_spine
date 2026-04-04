from unittest.mock import MagicMock

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


class TestObservabilityEvidenceReviewSummary:
    def test_ready_path(self, tmp_path):
        ledger = tmp_path / "observability_evidence_review_ready.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_pressure_capture_quality_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "LEDGER_READ_ONLY",
                "reason": "OK",
                "total_transition_events": 3,
                "auditable_event_count": 3,
                "pressure_snapshot_present_count": 3,
                "pressure_snapshot_missing_count": 0,
                "audit_state_counts": {
                    "PRESSURE_CAPTURE_AUDIT_VALID": 3,
                    "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                    "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                },
                "capture_reason_counts": {
                    "PRESSURE_CAPTURE_FULL": 3,
                    "PRESSURE_CAPTURE_PARTIAL": 0,
                    "PRESSURE_CAPTURE_FAILED": 0,
                    "UNRECOGNIZED_CAPTURE_REASON": 0,
                },
                "recoverability_counts": {
                    "FULLY_RECOVERABLE": 3,
                    "PARTIALLY_RECOVERABLE": 0,
                    "UNRECOVERABLE": 0,
                },
                "event_type_counts": {"FAMILY_FISSION": 3},
                "warnings": ["QUALITY_WARN"],
                "explanation_lines": ["quality ready"],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_observability_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "OBSERVABILITY_STAGE_LOCK",
                "lock_state": "OBSERVABILITY_STAGE_LOCKED",
                "reason": "ALL_REQUIRED_CHECKS_PASSED",
                "warnings": ["LOCK_WARN"],
                "explanation_lines": ["stage lock green"],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_observability_evidence_review_summary()

        assert out["review_available"] is True
        assert out["review_mode"] == "OBSERVABILITY_EVIDENCE_REVIEW"
        assert out["review_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_READY"
        assert out["review_reason"] == "LOCKED_WITH_FULLY_AUDITABLE_OBSERVABILITY_EVIDENCE"
        assert out["evidence_counts"]["total_auditable_events"] == 3
        assert "QUALITY_WARN" in out["warnings"]
        assert "LOCK_WARN" in out["warnings"]

    def test_partial_path(self, tmp_path):
        ledger = tmp_path / "observability_evidence_review_partial.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_pressure_capture_quality_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "LEDGER_READ_ONLY",
                "reason": "OK",
                "total_transition_events": 4,
                "auditable_event_count": 4,
                "pressure_snapshot_present_count": 3,
                "pressure_snapshot_missing_count": 1,
                "audit_state_counts": {
                    "PRESSURE_CAPTURE_AUDIT_VALID": 2,
                    "PRESSURE_CAPTURE_AUDIT_INVALID": 1,
                    "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 1,
                },
                "capture_reason_counts": {
                    "PRESSURE_CAPTURE_FULL": 1,
                    "PRESSURE_CAPTURE_PARTIAL": 2,
                    "PRESSURE_CAPTURE_FAILED": 1,
                    "UNRECOGNIZED_CAPTURE_REASON": 0,
                },
                "recoverability_counts": {
                    "FULLY_RECOVERABLE": 1,
                    "PARTIALLY_RECOVERABLE": 2,
                    "UNRECOVERABLE": 1,
                },
                "event_type_counts": {"FAMILY_FISSION": 2, "FAMILY_REUNION": 2},
                "warnings": [],
                "explanation_lines": ["mixed quality"],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_observability_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "OBSERVABILITY_STAGE_LOCK",
                "lock_state": "OBSERVABILITY_STAGE_LOCK_INCONSISTENT",
                "reason": "CHECK_FAILURES_DETECTED",
                "warnings": ["OBSERVABILITY_STAGE_LOCK_CHECK_FAILURES"],
                "explanation_lines": ["stage lock inconsistent"],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_observability_evidence_review_summary()

        assert out["review_available"] is True
        assert out["review_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_PARTIAL"
        assert out["review_reason"] == "LIMITED_OR_MIXED_OBSERVABILITY_EVIDENCE"

    def test_unavailable_when_required_surface_missing(self, tmp_path):
        ledger = tmp_path / "observability_evidence_review_missing_surface.jsonl"
        ledger.write_text("")

        class MemWithoutStageLock(NeutralFamilyMemoryV1):
            def __getattribute__(self, name):
                if name == "get_observability_stage_lock_audit":
                    raise AttributeError(name)
                return super().__getattribute__(name)

        mem = MemWithoutStageLock(durable_ledger_path=str(ledger))
        out = mem.get_observability_evidence_review_summary()

        assert out["review_available"] is False
        assert out["review_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE"
        assert out["review_reason"] == "REQUIRED_SURFACE_MISSING"

    def test_no_hidden_direct_call_dependency_beyond_allowed_surfaces(self, tmp_path):
        ledger = tmp_path / "observability_evidence_review_no_hidden_dependency.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_pressure_capture_quality_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "LEDGER_READ_ONLY",
                "reason": "OK",
                "total_transition_events": 1,
                "auditable_event_count": 1,
                "pressure_snapshot_present_count": 1,
                "pressure_snapshot_missing_count": 0,
                "audit_state_counts": {
                    "PRESSURE_CAPTURE_AUDIT_VALID": 1,
                    "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                    "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                },
                "capture_reason_counts": {
                    "PRESSURE_CAPTURE_FULL": 1,
                    "PRESSURE_CAPTURE_PARTIAL": 0,
                    "PRESSURE_CAPTURE_FAILED": 0,
                    "UNRECOGNIZED_CAPTURE_REASON": 0,
                },
                "recoverability_counts": {
                    "FULLY_RECOVERABLE": 1,
                    "PARTIALLY_RECOVERABLE": 0,
                    "UNRECOVERABLE": 0,
                },
                "event_type_counts": {"FAMILY_FISSION": 1},
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_observability_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "OBSERVABILITY_STAGE_LOCK",
                "lock_state": "OBSERVABILITY_STAGE_LOCKED",
                "reason": "ALL_REQUIRED_CHECKS_PASSED",
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        mem.get_cross_band_evidence_review_summary = MagicMock()
        mem.get_system_lock_gate_posture = MagicMock()
        mem.get_system_evidence_review_summary = MagicMock()
        mem.get_transition_pressure_capture_audit = MagicMock()
        mem.get_pressure_capture_quality_summary_window = MagicMock()
        mem.get_pressure_capture_quality_summary_event_order_window = MagicMock()
        mem.get_pressure_capture_quality_window_comparator = MagicMock()

        out = mem.get_observability_evidence_review_summary()

        assert out["review_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_READY"
        mem.get_cross_band_evidence_review_summary.assert_not_called()
        mem.get_system_lock_gate_posture.assert_not_called()
        mem.get_system_evidence_review_summary.assert_not_called()
        mem.get_transition_pressure_capture_audit.assert_not_called()
        mem.get_pressure_capture_quality_summary_window.assert_not_called()
        mem.get_pressure_capture_quality_summary_event_order_window.assert_not_called()
        mem.get_pressure_capture_quality_window_comparator.assert_not_called()

    def test_guardrail_flags_remain_false(self, tmp_path):
        ledger = tmp_path / "observability_evidence_review_guardrails.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_pressure_capture_quality_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "LEDGER_READ_ONLY",
                "reason": "OK",
                "total_transition_events": 2,
                "auditable_event_count": 2,
                "pressure_snapshot_present_count": 1,
                "pressure_snapshot_missing_count": 1,
                "audit_state_counts": {
                    "PRESSURE_CAPTURE_AUDIT_VALID": 1,
                    "PRESSURE_CAPTURE_AUDIT_INVALID": 1,
                    "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                },
                "capture_reason_counts": {
                    "PRESSURE_CAPTURE_FULL": 1,
                    "PRESSURE_CAPTURE_PARTIAL": 1,
                    "PRESSURE_CAPTURE_FAILED": 0,
                    "UNRECOGNIZED_CAPTURE_REASON": 0,
                },
                "recoverability_counts": {
                    "FULLY_RECOVERABLE": 1,
                    "PARTIALLY_RECOVERABLE": 0,
                    "UNRECOVERABLE": 1,
                },
                "event_type_counts": {"FAMILY_REUNION": 2},
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": True,
                "event_creation_performed": True,
                "history_rewrite_performed": True,
            }
        )
        mem.get_observability_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "OBSERVABILITY_STAGE_LOCK",
                "lock_state": "OBSERVABILITY_STAGE_LOCK_INCONSISTENT",
                "reason": "CHECK_FAILURES_DETECTED",
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": True,
                "event_creation_performed": True,
                "history_rewrite_performed": True,
            }
        )

        out = mem.get_observability_evidence_review_summary()

        assert out["lineage_mutation_performed"] is False
        assert out["event_creation_performed"] is False
        assert out["history_rewrite_performed"] is False
