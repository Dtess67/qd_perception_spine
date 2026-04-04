from unittest.mock import MagicMock

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _find_check(out: dict, name: str) -> dict:
    for chk in out.get("check_results", []):
        if chk.get("check_name") == name:
            return chk
    return {}


class TestObservabilityEvidenceReviewStageLock:
    def test_locked_happy_path(self, tmp_path):
        ledger = tmp_path / "obs_review_stage_lock_locked.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        quality = {
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
            "warnings": [],
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }
        stage = {
            "audit_available": True,
            "audit_mode": "OBSERVABILITY_STAGE_LOCK",
            "lock_state": "OBSERVABILITY_STAGE_LOCKED",
            "reason": "ALL_REQUIRED_CHECKS_PASSED",
            "warnings": [],
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }
        review = {
            "review_available": True,
            "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW",
            "review_state": "OBSERVABILITY_EVIDENCE_REVIEW_READY",
            "review_reason": "LOCKED_WITH_FULLY_AUDITABLE_OBSERVABILITY_EVIDENCE",
            "supporting_surfaces": {
                "observability_pressure_capture_quality_summary": quality,
                "observability_stage_lock_audit": stage,
            },
            "evidence_scope": {
                "stage_lock_state": "OBSERVABILITY_STAGE_LOCKED",
                "stage_lock_reason": "ALL_REQUIRED_CHECKS_PASSED",
            },
            "evidence_counts": {
                "total_transition_events": 3,
                "total_auditable_events": 3,
                "pressure_snapshot_present_count": 3,
                "pressure_snapshot_missing_count": 0,
                "audit_state_counts": quality["audit_state_counts"],
                "capture_reason_counts": quality["capture_reason_counts"],
                "recoverability_counts": quality["recoverability_counts"],
                "event_type_counts": quality["event_type_counts"],
            },
            "warnings": [],
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

        mem.get_observability_evidence_review_summary = MagicMock(return_value=review)
        mem.get_pressure_capture_quality_summary = MagicMock(return_value=quality)
        mem.get_observability_stage_lock_audit = MagicMock(return_value=stage)

        out = mem.get_observability_evidence_review_stage_lock_audit()

        assert out["audit_available"] is True
        assert out["audit_mode"] == "OBSERVABILITY_EVIDENCE_REVIEW_STAGE_LOCK"
        assert out["lock_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_STAGE_LOCKED"
        assert out["reason"] == "ALL_CONSISTENCY_CHECKS_PASSED"
        assert all(chk.get("passed") is True for chk in out["check_results"])

    def test_unavailable_when_observability_evidence_review_surface_missing(self, tmp_path):
        ledger = tmp_path / "obs_review_stage_lock_missing_review_surface.jsonl"
        ledger.write_text("")

        class MemWithoutReview(NeutralFamilyMemoryV1):
            def __getattribute__(self, name):
                if name == "get_observability_evidence_review_summary":
                    raise AttributeError(name)
                return super().__getattribute__(name)

        mem = MemWithoutReview(durable_ledger_path=str(ledger))
        out = mem.get_observability_evidence_review_stage_lock_audit()

        assert out["audit_available"] is False
        assert out["lock_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE"
        assert out["reason"] == "REQUIRED_SURFACE_MISSING"

    def test_unavailable_when_allowed_required_source_surface_missing(self, tmp_path):
        ledger = tmp_path / "obs_review_stage_lock_missing_allowed_source.jsonl"
        ledger.write_text("")

        class MemWithoutQuality(NeutralFamilyMemoryV1):
            def __getattribute__(self, name):
                if name == "get_pressure_capture_quality_summary":
                    raise AttributeError(name)
                return super().__getattribute__(name)

        mem = MemWithoutQuality(durable_ledger_path=str(ledger))
        out = mem.get_observability_evidence_review_stage_lock_audit()

        assert out["audit_available"] is False
        assert out["lock_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE"
        assert out["reason"] == "REQUIRED_SURFACE_MISSING"

    def test_inconsistent_when_review_contract_drifts_from_allowed_sources(self, tmp_path):
        ledger = tmp_path / "obs_review_stage_lock_drift.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_pressure_capture_quality_summary = MagicMock(
            return_value={
                "summary_available": True,
                "summary_mode": "LEDGER_READ_ONLY",
                "reason": "OK",
                "total_transition_events": 2,
                "auditable_event_count": 2,
                "pressure_snapshot_present_count": 2,
                "pressure_snapshot_missing_count": 0,
                "audit_state_counts": {
                    "PRESSURE_CAPTURE_AUDIT_VALID": 2,
                    "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                    "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                },
                "capture_reason_counts": {
                    "PRESSURE_CAPTURE_FULL": 2,
                    "PRESSURE_CAPTURE_PARTIAL": 0,
                    "PRESSURE_CAPTURE_FAILED": 0,
                    "UNRECOGNIZED_CAPTURE_REASON": 0,
                },
                "recoverability_counts": {
                    "FULLY_RECOVERABLE": 2,
                    "PARTIALLY_RECOVERABLE": 0,
                    "UNRECOVERABLE": 0,
                },
                "event_type_counts": {"FAMILY_REUNION": 2},
                "warnings": [],
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
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        # Drifted state/reason against allowed-source-derived mapping.
        mem.get_observability_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW",
                "review_state": "OBSERVABILITY_EVIDENCE_REVIEW_PARTIAL",
                "review_reason": "LIMITED_OR_MIXED_OBSERVABILITY_EVIDENCE",
                "supporting_surfaces": {},
                "evidence_scope": {"stage_lock_state": "OBSERVABILITY_STAGE_LOCKED"},
                "evidence_counts": {
                    "total_transition_events": 2,
                    "total_auditable_events": 2,
                    "pressure_snapshot_present_count": 2,
                    "pressure_snapshot_missing_count": 0,
                    "audit_state_counts": {
                        "PRESSURE_CAPTURE_AUDIT_VALID": 2,
                        "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                    },
                    "capture_reason_counts": {
                        "PRESSURE_CAPTURE_FULL": 2,
                        "PRESSURE_CAPTURE_PARTIAL": 0,
                        "PRESSURE_CAPTURE_FAILED": 0,
                        "UNRECOGNIZED_CAPTURE_REASON": 0,
                    },
                    "recoverability_counts": {
                        "FULLY_RECOVERABLE": 2,
                        "PARTIALLY_RECOVERABLE": 0,
                        "UNRECOVERABLE": 0,
                    },
                    "event_type_counts": {"FAMILY_REUNION": 2},
                },
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        out = mem.get_observability_evidence_review_stage_lock_audit()

        assert out["audit_available"] is True
        assert out["lock_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT"
        chk = _find_check(out, "REVIEW_STATE_REASON_MATCH_ALLOWED_MAPPING")
        assert chk.get("passed") is False

    def test_no_hidden_non_summary_lower_band_dependency(self, tmp_path):
        ledger = tmp_path / "obs_review_stage_lock_no_hidden_dependency.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_observability_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW",
                "review_state": "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE",
                "review_reason": "OBSERVABILITY_EVIDENCE_SURFACE_INSUFFICIENT_OR_MISSING",
                "supporting_surfaces": {},
                "evidence_scope": {"stage_lock_state": "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE"},
                "evidence_counts": {
                    "total_transition_events": 0,
                    "total_auditable_events": 0,
                    "pressure_snapshot_present_count": 0,
                    "pressure_snapshot_missing_count": 0,
                    "audit_state_counts": {
                        "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                    },
                    "capture_reason_counts": {
                        "PRESSURE_CAPTURE_FULL": 0,
                        "PRESSURE_CAPTURE_PARTIAL": 0,
                        "PRESSURE_CAPTURE_FAILED": 0,
                        "UNRECOGNIZED_CAPTURE_REASON": 0,
                    },
                    "recoverability_counts": {
                        "FULLY_RECOVERABLE": 0,
                        "PARTIALLY_RECOVERABLE": 0,
                        "UNRECOVERABLE": 0,
                    },
                    "event_type_counts": {},
                },
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_pressure_capture_quality_summary = MagicMock(
            return_value={
                "summary_available": False,
                "summary_mode": "LEDGER_READ_ONLY",
                "reason": "NO_TRANSITION_EVENTS",
                "total_transition_events": 0,
                "auditable_event_count": 0,
                "pressure_snapshot_present_count": 0,
                "pressure_snapshot_missing_count": 0,
                "audit_state_counts": {
                    "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                    "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                    "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                },
                "capture_reason_counts": {
                    "PRESSURE_CAPTURE_FULL": 0,
                    "PRESSURE_CAPTURE_PARTIAL": 0,
                    "PRESSURE_CAPTURE_FAILED": 0,
                    "UNRECOGNIZED_CAPTURE_REASON": 0,
                },
                "recoverability_counts": {
                    "FULLY_RECOVERABLE": 0,
                    "PARTIALLY_RECOVERABLE": 0,
                    "UNRECOVERABLE": 0,
                },
                "event_type_counts": {},
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_observability_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "OBSERVABILITY_STAGE_LOCK",
                "lock_state": "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE",
                "reason": "REQUIRED_SURFACE_MISSING",
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        mem.get_transition_pressure_capture_audit = MagicMock()
        mem.get_pressure_capture_quality_summary_window = MagicMock()
        mem.get_pressure_capture_quality_summary_event_order_window = MagicMock()
        mem.get_pressure_capture_quality_window_comparator = MagicMock()
        mem.get_cross_band_evidence_review_summary = MagicMock()
        mem.get_system_lock_gate_posture = MagicMock()

        out = mem.get_observability_evidence_review_stage_lock_audit()

        assert out["lock_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_STAGE_LOCKED"
        mem.get_transition_pressure_capture_audit.assert_not_called()
        mem.get_pressure_capture_quality_summary_window.assert_not_called()
        mem.get_pressure_capture_quality_summary_event_order_window.assert_not_called()
        mem.get_pressure_capture_quality_window_comparator.assert_not_called()
        mem.get_cross_band_evidence_review_summary.assert_not_called()
        mem.get_system_lock_gate_posture.assert_not_called()

    def test_guardrail_flags_remain_false(self, tmp_path):
        ledger = tmp_path / "obs_review_stage_lock_guardrails.jsonl"
        ledger.write_text("")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_observability_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW",
                "review_state": "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE",
                "review_reason": "OBSERVABILITY_EVIDENCE_SURFACE_INSUFFICIENT_OR_MISSING",
                "supporting_surfaces": {},
                "evidence_scope": {"stage_lock_state": "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE"},
                "evidence_counts": {
                    "total_transition_events": 0,
                    "total_auditable_events": 0,
                    "pressure_snapshot_present_count": 0,
                    "pressure_snapshot_missing_count": 0,
                    "audit_state_counts": {
                        "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                    },
                    "capture_reason_counts": {
                        "PRESSURE_CAPTURE_FULL": 0,
                        "PRESSURE_CAPTURE_PARTIAL": 0,
                        "PRESSURE_CAPTURE_FAILED": 0,
                        "UNRECOGNIZED_CAPTURE_REASON": 0,
                    },
                    "recoverability_counts": {
                        "FULLY_RECOVERABLE": 0,
                        "PARTIALLY_RECOVERABLE": 0,
                        "UNRECOVERABLE": 0,
                    },
                    "event_type_counts": {},
                },
                "warnings": [],
                "lineage_mutation_performed": True,
                "event_creation_performed": True,
                "history_rewrite_performed": True,
            }
        )
        mem.get_pressure_capture_quality_summary = MagicMock(
            return_value={
                "summary_available": False,
                "summary_mode": "LEDGER_READ_ONLY",
                "reason": "NO_TRANSITION_EVENTS",
                "total_transition_events": 0,
                "auditable_event_count": 0,
                "pressure_snapshot_present_count": 0,
                "pressure_snapshot_missing_count": 0,
                "audit_state_counts": {
                    "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                    "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                    "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                },
                "capture_reason_counts": {
                    "PRESSURE_CAPTURE_FULL": 0,
                    "PRESSURE_CAPTURE_PARTIAL": 0,
                    "PRESSURE_CAPTURE_FAILED": 0,
                    "UNRECOGNIZED_CAPTURE_REASON": 0,
                },
                "recoverability_counts": {
                    "FULLY_RECOVERABLE": 0,
                    "PARTIALLY_RECOVERABLE": 0,
                    "UNRECOVERABLE": 0,
                },
                "event_type_counts": {},
                "warnings": [],
                "lineage_mutation_performed": True,
                "event_creation_performed": True,
                "history_rewrite_performed": True,
            }
        )
        mem.get_observability_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "OBSERVABILITY_STAGE_LOCK",
                "lock_state": "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE",
                "reason": "REQUIRED_SURFACE_MISSING",
                "warnings": [],
                "lineage_mutation_performed": True,
                "event_creation_performed": True,
                "history_rewrite_performed": True,
            }
        )

        out = mem.get_observability_evidence_review_stage_lock_audit()

        assert out["audit_available"] is True
        assert out["lock_state"] == "OBSERVABILITY_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT"
        assert out["lineage_mutation_performed"] is False
        assert out["event_creation_performed"] is False
        assert out["history_rewrite_performed"] is False
        chk = _find_check(out, "READ_ONLY_GUARDRAILS_FALSE")
        assert chk.get("passed") is False
