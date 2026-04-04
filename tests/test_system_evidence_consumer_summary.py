from unittest.mock import MagicMock

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


class TestSystemEvidenceConsumerSummary:
    def test_packages_ready_locked_rely_posture(self, tmp_path):
        ledger = tmp_path / "system_evidence_consumer_summary_ready.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        review = {
            "review_available": True,
            "review_mode": "SYSTEM_EVIDENCE_REVIEW",
            "review_state": "SYSTEM_EVIDENCE_REVIEW_READY",
            "review_reason": "COMPOSED_EVIDENCE_SURFACES_READY",
            "warnings": ["R_WARN"],
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }
        stage_lock = {
            "audit_available": True,
            "audit_mode": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK",
            "lock_state": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCKED",
            "reason": "ALL_CONSISTENCY_CHECKS_PASSED",
            "warnings": ["L_WARN"],
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }
        gate = {
            "gate_available": True,
            "gate_mode": "SYSTEM_EVIDENCE_REVIEW_CONSUMER_GATE",
            "gate_state": "SYSTEM_EVIDENCE_GATE_RELY",
            "gate_reason": "SYSTEM_EVIDENCE_REVIEW_READY_AND_STAGE_LOCKED",
            "warnings": ["G_WARN"],
            "explanation_lines": ["gate-line"],
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

        mem.get_system_evidence_review_summary = MagicMock(return_value=review)
        mem.get_system_evidence_review_stage_lock_audit = MagicMock(return_value=stage_lock)
        mem.get_system_evidence_review_consumer_gate = MagicMock(return_value=gate)

        out = mem.get_system_evidence_consumer_summary()

        assert out["summary_available"] is True
        assert out["summary_mode"] == "SYSTEM_EVIDENCE_CONSUMER_SUMMARY"
        assert out["summary_state"] == "SYSTEM_EVIDENCE_GATE_RELY"
        assert out["summary_reason"] == "SYSTEM_EVIDENCE_REVIEW_READY_AND_STAGE_LOCKED"
        assert out["consumer_posture"]["review_state"] == "SYSTEM_EVIDENCE_REVIEW_READY"
        assert out["consumer_posture"]["stage_lock_state"] == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCKED"
        assert out["consumer_posture"]["gate_state"] == "SYSTEM_EVIDENCE_GATE_RELY"
        assert "R_WARN" in out["warnings"]
        assert "L_WARN" in out["warnings"]
        assert "G_WARN" in out["warnings"]

    def test_packages_partial_locked_limited_posture(self, tmp_path):
        ledger = tmp_path / "system_evidence_consumer_summary_partial.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_system_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_PARTIAL",
                "review_reason": "LIMITED_OR_ASYMMETRIC_EVIDENCE_SURFACE",
                "warnings": [],
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
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_system_evidence_review_consumer_gate = MagicMock(
            return_value={
                "gate_available": True,
                "gate_mode": "SYSTEM_EVIDENCE_REVIEW_CONSUMER_GATE",
                "gate_state": "SYSTEM_EVIDENCE_GATE_LIMITED",
                "gate_reason": "SYSTEM_EVIDENCE_REVIEW_PARTIAL_UNDER_STAGE_LOCK",
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_system_evidence_consumer_summary()

        assert out["summary_state"] == "SYSTEM_EVIDENCE_GATE_LIMITED"
        assert out["summary_reason"] == "SYSTEM_EVIDENCE_REVIEW_PARTIAL_UNDER_STAGE_LOCK"
        assert out["consumer_posture"]["review_state"] == "SYSTEM_EVIDENCE_REVIEW_PARTIAL"
        assert out["consumer_posture"]["stage_lock_state"] == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCKED"
        assert out["consumer_posture"]["gate_state"] == "SYSTEM_EVIDENCE_GATE_LIMITED"

    def test_packages_hold_posture_on_unavailable_or_inconsistent(self, tmp_path):
        ledger = tmp_path / "system_evidence_consumer_summary_hold.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_system_evidence_review_summary = MagicMock(
            return_value={
                "review_available": False,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE",
                "review_reason": "REQUIRED_SURFACE_UNUSABLE",
                "warnings": [],
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
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_system_evidence_review_consumer_gate = MagicMock(
            return_value={
                "gate_available": True,
                "gate_mode": "SYSTEM_EVIDENCE_REVIEW_CONSUMER_GATE",
                "gate_state": "SYSTEM_EVIDENCE_GATE_HOLD",
                "gate_reason": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT",
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_system_evidence_consumer_summary()

        assert out["summary_state"] == "SYSTEM_EVIDENCE_GATE_HOLD"
        assert out["summary_reason"] == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT"
        assert out["consumer_posture"]["gate_state"] == "SYSTEM_EVIDENCE_GATE_HOLD"

    def test_no_hidden_predicates_beyond_v1_1_v1_2_v1_3_outputs(self, tmp_path):
        ledger = tmp_path / "system_evidence_consumer_summary_no_hidden_predicates.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        # Deliberately inconsistent primary surfaces: summary must package gate output only.
        mem.get_system_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_READY",
                "review_reason": "COMPOSED_EVIDENCE_SURFACES_READY",
                "evidence_scope": {"system_gate_state": "SYSTEM_GATE_UNAVAILABLE"},
                "warnings": [],
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
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_system_evidence_review_consumer_gate = MagicMock(
            return_value={
                "gate_available": True,
                "gate_mode": "SYSTEM_EVIDENCE_REVIEW_CONSUMER_GATE",
                "gate_state": "SYSTEM_EVIDENCE_GATE_LIMITED",
                "gate_reason": "SYSTEM_EVIDENCE_REVIEW_PARTIAL_UNDER_STAGE_LOCK",
                "warnings": [],
                "explanation_lines": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        # These must not be used directly by v1.4 summary.
        mem.get_pressure_capture_quality_summary = MagicMock()
        mem.get_observability_stage_lock_audit = MagicMock()
        mem.get_system_lock_gate_posture = MagicMock()
        mem.get_cross_band_evidence_review_summary = MagicMock()

        out = mem.get_system_evidence_consumer_summary()

        assert out["summary_state"] == "SYSTEM_EVIDENCE_GATE_LIMITED"
        assert out["summary_reason"] == "SYSTEM_EVIDENCE_REVIEW_PARTIAL_UNDER_STAGE_LOCK"
        mem.get_pressure_capture_quality_summary.assert_not_called()
        mem.get_observability_stage_lock_audit.assert_not_called()
        mem.get_system_lock_gate_posture.assert_not_called()
        mem.get_cross_band_evidence_review_summary.assert_not_called()
