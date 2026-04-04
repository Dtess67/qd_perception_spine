
import pytest
import os
import json
from unittest.mock import MagicMock
from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

class TestSystemLockGatePosture:
    def test_gate_locked_when_umbrella_locked(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        # Mock the umbrella audit
        mock_audit = {
            "audit_available": True,
            "lock_state": "SYSTEM_STAGE_LOCKED",
            "reason": "ALL_SUB_AUDITS_LOCKED",
            "warnings": [],
            "explanation_lines": ["All bands locked."],
        }
        mem.get_system_stage_lock_audit = MagicMock(return_value=mock_audit)
        
        result = mem.get_system_lock_gate_posture()
        
        assert result["gate_state"] == "SYSTEM_GATE_LOCKED"
        assert result["gate_reason"] == "SYSTEM_STAGE_LOCKED"
        assert result["system_stage_lock"] == mock_audit
        assert result["gate_available"] is True
        assert result["gate_mode"] == "SYSTEM_LOCK_GATE_POSTURE"
        # Single-call discipline
        mem.get_system_stage_lock_audit.assert_called_once()

    def test_gate_inconsistent_when_umbrella_inconsistent(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        mock_audit = {
            "audit_available": True,
            "lock_state": "SYSTEM_STAGE_LOCK_INCONSISTENT",
            "reason": "CONSISTENCY_CHECK_FAILED",
            "warnings": ["INCONSISTENT_WARN"],
            "explanation_lines": ["Failed checks: X"],
        }
        mem.get_system_stage_lock_audit = MagicMock(return_value=mock_audit)
        
        result = mem.get_system_lock_gate_posture()
        
        assert result["gate_state"] == "SYSTEM_GATE_INCONSISTENT"
        assert result["gate_reason"] == "SYSTEM_STAGE_LOCK_INCONSISTENT"
        assert result["system_stage_lock"] == mock_audit
        assert "INCONSISTENT_WARN" in result["warnings"]

    def test_gate_unavailable_when_umbrella_unavailable(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        mock_audit = {
            "audit_available": True,
            "lock_state": "SYSTEM_STAGE_LOCK_UNAVAILABLE",
            "reason": "SUB_AUDIT_NOT_LOCKED",
            "warnings": [],
            "explanation_lines": ["Band X unavailable"],
        }
        mem.get_system_stage_lock_audit = MagicMock(return_value=mock_audit)
        
        result = mem.get_system_lock_gate_posture()
        
        assert result["gate_state"] == "SYSTEM_GATE_UNAVAILABLE"
        assert result["gate_reason"] == "SYSTEM_STAGE_LOCK_UNAVAILABLE"

    def test_gate_unavailable_when_umbrella_audit_unusable(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        # Umbrella audit reports not available
        mock_audit = {
            "audit_available": False,
            "lock_state": "SYSTEM_STAGE_LOCK_UNAVAILABLE",
            "reason": "REQUIRED_SUB_AUDIT_API_MISSING",
            "explanation_lines": ["API missing"],
        }
        mem.get_system_stage_lock_audit = MagicMock(return_value=mock_audit)
        
        result = mem.get_system_lock_gate_posture()
        
        assert result["gate_state"] == "SYSTEM_GATE_UNAVAILABLE"
        assert result["gate_reason"] == "SYSTEM_STAGE_LOCK_AUDIT_UNAVAILABLE"

    def test_gate_unavailable_on_unexpected_lock_state(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        # Unexpected lock_state
        mock_audit = {
            "audit_available": True,
            "lock_state": "UNKNOWN_FUTURE_STATE",
            "reason": "SOME_REASON",
            "explanation_lines": [],
        }
        mem.get_system_stage_lock_audit = MagicMock(return_value=mock_audit)
        
        result = mem.get_system_lock_gate_posture()
        
        assert result["gate_state"] == "SYSTEM_GATE_UNAVAILABLE"
        assert result["gate_reason"] == "SYSTEM_STAGE_LOCK_AUDIT_UNUSABLE"

    def test_no_lower_band_direct_calls(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        mem.get_observability_stage_lock_audit = MagicMock()
        mem.get_cross_band_stage_lock_audit = MagicMock()
        # We need to mock get_system_stage_lock_audit because it calls lower bands
        mem.get_system_stage_lock_audit = MagicMock(return_value={"audit_available": True})
        
        mem.get_system_lock_gate_posture()
        
        mem.get_observability_stage_lock_audit.assert_not_called()
        mem.get_cross_band_stage_lock_audit.assert_not_called()

    def test_read_only_and_no_mutation_flags(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        result = mem.get_system_lock_gate_posture()
        
        assert result["lineage_mutation_performed"] is False
        assert result["event_creation_performed"] is False
        assert result["history_rewrite_performed"] is False
        
        # Ensure no forbidden fields
        forbidden = ["rollout_permitted", "safe_to_proceed", "proceed", "recommended_action", "block_deploy", "action_required"]
        for field in forbidden:
            assert field not in result
            for line in result["explanation_lines"]:
                assert field not in line.lower()

    def test_explanation_lines_honesty(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        mock_audit = {
            "audit_available": True,
            "lock_state": "SYSTEM_STAGE_LOCKED",
            "explanation_lines": ["Original audit line"],
        }
        mem.get_system_stage_lock_audit = MagicMock(return_value=mock_audit)
        
        result = mem.get_system_lock_gate_posture()
        
        # Should preserve original lines and add its own
        assert any("Gate posture: SYSTEM_GATE_LOCKED" in line for line in result["explanation_lines"])
        assert "Original audit line" in result["explanation_lines"]
