"""
Demo for Window Comparator Summary v1.7.

Shows:
- comparator with matching windows
- comparator with differing windows
- availability mismatch case
- both unavailable case
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
            "event_id": "cmp_evt_01",
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
            "event_id": "cmp_evt_02",
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
            "event_id": "cmp_evt_03",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 3,
            "source_family_ids": ["fam_07"],
            "successor_family_ids": ["fam_08", "fam_09"],
            "pressure_snapshot": {
                "pre_event_pressure": None,
                "post_event_pressure": None,
                "capture_attempted": True,
                "capture_succeeded": False,
                "capture_mode": "EVENT_WRITE_TIME",
                "capture_reason": "PRESSURE_CAPTURE_FAILED",
                "pre_capture_status_by_family": {"fam_07": "PRESSURE_CAPTURE_EXCEPTION:RuntimeError"},
                "post_capture_status_by_family": {
                    "fam_08": "PRESSURE_CAPTURE_EXCEPTION:RuntimeError",
                    "fam_09": "PRESSURE_CAPTURE_EXCEPTION:RuntimeError",
                },
            },
        },
    )


def run_window_comparator_demo_v1_7() -> None:
    ledger_path = "runs/family_v24_window_comparator_demo.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)
    _seed_ledger(ledger_path)
    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)

    _divider("Comparator: Matching Windows")
    print(json.dumps(mem.get_pressure_capture_quality_window_comparator(), indent=2, sort_keys=True))

    _divider("Comparator: Differing Windows")
    print(
        json.dumps(
            mem.get_pressure_capture_quality_window_comparator(
                start_index=0,
                end_index=2,
                start_event_order=3,
                end_event_order=3,
            ),
            indent=2,
            sort_keys=True,
        )
    )

    _divider("Comparator: Index Unavailable, Event-Order Available")
    print(
        json.dumps(
            mem.get_pressure_capture_quality_window_comparator(
                start_index=2,
                end_index=1,
                start_event_order=1,
                end_event_order=3,
            ),
            indent=2,
            sort_keys=True,
        )
    )

    _divider("Comparator: Both Unavailable")
    print(
        json.dumps(
            mem.get_pressure_capture_quality_window_comparator(
                start_index=2,
                end_index=1,
                start_event_order=3,
                end_event_order=2,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    run_window_comparator_demo_v1_7()
