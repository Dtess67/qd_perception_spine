from unittest.mock import MagicMock

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


class TestUnifiedSystemConsumerSummary:
    def test_happy_path_packages_unified_posture_and_stage_lock(self, tmp_path):
        ledger = tmp_path / "unified_consumer_summary_happy.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_unified_system_consumer_posture_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "UNIFIED_SYSTEM_CONSUMER_POSTURE",
                "summary_state": "SYSTEM_CONSUMER_LIMITED",
                "summary_reason": "LIMITED_EQUIVALENT_INPUT_POSTURE",
                "warnings": ["UP_WARN"],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_unified_system_consumer_posture_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK",
                "lock_state": "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCKED",
                "reason": "ALL_CONSISTENCY_CHECKS_PASSED",
                "warnings": ["SL_WARN"],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_unified_system_consumer_summary()

        assert out["summary_available"] is True
        assert out["summary_mode"] == "UNIFIED_SYSTEM_CONSUMER_SUMMARY"
        assert out["summary_state"] == "SYSTEM_CONSUMER_LIMITED"
        assert out["summary_reason"] == "LIMITED_EQUIVALENT_INPUT_POSTURE"
        assert out["packaged_consumer_posture"]["unified_posture_state"] == "SYSTEM_CONSUMER_LIMITED"
        assert (
            out["packaged_consumer_posture"]["unified_stage_lock_state"]
            == "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCKED"
        )
        assert "UP_WARN" in out["warnings"]
        assert "SL_WARN" in out["warnings"]

    def test_unavailable_when_unified_posture_surface_missing(self, tmp_path):
        ledger = tmp_path / "unified_consumer_summary_posture_missing.jsonl"
        ledger.write_text("")

        class MemWithoutUnifiedPosture(NeutralFamilyMemoryV1):
            def __getattribute__(self, name):
                if name == "get_unified_system_consumer_posture_summary":
                    raise AttributeError(name)
                return super().__getattribute__(name)

        mem = MemWithoutUnifiedPosture(durable_ledger_path=str(ledger))
        out = mem.get_unified_system_consumer_summary()

        assert out["summary_available"] is False
        assert out["summary_state"] == "SYSTEM_CONSUMER_UNAVAILABLE"
        assert out["summary_reason"] == "REQUIRED_SURFACE_MISSING"

    def test_unavailable_when_unified_stage_lock_surface_missing(self, tmp_path):
        ledger = tmp_path / "unified_consumer_summary_stage_lock_missing.jsonl"
        ledger.write_text("")

        class MemWithoutUnifiedStageLock(NeutralFamilyMemoryV1):
            def __getattribute__(self, name):
                if name == "get_unified_system_consumer_posture_stage_lock_audit":
                    raise AttributeError(name)
                return super().__getattribute__(name)

        mem = MemWithoutUnifiedStageLock(durable_ledger_path=str(ledger))
        out = mem.get_unified_system_consumer_summary()

        assert out["summary_available"] is False
        assert out["summary_state"] == "SYSTEM_CONSUMER_UNAVAILABLE"
        assert out["summary_reason"] == "REQUIRED_SURFACE_MISSING"

    def test_no_hidden_lower_band_direct_call_dependency(self, tmp_path):
        ledger = tmp_path / "unified_consumer_summary_no_hidden_dependency.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_unified_system_consumer_posture_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "UNIFIED_SYSTEM_CONSUMER_POSTURE",
                "summary_state": "SYSTEM_CONSUMER_RELY",
                "summary_reason": "BOTH_SIDES_RELY_EQUIVALENT",
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_unified_system_consumer_posture_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK",
                "lock_state": "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCKED",
                "reason": "ALL_CONSISTENCY_CHECKS_PASSED",
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

        out = mem.get_unified_system_consumer_summary()

        assert out["summary_state"] == "SYSTEM_CONSUMER_RELY"
        mem.get_system_evidence_consumer_summary.assert_not_called()
        mem.get_system_lock_gate_posture.assert_not_called()
        mem.get_system_evidence_review_summary.assert_not_called()
        mem.get_system_evidence_review_stage_lock_audit.assert_not_called()
        mem.get_system_evidence_review_consumer_gate.assert_not_called()
        mem.get_cross_band_evidence_review_summary.assert_not_called()
        mem.get_observability_stage_lock_audit.assert_not_called()
        mem.get_pressure_capture_quality_summary.assert_not_called()

    def test_guardrail_flags_remain_false(self, tmp_path):
        ledger = tmp_path / "unified_consumer_summary_guardrails.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_unified_system_consumer_posture_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "UNIFIED_SYSTEM_CONSUMER_POSTURE",
                "summary_state": "SYSTEM_CONSUMER_HOLD",
                "summary_reason": "HOLD_EQUIVALENT_INPUT_POSTURE",
                "warnings": [],
                "lineage_mutation_performed": True,
                "event_creation_performed": True,
                "history_rewrite_performed": True,
            }
        )
        mem.get_unified_system_consumer_posture_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK",
                "lock_state": "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK_INCONSISTENT",
                "reason": "CONSISTENCY_CHECK_FAILED",
                "warnings": [],
                "lineage_mutation_performed": True,
                "event_creation_performed": True,
                "history_rewrite_performed": True,
            }
        )

        out = mem.get_unified_system_consumer_summary()

        assert out["lineage_mutation_performed"] is False
        assert out["event_creation_performed"] is False
        assert out["history_rewrite_performed"] is False
