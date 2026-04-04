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
            "event_id": "sys_er_01",
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
            "event_id": "sys_er_02",
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


class TestSystemEvidenceReview:
    def test_review_ready_on_healthy_locked_surface_with_meaningful_evidence(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_green.jsonl"
        _seed_green_ledger(ledger)
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))
        mem.get_observability_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW",
                "review_state": "OBSERVABILITY_EVIDENCE_REVIEW_READY",
                "evidence_scope": {"total_auditable_events": 2},
                "evidence_counts": {"total_auditable_events": 2},
                "warnings": [],
            }
        )

        out = mem.get_system_evidence_review_summary()

        assert out["review_available"] is True
        assert out["review_mode"] == "SYSTEM_EVIDENCE_REVIEW"
        assert out["review_state"] == "SYSTEM_EVIDENCE_REVIEW_READY"
        assert out["review_reason"] == "COMPOSED_EVIDENCE_SURFACES_READY"
        assert out["evidence_scope"]["system_gate_state"] == "SYSTEM_GATE_LOCKED"
        assert out["evidence_counts"]["total_auditable_events"] > 0

    def test_ready_requires_real_observability_evidence_review_surface(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_no_obs_review.jsonl"
        ledger.write_text("", encoding="utf-8")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_cross_band_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_state": "CROSS_BAND_EVIDENCE_REVIEW_READY",
                "evidence_scope": {
                    "total_auditable_events": 4,
                    "stage_lock_state": "CROSS_BAND_STAGE_LOCKED",
                    "coverage_notes": ["cross-band evidence present"],
                },
                "evidence_counts": {
                    "CROSS_BAND_ALIGNMENT_OBSERVED": 4,
                    "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                    "CROSS_BAND_PARTIAL": 0,
                    "CROSS_BAND_UNAVAILABLE": 0,
                },
                "warnings": [],
            }
        )
        mem.get_system_lock_gate_posture = MagicMock(
            return_value={
                "gate_available": True,
                "gate_state": "SYSTEM_GATE_LOCKED",
                "gate_reason": "SYSTEM_STAGE_LOCKED",
                "warnings": [],
            }
        )
        mem.get_observability_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "OBSERVABILITY_STAGE_LOCK",
                "lock_state": "OBSERVABILITY_STAGE_LOCKED",
                "warnings": [],
            }
        )
        mem.get_pressure_capture_quality_summary = MagicMock(
            return_value={
                "summary_available": True,
                "auditable_event_count": 5,
                "audit_state_counts": {
                    "PRESSURE_CAPTURE_AUDIT_VALID": 5,
                    "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                    "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                },
                "recoverability_counts": {
                    "FULLY_RECOVERABLE": 5,
                    "PARTIALLY_RECOVERABLE": 0,
                    "UNRECOVERABLE": 0,
                },
                "warnings": [],
                "explanation_lines": ["observability quality available"],
            }
        )
        # Explicitly simulate missing dedicated observability review surface.
        mem.get_observability_evidence_review_summary = None

        out = mem.get_system_evidence_review_summary()

        assert out["review_state"] == "SYSTEM_EVIDENCE_REVIEW_PARTIAL"
        assert "OBSERVABILITY_EVIDENCE_REVIEW_SURFACE_MISSING" in out["warnings"]

    def test_system_gate_and_quality_do_not_gate_ready_when_real_obs_review_is_ready(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_gate_quality_not_predicate.jsonl"
        ledger.write_text("", encoding="utf-8")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_cross_band_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_state": "CROSS_BAND_EVIDENCE_REVIEW_READY",
                "evidence_scope": {
                    "total_auditable_events": 3,
                    "stage_lock_state": "CROSS_BAND_STAGE_LOCKED",
                    "coverage_notes": ["cross-band evidence ready"],
                },
                "evidence_counts": {
                    "CROSS_BAND_ALIGNMENT_OBSERVED": 3,
                    "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                    "CROSS_BAND_PARTIAL": 0,
                    "CROSS_BAND_UNAVAILABLE": 0,
                },
                "warnings": [],
            }
        )
        mem.get_system_lock_gate_posture = MagicMock(
            return_value={
                "gate_available": True,
                "gate_state": "SYSTEM_GATE_UNAVAILABLE",
                "gate_reason": "SYSTEM_STAGE_LOCK_UNAVAILABLE",
                "warnings": [],
            }
        )
        mem.get_observability_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "OBSERVABILITY_STAGE_LOCK",
                "lock_state": "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE",
                "warnings": [],
            }
        )
        mem.get_pressure_capture_quality_summary = MagicMock(
            return_value={
                "summary_available": False,
                "auditable_event_count": 0,
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
                "explanation_lines": ["observability quality unavailable"],
            }
        )
        mem.get_observability_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW",
                "review_state": "OBSERVABILITY_EVIDENCE_REVIEW_READY",
                "evidence_scope": {"total_auditable_events": 2},
                "evidence_counts": {"total_auditable_events": 2},
                "warnings": [],
            }
        )

        out = mem.get_system_evidence_review_summary()

        assert out["review_state"] == "SYSTEM_EVIDENCE_REVIEW_READY"

    def test_review_partial_when_supporting_surfaces_are_asymmetric_or_limited(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_partial.jsonl"
        ledger.write_text("", encoding="utf-8")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_cross_band_evidence_review_summary = MagicMock(
            return_value={
                "review_available": True,
                "review_state": "CROSS_BAND_EVIDENCE_REVIEW_READY",
                "evidence_scope": {
                    "total_auditable_events": 4,
                    "stage_lock_state": "CROSS_BAND_STAGE_LOCKED",
                    "coverage_notes": ["cross-band evidence present"],
                },
                "evidence_counts": {
                    "CROSS_BAND_ALIGNMENT_OBSERVED": 4,
                    "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                    "CROSS_BAND_PARTIAL": 0,
                    "CROSS_BAND_UNAVAILABLE": 0,
                },
                "warnings": [],
            }
        )
        mem.get_system_lock_gate_posture = MagicMock(
            return_value={
                "gate_available": True,
                "gate_state": "SYSTEM_GATE_LOCKED",
                "gate_reason": "SYSTEM_STAGE_LOCKED",
                "warnings": [],
            }
        )
        mem.get_observability_stage_lock_audit = MagicMock(
            return_value={
                "audit_available": True,
                "audit_mode": "OBSERVABILITY_STAGE_LOCK",
                "lock_state": "OBSERVABILITY_STAGE_LOCKED",
                "warnings": [],
            }
        )
        mem.get_pressure_capture_quality_summary = MagicMock(
            return_value={
                "summary_available": False,
                "auditable_event_count": 0,
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
                "warnings": ["OBS_QUALITY_LIMITED"],
                "explanation_lines": ["observability quality surface limited"],
            }
        )
        # Explicitly simulate missing dedicated observability review surface.
        mem.get_observability_evidence_review_summary = None

        out = mem.get_system_evidence_review_summary()

        assert out["review_state"] == "SYSTEM_EVIDENCE_REVIEW_PARTIAL"
        assert out["review_reason"] == "LIMITED_OR_ASYMMETRIC_EVIDENCE_SURFACE"
        assert "OBSERVABILITY_EVIDENCE_REVIEW_SURFACE_MISSING" in out["warnings"]

    def test_review_unavailable_when_required_surface_missing_or_unusable(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_unavailable.jsonl"
        ledger.write_text("", encoding="utf-8")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        mem.get_cross_band_evidence_review_summary = None
        out = mem.get_system_evidence_review_summary()

        assert out["review_available"] is False
        assert out["review_state"] == "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"
        assert out["review_reason"] == "REQUIRED_SURFACE_MISSING"

    def test_no_recommendation_or_action_language_in_output(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_language.jsonl"
        _seed_green_ledger(ledger)
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        out = mem.get_system_evidence_review_summary()

        forbidden_fields = [
            "recommended_action",
            "action_required",
            "rollout_permitted",
            "safe_to_proceed",
            "proceed",
            "should",
        ]
        for field in forbidden_fields:
            assert field not in out
        for line in out.get("explanation_lines", []):
            low = str(line).lower()
            assert "should" not in low
            assert "recommend" not in low
            assert "rollout" not in low
            assert "action required" not in low

    def test_read_only_no_mutation_behavior(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_no_mutation.jsonl"
        _seed_green_ledger(ledger)
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        before = ledger.read_text(encoding="utf-8")
        write_counter_before = mem._durable_write_counter
        written_ids_before = set(mem._durable_written_event_ids)
        fission_events_before = list(mem._fission_events)
        reunion_events_before = list(mem._reunion_events)

        out = mem.get_system_evidence_review_summary()

        after = ledger.read_text(encoding="utf-8")
        assert before == after
        assert mem._durable_write_counter == write_counter_before
        assert mem._durable_written_event_ids == written_ids_before
        assert mem._fission_events == fission_events_before
        assert mem._reunion_events == reunion_events_before
        assert out["lineage_mutation_performed"] is False
        assert out["event_creation_performed"] is False
        assert out["history_rewrite_performed"] is False

    def test_no_repair_no_retrofit_behavior(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_no_repair.jsonl"
        legacy = {
            "event_id": "legacy_evt_01",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 7,
            "source_family_ids": ["fam_20", "fam_21"],
            "successor_family_ids": ["fam_22"],
        }
        _write_event(ledger, legacy)
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        before = ledger.read_text(encoding="utf-8")
        _ = mem.get_system_evidence_review_summary()
        after = ledger.read_text(encoding="utf-8")
        persisted = mem.get_event_ledger()[0]

        assert before == after
        assert persisted == legacy

    def test_embedded_supporting_surfaces_preserved_honestly(self, tmp_path: Path):
        ledger = tmp_path / "system_evidence_supporting_surfaces.jsonl"
        ledger.write_text("", encoding="utf-8")
        mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

        cross_surface = {
            "review_available": True,
            "review_state": "CROSS_BAND_EVIDENCE_REVIEW_READY",
            "evidence_scope": {
                "total_auditable_events": 2,
                "stage_lock_state": "CROSS_BAND_STAGE_LOCKED",
                "coverage_notes": ["cross ready"],
            },
            "evidence_counts": {
                "CROSS_BAND_ALIGNMENT_OBSERVED": 2,
                "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                "CROSS_BAND_PARTIAL": 0,
                "CROSS_BAND_UNAVAILABLE": 0,
            },
            "warnings": ["CB_WARN"],
        }
        system_surface = {
            "gate_available": True,
            "gate_state": "SYSTEM_GATE_LOCKED",
            "gate_reason": "SYSTEM_STAGE_LOCKED",
            "warnings": ["SYS_WARN"],
        }
        obs_lock_surface = {
            "audit_available": True,
            "audit_mode": "OBSERVABILITY_STAGE_LOCK",
            "lock_state": "OBSERVABILITY_STAGE_LOCKED",
            "warnings": ["OBS_LOCK_WARN"],
        }
        obs_quality_surface = {
            "summary_available": True,
            "auditable_event_count": 2,
            "audit_state_counts": {
                "PRESSURE_CAPTURE_AUDIT_VALID": 2,
                "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
            },
            "recoverability_counts": {
                "FULLY_RECOVERABLE": 2,
                "PARTIALLY_RECOVERABLE": 0,
                "UNRECOVERABLE": 0,
            },
            "warnings": ["OBS_QUALITY_WARN"],
            "explanation_lines": ["obs quality ready"],
        }
        obs_review_surface = {
            "review_available": True,
            "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW",
            "review_state": "OBSERVABILITY_EVIDENCE_REVIEW_READY",
            "warnings": ["OBS_REVIEW_WARN"],
        }

        mem.get_cross_band_evidence_review_summary = MagicMock(return_value=cross_surface)
        mem.get_system_lock_gate_posture = MagicMock(return_value=system_surface)
        mem.get_observability_stage_lock_audit = MagicMock(return_value=obs_lock_surface)
        mem.get_pressure_capture_quality_summary = MagicMock(return_value=obs_quality_surface)
        mem.get_observability_evidence_review_summary = MagicMock(return_value=obs_review_surface)

        out = mem.get_system_evidence_review_summary()

        assert out["system_lock_posture"] == system_surface
        assert out["supporting_surfaces"]["cross_band_evidence_review_summary"] == cross_surface
        assert out["supporting_surfaces"]["observability_stage_lock_audit"] == obs_lock_surface
        assert out["supporting_surfaces"]["observability_pressure_capture_quality_summary"] == obs_quality_surface
        assert out["supporting_surfaces"]["observability_evidence_review_summary"] == obs_review_surface
        assert "CB_WARN" in out["warnings"]
        assert "SYS_WARN" in out["warnings"]
        assert "OBS_LOCK_WARN" in out["warnings"]
        assert "OBS_QUALITY_WARN" in out["warnings"]
        assert "OBS_REVIEW_WARN" in out["warnings"]
