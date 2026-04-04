"""
Demo for Event-Order Bounded Capture Quality Summary v1.6.

Shows:
- full-range event_order window summary
- bounded event_order window summary
- bounded event_order window with max_events
- invalid event_order bounds fail-closed
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
            "event_id": "order_evt_01",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 10,
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
            "event_id": "order_evt_02",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 20,
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
            "event_id": "order_evt_03",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 20,
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
            "event_id": "order_evt_04",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 30,
            "source_family_ids": ["fam_10"],
            "successor_family_ids": ["fam_11", "fam_12"],
        },
    )
    _write_event(
        path,
        {
            "event_id": "order_evt_no_event_order",
            "event_type": "FAMILY_FISSION_V1",
            "source_family_ids": ["fam_13"],
            "successor_family_ids": ["fam_14", "fam_15"],
        },
    )


def run_capture_quality_event_order_window_demo_v1_6() -> None:
    ledger_path = "runs/family_v23_capture_quality_event_order_window_demo.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)

    _seed_mixed_transition_ledger(ledger_path)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)

    _divider("Event-Order Window Summary: Full Range")
    print(json.dumps(mem.get_pressure_capture_quality_summary_event_order_window(), indent=2, sort_keys=True))

    _divider("Event-Order Window Summary: start_event_order=20, end_event_order=30")
    print(
        json.dumps(
            mem.get_pressure_capture_quality_summary_event_order_window(
                start_event_order=20,
                end_event_order=30,
            ),
            indent=2,
            sort_keys=True,
        )
    )

    _divider("Event-Order Window Summary: start_event_order=10, end_event_order=30, max_events=2")
    print(
        json.dumps(
            mem.get_pressure_capture_quality_summary_event_order_window(
                start_event_order=10,
                end_event_order=30,
                max_events=2,
            ),
            indent=2,
            sort_keys=True,
        )
    )

    _divider("Event-Order Window Summary: Invalid Bounds (start_event_order=30, end_event_order=20)")
    print(
        json.dumps(
            mem.get_pressure_capture_quality_summary_event_order_window(
                start_event_order=30,
                end_event_order=20,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    run_capture_quality_event_order_window_demo_v1_6()
