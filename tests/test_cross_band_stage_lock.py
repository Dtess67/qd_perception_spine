import json
from pathlib import Path
from unittest.mock import patch

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


def _write_green_ledger(path: Path) -> None:
    _write_event(
        path,
        {
            "event_id": "cbsl_align_fission",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_01"],
            "successor_family_ids": ["fam_02", "fam_03"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_01"], "PRESSURE_FISSION_PRONE"),
                "post_event_pressure": _pressure_payload(["fam_02", "fam_03"], "PRESSURE_STABLE"),
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "cbsl_contradict_fission",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 2,
            "source_family_ids": ["fam_10"],
            "successor_family_ids": ["fam_11", "fam_12"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_10"], "PRESSURE_STABLE"),
                "post_event_pressure": _pressure_payload(["fam_11", "fam_12"], "PRESSURE_STABLE"),
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "cbsl_partial_reunion",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 3,
            "source_family_ids": ["fam_20", "fam_21"],
            "successor_family_ids": ["fam_22"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_20", "fam_21"], "PRESSURE_STRETCHED"),
                "post_event_pressure": _pressure_payload(["fam_22"], "PRESSURE_STABLE"),
            },
        },
    )
    # No pressure_snapshot — honest unavailable case
    _write_event(
        path,
        {
            "event_id": "cbsl_no_pressure",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 4,
            "source_family_ids": ["fam_30"],
            "successor_family_ids": ["fam_31", "fam_32"],
        },
    )


# ---------------------------------------------------------------------------
# Test 1: Stage lock passes on current green state
# ---------------------------------------------------------------------------

def test_cross_band_stage_lock_passes_on_green_ledger(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_green_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_stage_lock_audit()

    assert out["audit_available"] is True
    assert out["audit_mode"] == "CROSS_BAND_STAGE_LOCK"
    assert out["lock_state"] == "CROSS_BAND_STAGE_LOCKED"
    assert out["reason"] == "ALL_CONSISTENCY_CHECKS_PASSED"
    assert out["checks_run"] == 8
    assert out["checks_passed"] == 8
    assert out["checks_failed"] == 0
    assert all(c["passed"] for c in out["check_results"])
    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False


def test_cross_band_stage_lock_passes_on_empty_ledger(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    ledger.write_text("", encoding="utf-8")
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_stage_lock_audit()

    assert out["audit_available"] is True
    assert out["lock_state"] == "CROSS_BAND_STAGE_LOCKED"
    assert out["checks_failed"] == 0


# ---------------------------------------------------------------------------
# Test 2: Lock becomes INCONSISTENT if comparator delta direction is wrong
# ---------------------------------------------------------------------------

def test_cross_band_stage_lock_inconsistent_when_delta_direction_wrong(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_green_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    original_comparator = mem.get_cross_band_self_check_window_comparator

    def patched_comparator(**kwargs):
        result = original_comparator(**kwargs)
        # Flip the delta direction for CROSS_BAND_ALIGNMENT_OBSERVED
        comp = result["comparison"]
        deltas = comp["self_check_state_count_deltas"]
        deltas["CROSS_BAND_ALIGNMENT_OBSERVED"] = -(
            deltas["CROSS_BAND_ALIGNMENT_OBSERVED"] + 99
        )
        return result

    with patch.object(mem, "get_cross_band_self_check_window_comparator", patched_comparator):
        out = mem.get_cross_band_stage_lock_audit()

    assert out["lock_state"] == "CROSS_BAND_STAGE_LOCK_INCONSISTENT"
    assert out["reason"] == "CONSISTENCY_CHECK_FAILED"
    assert out["checks_failed"] >= 1
    failed_names = [c["check_name"] for c in out["check_results"] if not c["passed"]]
    assert "COMPARATOR_DELTA_DIRECTION_CORRECT" in failed_names


def test_cross_band_stage_lock_inconsistent_when_comparator_index_side_diverges(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_green_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    original_comparator = mem.get_cross_band_self_check_window_comparator

    def patched_comparator(**kwargs):
        result = original_comparator(**kwargs)
        # Corrupt the embedded index summary so it diverges from the direct v1.1 call
        result["index_window_summary"] = dict(result["index_window_summary"])
        result["index_window_summary"]["__injected_field__"] = "drift"
        return result

    with patch.object(mem, "get_cross_band_self_check_window_comparator", patched_comparator):
        out = mem.get_cross_band_stage_lock_audit()

    assert out["lock_state"] == "CROSS_BAND_STAGE_LOCK_INCONSISTENT"
    failed_names = [c["check_name"] for c in out["check_results"] if not c["passed"]]
    assert "COMPARATOR_INDEX_SIDE_MATCHES_V1_1" in failed_names


def test_cross_band_stage_lock_inconsistent_when_comparator_event_order_side_diverges(
    tmp_path: Path,
):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_green_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    original_comparator = mem.get_cross_band_self_check_window_comparator

    def patched_comparator(**kwargs):
        result = original_comparator(**kwargs)
        result["event_order_window_summary"] = dict(result["event_order_window_summary"])
        result["event_order_window_summary"]["__injected_field__"] = "drift"
        return result

    with patch.object(mem, "get_cross_band_self_check_window_comparator", patched_comparator):
        out = mem.get_cross_band_stage_lock_audit()

    assert out["lock_state"] == "CROSS_BAND_STAGE_LOCK_INCONSISTENT"
    failed_names = [c["check_name"] for c in out["check_results"] if not c["passed"]]
    assert "COMPARATOR_EVENT_ORDER_SIDE_MATCHES_V1_2" in failed_names


# ---------------------------------------------------------------------------
# Test 3: Lock becomes INCONSISTENT if bucket surfaces drift
# ---------------------------------------------------------------------------

def test_cross_band_stage_lock_inconsistent_when_bucket_names_drift(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_green_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    original_v1_1 = mem.get_cross_band_self_check_summary_window

    def patched_v1_1(**kwargs):
        result = original_v1_1(**kwargs)
        # Replace canonical bucket name with a drifted name
        counts = dict(result.get("self_check_state_counts", {}))
        if "CROSS_BAND_ALIGNMENT_OBSERVED" in counts:
            counts["CROSS_BAND_ALIGNMENT_DRIFTED"] = counts.pop("CROSS_BAND_ALIGNMENT_OBSERVED")
        result = dict(result)
        result["self_check_state_counts"] = counts
        return result

    with patch.object(mem, "get_cross_band_self_check_summary_window", patched_v1_1):
        out = mem.get_cross_band_stage_lock_audit()

    assert out["lock_state"] == "CROSS_BAND_STAGE_LOCK_INCONSISTENT"
    failed_names = [c["check_name"] for c in out["check_results"] if not c["passed"]]
    assert "BUCKET_NAMES_PRESERVED" in failed_names


# ---------------------------------------------------------------------------
# Test 4: Lock becomes UNAVAILABLE if a required surface is missing
# ---------------------------------------------------------------------------

def test_cross_band_stage_lock_unavailable_when_comparator_missing(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_green_ledger(ledger)

    # Subclass that hides the comparator so hasattr returns False
    class MemWithoutComparator(NeutralFamilyMemoryV1):
        def __getattribute__(self, name: str):
            if name == "get_cross_band_self_check_window_comparator":
                raise AttributeError(name)
            return super().__getattribute__(name)

    mem = MemWithoutComparator(durable_ledger_path=str(ledger))
    out = mem.get_cross_band_stage_lock_audit()

    assert out["audit_available"] is False
    assert out["lock_state"] == "CROSS_BAND_STAGE_LOCK_UNAVAILABLE"
    assert out["reason"] == "REQUIRED_API_SURFACE_MISSING"
    assert out["checks_run"] == 0
    assert out["contract_surface"]["comparator_api_present"] is False


def test_cross_band_stage_lock_unavailable_when_v1_1_raises(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_green_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    def boom(**kwargs):
        raise RuntimeError("simulated exception")

    with patch.object(mem, "get_cross_band_self_check_summary_window", boom):
        out = mem.get_cross_band_stage_lock_audit()

    assert out["audit_available"] is False
    assert out["lock_state"] == "CROSS_BAND_STAGE_LOCK_UNAVAILABLE"
    assert "V1_1_CALL_EXCEPTION" in out["reason"]


# ---------------------------------------------------------------------------
# Test 5: Read-only / no mutation behavior
# ---------------------------------------------------------------------------

def test_cross_band_stage_lock_read_only_no_mutation(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_green_ledger(ledger)
    before = ledger.read_text(encoding="utf-8")
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_stage_lock_audit()
    after = ledger.read_text(encoding="utf-8")

    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False
    assert before == after


# ---------------------------------------------------------------------------
# Test 6: No repair / no retrofit behavior — legacy events without snapshots
# ---------------------------------------------------------------------------

def test_cross_band_stage_lock_no_repair_no_retrofit(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    legacy = {
        "event_id": "cbsl_legacy_no_snapshot",
        "event_type": "FAMILY_REUNION_V1",
        "event_order": 10,
        "source_family_ids": ["fam_50", "fam_51"],
        "successor_family_ids": ["fam_52"],
    }
    _write_event(ledger, legacy)
    before = ledger.read_text(encoding="utf-8")
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_stage_lock_audit()
    after = ledger.read_text(encoding="utf-8")

    # Ledger untouched
    assert before == after
    # Legacy event not repaired or retrofitted
    persisted = mem.get_event_ledger()[0]
    assert persisted == legacy
    # Guardrails clean
    assert out["lineage_mutation_performed"] is False
    assert out["event_creation_performed"] is False
    assert out["history_rewrite_performed"] is False


# ---------------------------------------------------------------------------
# Test 7: Contract surface shape is complete and correct
# ---------------------------------------------------------------------------

def test_cross_band_stage_lock_contract_surface_shape(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_green_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_stage_lock_audit()
    cs = out["contract_surface"]

    assert cs["single_event_api_present"] is True
    assert cs["index_window_api_present"] is True
    assert cs["event_order_window_api_present"] is True
    assert cs["comparator_api_present"] is True
    assert cs["bucket_surfaces"] == [
        "CROSS_BAND_ALIGNMENT_OBSERVED",
        "CROSS_BAND_CONTRADICTION_OBSERVED",
        "CROSS_BAND_PARTIAL",
        "CROSS_BAND_UNAVAILABLE",
    ]
    assert cs["window_semantics"]["v1_1_index_window"] == (
        "start_index_inclusive_end_index_exclusive"
    )
    assert cs["window_semantics"]["v1_2_event_order_window"] == (
        "start_event_order_inclusive_end_event_order_inclusive"
    )
    assert cs["comparator_delta_direction"] == "event_order_window_minus_index_window"


# ---------------------------------------------------------------------------
# Test 8: check_results shape is complete for all 8 checks
# ---------------------------------------------------------------------------

def test_cross_band_stage_lock_check_results_shape(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_green_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    out = mem.get_cross_band_stage_lock_audit()

    assert len(out["check_results"]) == 8
    expected_check_names = {
        "SINGLE_EVENT_SURFACE_USABLE",
        "INDEX_WINDOW_FULL_RANGE_CONSISTENT",
        "COMPARATOR_INDEX_SIDE_MATCHES_V1_1",
        "COMPARATOR_EVENT_ORDER_SIDE_MATCHES_V1_2",
        "BUCKET_NAMES_PRESERVED",
        "READ_ONLY_GUARDRAILS_FALSE",
        "UNAVAILABLE_CASES_REMAIN_UNAVAILABLE",
        "COMPARATOR_DELTA_DIRECTION_CORRECT",
    }
    actual_check_names = {c["check_name"] for c in out["check_results"]}
    assert actual_check_names == expected_check_names

    for c in out["check_results"]:
        assert "check_name" in c
        assert "passed" in c
        assert isinstance(c["passed"], bool)
        assert "reason" in c
        assert "details" in c


# ---------------------------------------------------------------------------
# Test 9: Unavailable cases remain unavailable — check 7 catches hardened state
# ---------------------------------------------------------------------------

def test_cross_band_stage_lock_inconsistent_when_unavailable_case_hardened(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    # Write only an event without pressure_snapshot
    _write_event(
        ledger,
        {
            "event_id": "cbsl_no_pressure_only",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_40"],
            "successor_family_ids": ["fam_41", "fam_42"],
        },
    )
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    original_v1_0a = mem.get_transition_cross_band_self_check

    def patched_v1_0a(event_id: str) -> dict:
        result = original_v1_0a(event_id)
        # Force-harden state (simulates a broken implementation)
        result = dict(result)
        result["self_check_state"] = "CROSS_BAND_ALIGNMENT_OBSERVED"
        return result

    with patch.object(mem, "get_transition_cross_band_self_check", patched_v1_0a):
        out = mem.get_cross_band_stage_lock_audit()

    assert out["lock_state"] == "CROSS_BAND_STAGE_LOCK_INCONSISTENT"
    failed_names = [c["check_name"] for c in out["check_results"] if not c["passed"]]
    assert "UNAVAILABLE_CASES_REMAIN_UNAVAILABLE" in failed_names


# ---------------------------------------------------------------------------
# Test 10: Read-only guardrail violation triggers INCONSISTENT
# ---------------------------------------------------------------------------

def test_cross_band_stage_lock_inconsistent_when_guardrail_violated(tmp_path: Path):
    ledger = tmp_path / "event_ledger.jsonl"
    _write_green_ledger(ledger)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=str(ledger))

    original_v1_1 = mem.get_cross_band_self_check_summary_window

    def patched_v1_1(**kwargs):
        result = original_v1_1(**kwargs)
        result = dict(result)
        result["lineage_mutation_performed"] = True
        return result

    with patch.object(mem, "get_cross_band_self_check_summary_window", patched_v1_1):
        out = mem.get_cross_band_stage_lock_audit()

    assert out["lock_state"] == "CROSS_BAND_STAGE_LOCK_INCONSISTENT"
    failed_names = [c["check_name"] for c in out["check_results"] if not c["passed"]]
    assert "READ_ONLY_GUARDRAILS_FALSE" in failed_names
