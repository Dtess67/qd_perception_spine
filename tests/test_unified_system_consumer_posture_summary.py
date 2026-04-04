from unittest.mock import MagicMock

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


class TestUnifiedSystemConsumerPostureSummary:
    def test_rely_when_evidence_rely_and_lock_rely(self, tmp_path):
        ledger = tmp_path / "unified_consumer_rely.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_system_evidence_consumer_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "SYSTEM_EVIDENCE_CONSUMER_SUMMARY",
                "summary_state": "SYSTEM_EVIDENCE_GATE_RELY",
                "summary_reason": "SYSTEM_EVIDENCE_REVIEW_READY_AND_STAGE_LOCKED",
                "warnings": [],
            }
        )
        mem.get_system_lock_gate_posture = MagicMock(
            return_value={
                "gate_available": True,
                "gate_mode": "SYSTEM_LOCK_GATE_POSTURE",
                "gate_state": "SYSTEM_GATE_LOCKED",
                "gate_reason": "SYSTEM_STAGE_LOCKED",
                "warnings": [],
            }
        )

        out = mem.get_unified_system_consumer_posture_summary()

        assert out["summary_available"] is True
        assert out["summary_mode"] == "UNIFIED_SYSTEM_CONSUMER_POSTURE"
        assert out["summary_state"] == "SYSTEM_CONSUMER_RELY"
        assert out["summary_reason"] == "BOTH_SIDES_RELY_EQUIVALENT"

    def test_limited_when_evidence_limited_and_lock_rely(self, tmp_path):
        ledger = tmp_path / "unified_consumer_limited_evidence.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_system_evidence_consumer_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "SYSTEM_EVIDENCE_CONSUMER_SUMMARY",
                "summary_state": "SYSTEM_EVIDENCE_GATE_LIMITED",
                "summary_reason": "SYSTEM_EVIDENCE_REVIEW_PARTIAL_UNDER_STAGE_LOCK",
                "warnings": [],
            }
        )
        mem.get_system_lock_gate_posture = MagicMock(
            return_value={
                "gate_available": True,
                "gate_mode": "SYSTEM_LOCK_GATE_POSTURE",
                "gate_state": "SYSTEM_GATE_LOCKED",
                "gate_reason": "SYSTEM_STAGE_LOCKED",
                "warnings": [],
            }
        )

        out = mem.get_unified_system_consumer_posture_summary()

        assert out["summary_state"] == "SYSTEM_CONSUMER_LIMITED"
        assert out["summary_reason"] == "LIMITED_EQUIVALENT_INPUT_POSTURE"

    def test_limited_when_evidence_rely_and_lock_limited(self, tmp_path):
        ledger = tmp_path / "unified_consumer_limited_lock.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_system_evidence_consumer_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "SYSTEM_EVIDENCE_CONSUMER_SUMMARY",
                "summary_state": "SYSTEM_EVIDENCE_GATE_RELY",
                "summary_reason": "SYSTEM_EVIDENCE_REVIEW_READY_AND_STAGE_LOCKED",
                "warnings": [],
            }
        )
        mem.get_system_lock_gate_posture = MagicMock(
            return_value={
                "gate_available": True,
                "gate_mode": "SYSTEM_LOCK_GATE_POSTURE",
                "gate_state": "SYSTEM_GATE_LIMITED",
                "gate_reason": "SYSTEM_STAGE_LOCK_PARTIAL",
                "warnings": [],
            }
        )

        out = mem.get_unified_system_consumer_posture_summary()

        assert out["summary_state"] == "SYSTEM_CONSUMER_LIMITED"
        assert out["summary_reason"] == "LIMITED_EQUIVALENT_INPUT_POSTURE"

    def test_hold_when_any_side_hold_equivalent(self, tmp_path):
        ledger = tmp_path / "unified_consumer_hold.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_system_evidence_consumer_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "SYSTEM_EVIDENCE_CONSUMER_SUMMARY",
                "summary_state": "SYSTEM_EVIDENCE_GATE_HOLD",
                "summary_reason": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT",
                "warnings": [],
            }
        )
        mem.get_system_lock_gate_posture = MagicMock(
            return_value={
                "gate_available": True,
                "gate_mode": "SYSTEM_LOCK_GATE_POSTURE",
                "gate_state": "SYSTEM_GATE_LOCKED",
                "gate_reason": "SYSTEM_STAGE_LOCKED",
                "warnings": [],
            }
        )

        out = mem.get_unified_system_consumer_posture_summary()

        assert out["summary_state"] == "SYSTEM_CONSUMER_HOLD"
        assert out["summary_reason"] == "HOLD_EQUIVALENT_INPUT_POSTURE"

    def test_unavailable_when_required_surface_missing(self, tmp_path):
        ledger = tmp_path / "unified_consumer_unavailable_missing.jsonl"
        ledger.write_text("")

        class MemWithoutEvidenceSummary(NeutralFamilyMemoryV1):
            def __getattribute__(self, name):
                if name == "get_system_evidence_consumer_summary":
                    raise AttributeError(name)
                return super().__getattribute__(name)

        mem = MemWithoutEvidenceSummary(durable_ledger_path=str(ledger))
        out = mem.get_unified_system_consumer_posture_summary()

        assert out["summary_available"] is False
        assert out["summary_state"] == "SYSTEM_CONSUMER_UNAVAILABLE"
        assert out["summary_reason"] == "REQUIRED_SURFACE_MISSING"

    def test_no_hidden_lower_band_direct_call_dependency(self, tmp_path):
        ledger = tmp_path / "unified_consumer_no_hidden_dependency.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_system_evidence_consumer_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "SYSTEM_EVIDENCE_CONSUMER_SUMMARY",
                "summary_state": "SYSTEM_EVIDENCE_GATE_RELY",
                "summary_reason": "SYSTEM_EVIDENCE_REVIEW_READY_AND_STAGE_LOCKED",
                "warnings": [],
            }
        )
        mem.get_system_lock_gate_posture = MagicMock(
            return_value={
                "gate_available": True,
                "gate_mode": "SYSTEM_LOCK_GATE_POSTURE",
                "gate_state": "SYSTEM_GATE_LOCKED",
                "gate_reason": "SYSTEM_STAGE_LOCKED",
                "warnings": [],
            }
        )

        # Lower-band surfaces must not be called by unified summary.
        mem.get_system_evidence_review_summary = MagicMock()
        mem.get_system_evidence_review_stage_lock_audit = MagicMock()
        mem.get_cross_band_evidence_review_summary = MagicMock()
        mem.get_observability_stage_lock_audit = MagicMock()
        mem.get_pressure_capture_quality_summary = MagicMock()

        out = mem.get_unified_system_consumer_posture_summary()

        assert out["summary_state"] == "SYSTEM_CONSUMER_RELY"
        mem.get_system_evidence_review_summary.assert_not_called()
        mem.get_system_evidence_review_stage_lock_audit.assert_not_called()
        mem.get_cross_band_evidence_review_summary.assert_not_called()
        mem.get_observability_stage_lock_audit.assert_not_called()
        mem.get_pressure_capture_quality_summary.assert_not_called()
