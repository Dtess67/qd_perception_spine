from unittest.mock import MagicMock

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


class TestUnifiedSystemConsumerPostureStageLock:
    def test_locked_when_unified_surface_is_canonical_and_read_only(self, tmp_path):
        ledger = tmp_path / "unified_stage_lock_locked.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_unified_system_consumer_posture_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "UNIFIED_SYSTEM_CONSUMER_POSTURE",
                "summary_state": "SYSTEM_CONSUMER_RELY",
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_unified_system_consumer_posture_stage_lock_audit()

        assert out["audit_available"] is True
        assert out["audit_mode"] == "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK"
        assert out["lock_state"] == "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCKED"
        assert out["reason"] == "ALL_CONSISTENCY_CHECKS_PASSED"
        assert out["checks_failed"] == 0
        assert out["checks_passed"] == out["checks_run"]
        assert out["lineage_mutation_performed"] is False
        assert out["event_creation_performed"] is False
        assert out["history_rewrite_performed"] is False

    def test_inconsistent_when_summary_state_is_non_canonical(self, tmp_path):
        ledger = tmp_path / "unified_stage_lock_non_canonical.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_unified_system_consumer_posture_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "UNIFIED_SYSTEM_CONSUMER_POSTURE",
                "summary_state": "SYSTEM_CONSUMER_UNKNOWN",
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_unified_system_consumer_posture_stage_lock_audit()

        assert out["audit_available"] is True
        assert out["lock_state"] == "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK_INCONSISTENT"
        assert out["reason"] == "CONSISTENCY_CHECK_FAILED"
        assert any(
            r["check_name"] == "UNIFIED_SUMMARY_STATE_CANONICAL" and r["passed"] is False
            for r in out["check_results"]
        )

    def test_inconsistent_when_unavailable_shape_is_not_fail_closed(self, tmp_path):
        ledger = tmp_path / "unified_stage_lock_unavailable_shape.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_unified_system_consumer_posture_summary = MagicMock(
            return_value={
                "summary_available": False,
                "summary_mode": "UNIFIED_SYSTEM_CONSUMER_POSTURE",
                "summary_state": "SYSTEM_CONSUMER_LIMITED",
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_unified_system_consumer_posture_stage_lock_audit()

        assert out["audit_available"] is True
        assert out["lock_state"] == "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK_INCONSISTENT"
        assert any(
            r["check_name"] == "UNAVAILABLE_FAIL_CLOSED_SHAPE" and r["passed"] is False
            for r in out["check_results"]
        )

    def test_inconsistent_when_guardrail_flags_not_false(self, tmp_path):
        ledger = tmp_path / "unified_stage_lock_guardrail_violation.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_unified_system_consumer_posture_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "UNIFIED_SYSTEM_CONSUMER_POSTURE",
                "summary_state": "SYSTEM_CONSUMER_RELY",
                "warnings": [],
                "lineage_mutation_performed": True,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_unified_system_consumer_posture_stage_lock_audit()

        assert out["lock_state"] == "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK_INCONSISTENT"
        assert any(
            r["check_name"] == "READ_ONLY_GUARDRAILS_FALSE" and r["passed"] is False
            for r in out["check_results"]
        )
        assert "GUARDRAIL_FLAG_VIOLATION" in out["warnings"]

    def test_unavailable_when_required_surface_missing(self, tmp_path):
        ledger = tmp_path / "unified_stage_lock_missing_surface.jsonl"
        ledger.write_text("")

        class MemWithoutUnifiedSummary(NeutralFamilyMemoryV1):
            def __getattribute__(self, name):
                if name == "get_unified_system_consumer_posture_summary":
                    raise AttributeError(name)
                return super().__getattribute__(name)

        mem = MemWithoutUnifiedSummary(durable_ledger_path=str(ledger))
        out = mem.get_unified_system_consumer_posture_stage_lock_audit()

        assert out["audit_available"] is False
        assert out["lock_state"] == "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK_UNAVAILABLE"
        assert out["reason"] == "REQUIRED_SURFACE_MISSING"

    def test_unavailable_when_required_surface_unusable(self, tmp_path):
        ledger = tmp_path / "unified_stage_lock_unusable_surface.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_unified_system_consumer_posture_summary = MagicMock(side_effect=RuntimeError("boom"))
        out = mem.get_unified_system_consumer_posture_stage_lock_audit()

        assert out["audit_available"] is False
        assert out["lock_state"] == "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK_UNAVAILABLE"
        assert out["reason"] == "REQUIRED_SURFACE_UNUSABLE"

    def test_no_hidden_lower_band_direct_call_dependency(self, tmp_path):
        ledger = tmp_path / "unified_stage_lock_no_hidden_dependency.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_unified_system_consumer_posture_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "UNIFIED_SYSTEM_CONSUMER_POSTURE",
                "summary_state": "SYSTEM_CONSUMER_RELY",
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        mem.get_system_evidence_consumer_summary = MagicMock()
        mem.get_system_lock_gate_posture = MagicMock()
        mem.get_system_evidence_review_summary = MagicMock()
        mem.get_system_evidence_review_stage_lock_audit = MagicMock()
        mem.get_system_evidence_review_consumer_gate = MagicMock()
        mem.get_cross_band_evidence_review_summary = MagicMock()
        mem.get_observability_stage_lock_audit = MagicMock()
        mem.get_pressure_capture_quality_summary = MagicMock()

        out = mem.get_unified_system_consumer_posture_stage_lock_audit()

        assert out["lock_state"] == "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCKED"
        mem.get_system_evidence_consumer_summary.assert_not_called()
        mem.get_system_lock_gate_posture.assert_not_called()
        mem.get_system_evidence_review_summary.assert_not_called()
        mem.get_system_evidence_review_stage_lock_audit.assert_not_called()
        mem.get_system_evidence_review_consumer_gate.assert_not_called()
        mem.get_cross_band_evidence_review_summary.assert_not_called()
        mem.get_observability_stage_lock_audit.assert_not_called()
        mem.get_pressure_capture_quality_summary.assert_not_called()
