"""
Demo for Bounded Time-Slice Capture Quality Summary v1.5.

Shows:
- full-range windowed summary
- bounded index window summary
- bounded window with max_events limit
- invalid bounds fail-closed behavior
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


def _seed_mixed_transition_ledger(path: str) -> None:
    _write_event(
        path,
        {
            "event_id": "window_evt_01",
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
            "event_id": "window_evt_02",
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
    _write_event(
        path,
        {
            "event_id": "window_evt_03",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 3,
            "source_family_ids": ["fam_07", "fam_08"],
            "successor_family_ids": ["fam_09"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_07", "fam_08"], "PRESSURE_STABLE"),
                "post_event_pressure": None,
                "capture_attempted": True,
                "capture_succeeded": True,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FULL",
                "pre_capture_status_by_family": {
                    "fam_07": "PRESSURE_CAPTURED",
                    "fam_08": "PRESSURE_CAPTURED",
                },
                "post_capture_status_by_family": {"fam_09": "PRESSURE_UNAVAILABLE"},
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "window_evt_04",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 4,
            "source_family_ids": ["fam_10"],
            "successor_family_ids": ["fam_11", "fam_12"],
        },
    )


def run_capture_quality_window_demo_v1_5() -> None:
    ledger_path = "runs/family_v22_capture_quality_window_demo.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)

    _seed_mixed_transition_ledger(ledger_path)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)

    _divider("Windowed Summary: Full Range")
    print(json.dumps(mem.get_pressure_capture_quality_summary_window(), indent=2, sort_keys=True))

    _divider("Windowed Summary: start_index=1, end_index=4")
    print(
        json.dumps(
            mem.get_pressure_capture_quality_summary_window(start_index=1, end_index=4),
            indent=2,
            sort_keys=True,
        )
    )

    _divider("Windowed Summary: start_index=0, end_index=4, max_events=2")
    print(
        json.dumps(
            mem.get_pressure_capture_quality_summary_window(start_index=0, end_index=4, max_events=2),
            indent=2,
            sort_keys=True,
        )
    )

    _divider("Windowed Summary: Invalid Bounds (start_index=4, end_index=2)")
    print(
        json.dumps(
            mem.get_pressure_capture_quality_summary_window(start_index=4, end_index=2),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    run_capture_quality_window_demo_v1_5()
