"""
Demo for Observability Consistency / Stage Lock v1.8.

Shows:
- locked state on consistent observability outputs
- inconsistent state when comparator delta payload is intentionally drifted in demo
- unavailable state when a required surface is missing
"""

import json
import os

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _divider(title: str) -> None:
    print("\n" + ("=" * 72))
    print(title)
    print(("=" * 72))


def _write_event(path: str, record: dict) -> None:
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


def _seed_ledger(path: str) -> None:
    _write_event(
        path,
        {
            "event_id": "lock_evt_01",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_01"],
            "successor_family_ids": ["fam_02", "fam_03"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_01"], "PRESSURE_FISSION_PRONE"),
                "post_event_pressure": _pressure_payload(["fam_02", "fam_03"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {"fam_01": "PRESSURE_CAPTURED"},
                "post_capture_status_by_family": {
                    "fam_02": "PRESSURE_CAPTURED",
                    "fam_03": "PRESSURE_CAPTURED",
                },
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "lock_evt_02",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 2,
            "source_family_ids": ["fam_04", "fam_05"],
            "successor_family_ids": ["fam_06"],
            "pressure_snapshot": {
                "pre_event_pressure": None,
                "post_event_pressure": _pressure_payload(["fam_06"], "PRESSURE_STABLE"),
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_PARTIAL",
                "pre_capture_status_by_family": {
                    "fam_04": "PRESSURE_UNAVAILABLE",
                    "fam_05": "PRESSURE_UNAVAILABLE",
                },
                "post_capture_status_by_family": {"fam_06": "PRESSURE_CAPTURED"},
            },
        },
    )


def run_observability_stage_lock_demo_v1_8() -> None:
    ledger_path = "runs/family_v25_observability_stage_lock_demo.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)
    _seed_ledger(ledger_path)

    mem_locked = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    _divider("Stage Lock: Consistent (Locked)")
    print(json.dumps(mem_locked.get_observability_stage_lock_audit(), indent=2, sort_keys=True))

    mem_inconsistent = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    original = mem_inconsistent.get_pressure_capture_quality_window_comparator

    def drifted_comparator(*args, **kwargs):
        out = original(*args, **kwargs)
        out["comparison"]["window_event_count_delta"] = -123
        return out

    mem_inconsistent.get_pressure_capture_quality_window_comparator = drifted_comparator
    _divider("Stage Lock: Inconsistent (Comparator Delta Drift)")
    print(json.dumps(mem_inconsistent.get_observability_stage_lock_audit(), indent=2, sort_keys=True))

    mem_unavailable = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    mem_unavailable.get_pressure_capture_quality_summary_window = None
    _divider("Stage Lock: Unavailable (Missing Required Surface)")
    print(json.dumps(mem_unavailable.get_observability_stage_lock_audit(), indent=2, sort_keys=True))


if __name__ == "__main__":
    run_observability_stage_lock_demo_v1_8()
