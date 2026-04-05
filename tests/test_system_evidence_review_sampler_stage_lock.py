from unittest.mock import MagicMock

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _mem(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("")
    return NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))


def _index_window_spec():
    return {
        "start_index": 1,
        "end_index": 4,
        "max_events": 10,
        "applied_start_index": 1,
        "applied_end_index": 4,
        "applied_event_count": 3,
    }


def _event_order_window_spec():
    return {
        "start_event_order": 10.0,
        "end_event_order": 30.0,
        "max_events": 10,
        "applied_start_event_order": 10.0,
        "applied_end_event_order": 30.0,
        "applied_event_count": 3,
    }


def _cross_index_ready(window_spec):
    return {
        "review_available": True,
        "review_mode": "CROSS_BAND_EVIDENCE_REVIEW_WINDOW",
        "review_state": "CROSS_BAND_EVIDENCE_REVIEW_READY",
        "review_reason": "BOUNDED_ALIGNMENT_OBSERVED_WITH_AUDITABLE_SURFACE",
        "window_spec": dict(window_spec),
        "evidence_scope": {
            "bounded_scope": "INDEX_WINDOW",
            "bounded_summary_mode": "CROSS_BAND_SELF_CHECK_WINDOW",
            "coverage_notes": ["cross ok"],
            "total_auditable_events": 3,
            "scope_equivalence": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
        },
        "evidence_counts": {"total_auditable_events": 3},
        "warnings": [],
        "lineage_mutation_performed": False,
        "event_creation_performed": False,
        "history_rewrite_performed": False,
    }


def _obs_index_ready(window_spec):
    return {
        "review_available": True,
        "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW_WINDOW",
        "review_state": "OBSERVABILITY_EVIDENCE_REVIEW_READY",
        "review_reason": "BOUNDED_FULLY_AUDITABLE_OBSERVABILITY_EVIDENCE",
        "window_spec": dict(window_spec),
        "evidence_scope": {
            "bounded_scope": "INDEX_WINDOW",
            "bounded_summary_mode": "LEDGER_READ_ONLY_WINDOWED",
            "coverage_notes": ["obs ok"],
            "total_auditable_events": 3,
            "scope_equivalence": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
        },
        "evidence_counts": {"total_auditable_events": 3},
        "warnings": [],
        "lineage_mutation_performed": False,
        "event_creation_performed": False,
        "history_rewrite_performed": False,
    }


def _cross_event_ready(window_spec):
    out = _cross_index_ready(window_spec)
    out["review_mode"] = "CROSS_BAND_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW"
    out["evidence_scope"]["bounded_scope"] = "EVENT_ORDER_WINDOW"
    out["evidence_scope"]["bounded_summary_mode"] = "CROSS_BAND_SELF_CHECK_EVENT_ORDER_WINDOW"
    return out


def _obs_event_ready(window_spec):
    out = _obs_index_ready(window_spec)
    out["review_mode"] = "OBSERVABILITY_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW"
    out["evidence_scope"]["bounded_scope"] = "EVENT_ORDER_WINDOW"
    out["evidence_scope"]["bounded_summary_mode"] = "LEDGER_READ_ONLY_EVENT_ORDER_WINDOWED"
    return out


def _find_check(out, name):
    for chk in out.get("check_results", []):
        if chk.get("check_name") == name:
            return chk
    return {}


def test_stage_lock_window_locked_happy_path(tmp_path):
    mem = _mem(tmp_path)
    ws = _index_window_spec()
    mem.get_cross_band_evidence_review_summary_window = MagicMock(return_value=_cross_index_ready(ws))
    mem.get_observability_evidence_review_summary_window = MagicMock(return_value=_obs_index_ready(ws))

    out = mem.get_system_evidence_review_sampler_stage_lock_window(
        start_index=1,
        end_index=4,
        max_events=10,
    )

    assert out["audit_available"] is True
    assert out["audit_mode"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_WINDOW"
    assert out["lock_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_LOCKED"
    assert out["reason"] == "ALL_CONSISTENCY_CHECKS_PASSED"
    assert all(chk.get("passed") is True for chk in out["check_results"])


def test_stage_lock_event_order_locked_happy_path(tmp_path):
    mem = _mem(tmp_path)
    ws = _event_order_window_spec()
    mem.get_cross_band_evidence_review_summary_event_order_window = MagicMock(return_value=_cross_event_ready(ws))
    mem.get_observability_evidence_review_summary_event_order_window = MagicMock(return_value=_obs_event_ready(ws))

    out = mem.get_system_evidence_review_sampler_stage_lock_event_order_window(
        start_event_order=10.0,
        end_event_order=30.0,
        max_events=10,
    )

    assert out["audit_available"] is True
    assert out["audit_mode"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_EVENT_ORDER_WINDOW"
    assert out["lock_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_LOCKED"
    assert out["reason"] == "ALL_CONSISTENCY_CHECKS_PASSED"
    assert all(chk.get("passed") is True for chk in out["check_results"])


def test_stage_lock_unavailable_when_sampler_surface_missing(tmp_path):
    ledger = tmp_path / "missing_sampler.jsonl"
    ledger.write_text("")

    class MemWithoutSampler(NeutralFamilyMemoryV1):
        def __getattribute__(self, name):
            if name == "get_system_evidence_review_sampler_window":
                raise AttributeError(name)
            return super().__getattribute__(name)

    mem = MemWithoutSampler(durable_ledger_path=str(ledger))
    out = mem.get_system_evidence_review_sampler_stage_lock_window()

    assert out["audit_available"] is False
    assert out["lock_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_UNAVAILABLE"
    assert out["reason"] == "REQUIRED_SURFACE_MISSING"


def test_stage_lock_unavailable_when_required_bounded_anchor_missing(tmp_path):
    ledger = tmp_path / "missing_anchor.jsonl"
    ledger.write_text("")

    class MemWithoutCross(NeutralFamilyMemoryV1):
        def __getattribute__(self, name):
            if name == "get_cross_band_evidence_review_summary_window":
                raise AttributeError(name)
            return super().__getattribute__(name)

    mem = MemWithoutCross(durable_ledger_path=str(ledger))
    out = mem.get_system_evidence_review_sampler_stage_lock_window()

    assert out["audit_available"] is False
    assert out["lock_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_UNAVAILABLE"
    assert out["reason"] == "REQUIRED_SURFACE_MISSING"


def test_stage_lock_inconsistent_on_full_range_leakage(tmp_path):
    mem = _mem(tmp_path)
    ws = _index_window_spec()
    mem.get_cross_band_evidence_review_summary_window = MagicMock(return_value=_cross_index_ready(ws))
    mem.get_observability_evidence_review_summary_window = MagicMock(return_value=_obs_index_ready(ws))

    base_sampler = mem.get_system_evidence_review_sampler_window

    def _drifted_sampler(*args, **kwargs):
        _ = mem.get_system_evidence_review_summary()
        return base_sampler(*args, **kwargs)

    mem.get_system_evidence_review_sampler_window = _drifted_sampler

    out = mem.get_system_evidence_review_sampler_stage_lock_window(
        start_index=1,
        end_index=4,
        max_events=10,
    )

    assert out["lock_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_INCONSISTENT"
    chk = _find_check(out, "FULL_RANGE_SURFACES_CONTEXT_ONLY_NON_PREDICATE")
    assert chk.get("passed") is False


def test_stage_lock_inconsistent_on_window_spec_mismatch_handling_regression(tmp_path):
    mem = _mem(tmp_path)
    ws = _index_window_spec()
    cross = _cross_index_ready(ws)
    obs = _obs_index_ready(ws)
    mem.get_cross_band_evidence_review_summary_window = MagicMock(return_value=cross)
    mem.get_observability_evidence_review_summary_window = MagicMock(return_value=obs)

    def _drifted_sampler(*_args, **_kwargs):
        return {
            "review_available": True,
            "review_mode": "SYSTEM_EVIDENCE_REVIEW_WINDOW",
            "review_state": "SYSTEM_EVIDENCE_REVIEW_READY",
            "review_reason": "BOUNDED_COMPOSED_EVIDENCE_SURFACES_READY",
            "window_spec": dict(ws),
            "evidence_scope": {
                "bounded_scope": "INDEX_WINDOW",
                "scope_equivalence": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
            },
            "evidence_counts": {
                "cross_band_total_auditable_events": 3,
                "observability_total_auditable_events": 3,
                "total_auditable_events": 6,
            },
            "supporting_surfaces": {},
            "warnings": [],
            "explanation_lines": [],
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    mem.get_system_evidence_review_sampler_window = _drifted_sampler

    out = mem.get_system_evidence_review_sampler_stage_lock_window(
        start_index=1,
        end_index=4,
        max_events=10,
    )

    assert out["lock_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_INCONSISTENT"
    chk = _find_check(out, "FAIL_CLOSED_ON_WINDOW_SPEC_MISALIGNMENT")
    assert chk.get("passed") is False


def test_stage_lock_guardrail_flags_remain_false(tmp_path):
    mem = _mem(tmp_path)
    ws = _index_window_spec()
    mem.get_cross_band_evidence_review_summary_window = MagicMock(return_value=_cross_index_ready(ws))
    mem.get_observability_evidence_review_summary_window = MagicMock(return_value=_obs_index_ready(ws))

    base_sampler = mem.get_system_evidence_review_sampler_window

    def _guardrail_drift(*args, **kwargs):
        out = base_sampler(*args, **kwargs)
        out = dict(out)
        out["lineage_mutation_performed"] = True
        out["event_creation_performed"] = True
        out["history_rewrite_performed"] = True
        return out

    mem.get_system_evidence_review_sampler_window = _guardrail_drift

    out = mem.get_system_evidence_review_sampler_stage_lock_window(
        start_index=1,
        end_index=4,
        max_events=10,
    )

    assert out["audit_available"] is True
    assert out["lock_state"] == "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_INCONSISTENT"
    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False
    chk = _find_check(out, "READ_ONLY_GUARDRAILS_FALSE")
    assert chk.get("passed") is False
