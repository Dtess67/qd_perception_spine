import json
from pathlib import Path
from unittest.mock import MagicMock

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _write_event(path: Path, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def _pressure_payload(family_ids: list[str], state: str) -> dict:
    return {
        "family_ids": list(family_ids),
        "family_pressure_by_id": {
            fam_id: {
                "family_id": fam_id,
                "pressure_state": state,
                "forecast_available": True,
                "scorecard": {"diagnostic_scale": "0_to_1_comparative_not_probability"},
            }
            for fam_id in family_ids
        },
    }


def _seed_green_ledger(path: Path) -> None:
    _write_event(
        path,
        {
            "event_id": "sys_er_lock_01",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 1,
            "source_family_ids": ["fa"],
            "successor_family_ids": ["fb", "fc"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fa"], "PRESSURE_FISSION_PRONE"),
                "post_event_pressure": _pressure_payload(["fb", "fc"], "PRESSURE_STABLE"),
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "sys_er_lock_02",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 2,
            "source_family_ids": ["fb", "fc"],
            "successor_family_ids": ["fd"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fb", "fc"], "PRESSURE_STRETCHED"),
                "post_event_pressure": _pressure_payload(["fd"], "PRESSURE_STABLE"),
            },
        },
    )


def _check(out: dict, name: str) -> dict:
    for c in out.get("check_results", []):
        if c.get("check_name") == name:
            return c
    return {}


class TestSystemEvidenceReviewStageLock:
    def test_stage_lock_passes_on_corrected_v1_1_posture(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_stage_lock_green.jsonl"
        _seed_green_ledger(ledger)
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        out = mem.get_system_evidence_review_stage_lock_audit()

        assert out["audit_available"] is True
        assert out["audit_mode"] == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK"
        assert out["lock_state"] == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCKED"
        assert out["reason"] == "ALL_CONSISTENCY_CHECKS_PASSED"
        assert out["checks_failed"] == 0

    def test_stage_lock_inconsistent_when_ready_without_observability_review(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_stage_lock_drift_ready.jsonl"
        ledger.write_text("", encoding="utf-8")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_cross_band_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "CROSS_BAND_EVIDENCE_REVIEW",
                "review_state": "CROSS_BAND_EVIDENCE_REVIEW_READY",
                "evidence_scope": {"total_auditable_events": 3},
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )
        mem.get_system_lock_gate_posture = MagicMock(
            return_value={
                "gate_available": True,
                "gate_mode": "SYSTEM_LOCK_GATE_POSTURE",
                "gate_state": "SYSTEM_GATE_LOCKED",
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }
        )

        def _drifted_summary():
            return {
                "review_available": True,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_READY",
                "review_reason": "COMPOSED_EVIDENCE_SURFACES_READY",
                "supporting_surfaces": {
                    "observability_evidence_review_summary": None,
                },
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        mem.get_system_evidence_review_summary = _drifted_summary

        out = mem.get_system_evidence_review_stage_lock_audit()

        assert out["lock_state"] == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT"
        chk = _check(out, "READY_REQUIRES_OBSERVABILITY_EVIDENCE_REVIEW")
        assert chk.get("passed") is False

    def test_stage_lock_detects_gate_predicate_drift(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_stage_lock_gate_drift.jsonl"
        ledger.write_text("", encoding="utf-8")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        state = {"gate": "SYSTEM_GATE_LOCKED"}

        def _gate():
            return {
                "gate_available": True,
                "gate_mode": "SYSTEM_LOCK_GATE_POSTURE",
                "gate_state": state["gate"],
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        def _cross():
            return {
                "review_available": True,
                "review_mode": "CROSS_BAND_EVIDENCE_REVIEW",
                "review_state": "CROSS_BAND_EVIDENCE_REVIEW_PARTIAL",
                "evidence_scope": {"total_auditable_events": 1},
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        def _drifted_summary():
            g = mem.get_system_lock_gate_posture()
            if g["gate_state"] == "SYSTEM_GATE_LOCKED":
                reason = "GATE_LOCKED_PATH"
            else:
                reason = "GATE_UNAVAILABLE_PATH"
            return {
                "review_available": True,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_PARTIAL",
                "review_reason": reason,
                "supporting_surfaces": {
                    "observability_evidence_review_summary": None,
                },
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        mem.get_system_lock_gate_posture = _gate
        mem.get_cross_band_evidence_review_summary = _cross
        mem.get_system_evidence_review_summary = _drifted_summary

        out = mem.get_system_evidence_review_stage_lock_audit()

        assert out["lock_state"] == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT"
        chk = _check(out, "SYSTEM_GATE_CONTEXT_NON_PREDICATE")
        assert chk.get("passed") is False

    def test_stage_lock_detects_quality_predicate_drift(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_stage_lock_quality_drift.jsonl"
        ledger.write_text("", encoding="utf-8")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        quality = {"count": 1}

        def _quality():
            return {
                "summary_available": True,
                "auditable_event_count": quality["count"],
                "audit_state_counts": {
                    "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                    "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                    "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                },
                "recoverability_counts": {
                    "FULLY_RECOVERABLE": 0,
                    "PARTIALLY_RECOVERABLE": 0,
                    "UNRECOVERABLE": 0,
                },
                "warnings": [],
            }

        def _gate():
            return {
                "gate_available": True,
                "gate_mode": "SYSTEM_LOCK_GATE_POSTURE",
                "gate_state": "SYSTEM_GATE_LOCKED",
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        def _cross():
            return {
                "review_available": True,
                "review_mode": "CROSS_BAND_EVIDENCE_REVIEW",
                "review_state": "CROSS_BAND_EVIDENCE_REVIEW_PARTIAL",
                "evidence_scope": {"total_auditable_events": 1},
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        def _drifted_summary():
            q = mem.get_pressure_capture_quality_summary()
            if int(q.get("auditable_event_count", 0)) > 0:
                state = "SYSTEM_EVIDENCE_REVIEW_PARTIAL"
                reason = "QUALITY_NONZERO_PATH"
            else:
                state = "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"
                reason = "QUALITY_ZERO_PATH"
            return {
                "review_available": True,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW",
                "review_state": state,
                "review_reason": reason,
                "supporting_surfaces": {
                    "observability_evidence_review_summary": None,
                },
                "warnings": [],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        mem.get_pressure_capture_quality_summary = _quality
        mem.get_system_lock_gate_posture = _gate
        mem.get_cross_band_evidence_review_summary = _cross
        mem.get_system_evidence_review_summary = _drifted_summary

        out = mem.get_system_evidence_review_stage_lock_audit()

        assert out["lock_state"] == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT"
        chk = _check(out, "OBSERVABILITY_QUALITY_CONTEXT_NON_SUBSTITUTE")
        assert chk.get("passed") is False

    def test_stage_lock_unavailable_when_required_surface_missing(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_stage_lock_missing_surface.jsonl"
        ledger.write_text("", encoding="utf-8")

        class MemWithoutCross(NeutralFamilyMemoryV1):
            def __getattribute__(self, name):
                if name == "get_cross_band_evidence_review_summary":
                    raise AttributeError(name)
                return super().__getattribute__(name)

        mem = MemWithoutCross(durable_ledger_path=str(ledger))
        out = mem.get_system_evidence_review_stage_lock_audit()

        assert out["audit_available"] is False
        assert out["lock_state"] == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE"
        assert out["reason"] == "REQUIRED_SURFACE_MISSING"
