"""
Tests for get_system_stage_lock_audit() -- Umbrella Lock Integration v1.0.

Starting count: 238 passed.
New tests target: 10 new -> 248 total.
"""

import json
import pytest

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pressure_payload(family_ids, state):
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


def _write_event(path, record):
    with open(path, "a", encoding="utf-8") as f:
        print(json.dumps(record, sort_keys=True, separators=(",", ":")), file=f)


def _green_ledger(path):
    """Seed a ledger that produces LOCKED from both sub-bands."""
    _write_event(path, {
        "event_id": "ssl_t_01",
        "event_type": "FAMILY_FISSION_V1",
        "event_order": 1,
        "source_family_ids": ["fa"],
        "successor_family_ids": ["fb", "fc"],
        "pressure_snapshot": {
            "pre_event_pressure": _pressure_payload(["fa"], "PRESSURE_FISSION_PRONE"),
            "post_event_pressure": _pressure_payload(["fb", "fc"], "PRESSURE_STABLE"),
        },
    })
    _write_event(path, {
        "event_id": "ssl_t_02",
        "event_type": "FAMILY_REUNION_V1",
        "event_order": 2,
        "source_family_ids": ["fx", "fy"],
        "successor_family_ids": ["fz"],
        "pressure_snapshot": {
            "pre_event_pressure": _pressure_payload(["fx", "fy"], "PRESSURE_STRETCHED"),
            "post_event_pressure": _pressure_payload(["fz"], "PRESSURE_STABLE"),
        },
    })


@pytest.fixture
def green_mem(tmp_path):
    p = str(tmp_path / "ssl_green.jsonl")
    _green_ledger(p)
    return NeutralFamilyMemoryV1(durable_ledger_path=p)


@pytest.fixture
def empty_mem(tmp_path):
    p = str(tmp_path / "ssl_empty.jsonl")
    open(p, "w").close()
    return NeutralFamilyMemoryV1(durable_ledger_path=p)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_system_stage_lock_passes_on_green_ledger(green_mem):
    result = green_mem.get_system_stage_lock_audit()
    assert result["audit_available"] is True
    assert result["lock_state"] == "SYSTEM_STAGE_LOCKED"
    assert result["reason"] == "ALL_SUB_AUDITS_LOCKED"
    assert result["checks_run"] == 5
    assert result["checks_passed"] == 5
    assert result["checks_failed"] == 0
    assert result["audit_mode"] == "SYSTEM_STAGE_LOCK"


def test_system_stage_lock_passes_on_empty_ledger(empty_mem):
    result = empty_mem.get_system_stage_lock_audit()
    assert result["audit_available"] is True
    # Keep umbrella composition read-only: do not reinterpret lower-band outcomes.
    assert result["lock_state"] in (
        "SYSTEM_STAGE_LOCKED",
        "SYSTEM_STAGE_LOCK_UNAVAILABLE",
    )
    assert result["checks_failed"] == 0


def test_system_stage_lock_sub_audits_embedded(green_mem):
    result = green_mem.get_system_stage_lock_audit()
    assert "sub_audits" in result
    assert "observability_stage_lock" in result["sub_audits"]
    assert "cross_band_stage_lock" in result["sub_audits"]
    obs = result["sub_audits"]["observability_stage_lock"]
    cb = result["sub_audits"]["cross_band_stage_lock"]
    assert obs.get("audit_mode") == "OBSERVABILITY_STAGE_LOCK"
    assert cb.get("audit_mode") == "CROSS_BAND_STAGE_LOCK"


def test_system_stage_lock_read_only_no_mutation(green_mem):
    result = green_mem.get_system_stage_lock_audit()
    assert result["lineage_mutation_performed"] is False
    assert result["event_creation_performed"] is False
    assert result["history_rewrite_performed"] is False


def test_system_stage_lock_check_results_shape(green_mem):
    result = green_mem.get_system_stage_lock_audit()
    expected_checks = {
        "OBSERVABILITY_STAGE_LOCK_PRESENT_AND_USABLE",
        "CROSS_BAND_STAGE_LOCK_PRESENT_AND_USABLE",
        "OBSERVABILITY_STAGE_LOCKED_WHEN_AVAILABLE",
        "CROSS_BAND_STAGE_LOCKED_WHEN_AVAILABLE",
        "READ_ONLY_GUARDRAILS_FALSE",
    }
    found_checks = {c["check_name"] for c in result["check_results"]}
    assert found_checks == expected_checks
    for c in result["check_results"]:
        assert "passed" in c
        assert "reason" in c
        assert "details" in c


def test_system_stage_lock_inconsistent_when_obs_inconsistent(tmp_path):
    p = str(tmp_path / "ssl_obs_inc.jsonl")
    _green_ledger(p)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=p)

    orig_obs = mem.get_observability_stage_lock_audit

    def _fake_obs():
        r = orig_obs()
        r["lock_state"] = "OBSERVABILITY_STAGE_LOCK_INCONSISTENT"
        return r

    mem.get_observability_stage_lock_audit = _fake_obs
    result = mem.get_system_stage_lock_audit()
    assert result["lock_state"] == "SYSTEM_STAGE_LOCK_INCONSISTENT"
    assert result["checks_failed"] >= 1
    failed = [c["check_name"] for c in result["check_results"] if not c["passed"]]
    assert "OBSERVABILITY_STAGE_LOCKED_WHEN_AVAILABLE" in failed


def test_system_stage_lock_inconsistent_when_cb_inconsistent(tmp_path):
    p = str(tmp_path / "ssl_cb_inc.jsonl")
    _green_ledger(p)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=p)

    orig_cb = mem.get_cross_band_stage_lock_audit

    def _fake_cb():
        r = orig_cb()
        r["lock_state"] = "CROSS_BAND_STAGE_LOCK_INCONSISTENT"
        return r

    mem.get_cross_band_stage_lock_audit = _fake_cb
    result = mem.get_system_stage_lock_audit()
    assert result["lock_state"] == "SYSTEM_STAGE_LOCK_INCONSISTENT"
    failed = [c["check_name"] for c in result["check_results"] if not c["passed"]]
    assert "CROSS_BAND_STAGE_LOCKED_WHEN_AVAILABLE" in failed


def test_system_stage_lock_unavailable_when_obs_api_missing(tmp_path):
    p = str(tmp_path / "ssl_no_obs.jsonl")
    _green_ledger(p)

    class MemWithoutObs(NeutralFamilyMemoryV1):
        def __getattribute__(self, name):
            if name == "get_observability_stage_lock_audit":
                raise AttributeError(name)
            return super().__getattribute__(name)

    mem = MemWithoutObs(durable_ledger_path=p)
    result = mem.get_system_stage_lock_audit()
    assert result["audit_available"] is False
    assert result["lock_state"] == "SYSTEM_STAGE_LOCK_UNAVAILABLE"
    assert result["reason"] == "REQUIRED_SUB_AUDIT_API_MISSING"
    assert result["checks_run"] == 0


def test_system_stage_lock_unavailable_when_cb_api_missing(tmp_path):
    p = str(tmp_path / "ssl_no_cb.jsonl")
    _green_ledger(p)

    class MemWithoutCb(NeutralFamilyMemoryV1):
        def __getattribute__(self, name):
            if name == "get_cross_band_stage_lock_audit":
                raise AttributeError(name)
            return super().__getattribute__(name)

    mem = MemWithoutCb(durable_ledger_path=p)
    result = mem.get_system_stage_lock_audit()
    assert result["audit_available"] is False
    assert result["lock_state"] == "SYSTEM_STAGE_LOCK_UNAVAILABLE"
    assert result["reason"] == "REQUIRED_SUB_AUDIT_API_MISSING"
    assert result["checks_run"] == 0


def test_system_stage_lock_unavailable_when_obs_raises(tmp_path):
    p = str(tmp_path / "ssl_obs_raises.jsonl")
    _green_ledger(p)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=p)

    def _raising():
        raise RuntimeError("simulated obs failure")

    mem.get_observability_stage_lock_audit = _raising
    result = mem.get_system_stage_lock_audit()
    assert result["audit_available"] is False
    assert result["lock_state"] == "SYSTEM_STAGE_LOCK_UNAVAILABLE"
    assert result["reason"] == "SUB_AUDIT_CALL_FAILED"


def test_system_stage_lock_inconsistent_when_guardrail_violated(tmp_path):
    p = str(tmp_path / "ssl_grd.jsonl")
    _green_ledger(p)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=p)

    orig_obs = mem.get_observability_stage_lock_audit

    def _mutating_obs():
        r = orig_obs()
        r["lineage_mutation_performed"] = True
        return r

    mem.get_observability_stage_lock_audit = _mutating_obs
    result = mem.get_system_stage_lock_audit()
    assert result["lock_state"] == "SYSTEM_STAGE_LOCK_INCONSISTENT"
    failed = [c["check_name"] for c in result["check_results"] if not c["passed"]]
    assert "READ_ONLY_GUARDRAILS_FALSE" in failed


def test_system_stage_lock_no_repair_no_retrofit_side_effects(tmp_path):
    p = str(tmp_path / "ssl_no_mutation.jsonl")
    _green_ledger(p)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=p)

    with open(p, "r", encoding="utf-8") as f:
        ledger_before = f.read()
    write_counter_before = mem._durable_write_counter
    written_ids_before = set(mem._durable_written_event_ids)
    fission_events_before = list(mem._fission_events)
    reunion_events_before = list(mem._reunion_events)

    result = mem.get_system_stage_lock_audit()

    with open(p, "r", encoding="utf-8") as f:
        ledger_after = f.read()

    assert ledger_after == ledger_before
    assert mem._durable_write_counter == write_counter_before
    assert mem._durable_written_event_ids == written_ids_before
    assert mem._fission_events == fission_events_before
    assert mem._reunion_events == reunion_events_before
    assert result["lineage_mutation_performed"] is False
    assert result["event_creation_performed"] is False
    assert result["history_rewrite_performed"] is False
