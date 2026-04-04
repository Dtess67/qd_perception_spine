
import pytest
import os
import json
from unittest.mock import MagicMock
from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

class TestCrossBandEvidenceReview:
    def test_review_ready_on_healthy_locked_surface(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        # Mock window summary (evidence exists)
        mock_window = {
            "summary_available": True,
            "auditable_event_count": 5,
            "total_transition_events": 5,
            "window_event_count": 5,
            "self_check_state_counts": {
                "CROSS_BAND_ALIGNMENT_OBSERVED": 5,
                "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                "CROSS_BAND_PARTIAL": 0,
                "CROSS_BAND_UNAVAILABLE": 0,
            },
            "contradiction_flag_counts": {},
            "event_type_counts": {"FAMILY_FISSION": 5},
            "explanation_lines": ["Healthy surface"],
            "warnings": []
        }
        mem.get_cross_band_self_check_summary_window = MagicMock(return_value=mock_window)
        
        # Mock stage lock (locked)
        mock_lock = {
            "lock_state": "CROSS_BAND_STAGE_LOCKED",
            "contract_surface": {"comparator_api_present": True},
            "warnings": []
        }
        mem.get_cross_band_stage_lock_audit = MagicMock(return_value=mock_lock)
        
        result = mem.get_cross_band_evidence_review_summary()
        
        assert result["review_state"] == "CROSS_BAND_EVIDENCE_REVIEW_READY"
        assert result["review_reason"] == "CROSS_BAND_STAGE_LOCKED_WITH_RELEVANT_SURFACE"
        assert result["evidence_counts"]["CROSS_BAND_ALIGNMENT_OBSERVED"] == 5
        assert result["review_available"] is True
        assert result["review_mode"] == "CROSS_BAND_EVIDENCE_REVIEW"

    def test_review_partial_when_coverage_is_limited(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        # Mock window summary (mixed evidence)
        mock_window = {
            "summary_available": True,
            "auditable_event_count": 2,
            "self_check_state_counts": {
                "CROSS_BAND_ALIGNMENT_OBSERVED": 1,
                "CROSS_BAND_CONTRADICTION_OBSERVED": 1,
                "CROSS_BAND_PARTIAL": 0,
                "CROSS_BAND_UNAVAILABLE": 0,
            },
            "explanation_lines": ["Mixed surface"]
        }
        mem.get_cross_band_self_check_summary_window = MagicMock(return_value=mock_window)
        
        # Mock stage lock (inconsistent)
        mock_lock = {
            "lock_state": "CROSS_BAND_STAGE_LOCK_INCONSISTENT",
            "contract_surface": {}
        }
        mem.get_cross_band_stage_lock_audit = MagicMock(return_value=mock_lock)
        
        result = mem.get_cross_band_evidence_review_summary()
        
        assert result["review_state"] == "CROSS_BAND_EVIDENCE_REVIEW_PARTIAL"
        assert result["review_reason"] == "LIMITED_OR_MIXED_EVIDENCE_SURFACE"

    def test_review_unavailable_when_surfaces_missing_or_empty(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        # Mock window summary (not available)
        mock_window = {
            "summary_available": False,
            "auditable_event_count": 0,
            "self_check_state_counts": {
                "CROSS_BAND_ALIGNMENT_OBSERVED": 0,
                "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                "CROSS_BAND_PARTIAL": 0,
                "CROSS_BAND_UNAVAILABLE": 0,
            }
        }
        mem.get_cross_band_self_check_summary_window = MagicMock(return_value=mock_window)
        
        # Mock stage lock (unavailable)
        mock_lock = {
            "lock_state": "CROSS_BAND_STAGE_LOCK_UNAVAILABLE"
        }
        mem.get_cross_band_stage_lock_audit = MagicMock(return_value=mock_lock)
        
        result = mem.get_cross_band_evidence_review_summary()
        
        assert result["review_state"] == "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE"
        assert result["review_reason"] == "EVIDENCE_SURFACE_INSUFFICIENT_OR_MISSING"

    def test_exact_preservation_of_self_check_state_bucket_names(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        result = mem.get_cross_band_evidence_review_summary()
        
        expected_buckets = [
            "CROSS_BAND_ALIGNMENT_OBSERVED",
            "CROSS_BAND_CONTRADICTION_OBSERVED",
            "CROSS_BAND_PARTIAL",
            "CROSS_BAND_UNAVAILABLE",
        ]
        for bucket in expected_buckets:
            assert bucket in result["evidence_counts"]

    def test_read_only_and_no_mutation_flags(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        result = mem.get_cross_band_evidence_review_summary()
        
        assert result["lineage_mutation_performed"] is False
        assert result["event_creation_performed"] is False
        assert result["history_rewrite_performed"] is False
        
        # Ensure no forbidden fields
        forbidden = ["rollout_permitted", "safe_to_proceed", "proceed", "recommended_action", "block_deploy", "action_required", "should"]
        for field in forbidden:
            assert field not in result
            for line in result["explanation_lines"]:
                assert field not in line.lower()

    def test_composition_honesty(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        
        mock_window = {
            "summary_available": True,
            "auditable_event_count": 0,
            "explanation_lines": ["Thin evidence"]
        }
        mem.get_cross_band_self_check_summary_window = MagicMock(return_value=mock_window)
        
        result = mem.get_cross_band_evidence_review_summary()
        
        assert any("Evidence surface is thin" in line for line in result["explanation_lines"])
        assert result["review_state"] == "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE"
