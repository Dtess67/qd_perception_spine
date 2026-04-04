"""
Demo for Cross-Band Window Comparator v1.3.

Shows:
- default matching comparison across index and event_order windows
- bounded windows producing mismatches
- availability mismatch behavior
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
            "event_id": "cbcmp_evt_01",
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
            "event_id": "cbcmp_evt_02",
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
            "event_id": "cbcmp_evt_03",
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
    _write_event(
        path,
        {
            "event_id": "cbcmp_evt_04",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 4,
            "source_family_ids": ["fam_30"],
            "successor_family_ids": ["fam_31", "fam_32"],
        },
    )


def run_cross_band_window_comparator_demo_v1_3() -> None:
    ledger_path = "runs/family_v30_cross_band_window_comparator_demo.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)
    _seed_ledger(ledger_path)

    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)

    _divider("Cross-Band Window Comparator: Matching (Full Range)")
    print(json.dumps(mem.get_cross_band_self_check_window_comparator(), indent=2, sort_keys=True))

    _divider("Cross-Band Window Comparator: Selection Mismatch")
    print(
        json.dumps(
            mem.get_cross_band_self_check_window_comparator(
                start_index=0,
                end_index=2,
                start_event_order=3,
                end_event_order=4,
            ),
            indent=2,
            sort_keys=True,
        )
    )

    _divider("Cross-Band Window Comparator: Availability Mismatch")
    print(
        json.dumps(
            mem.get_cross_band_self_check_window_comparator(
                start_index=3,
                end_index=1,
                start_event_order=1,
                end_event_order=4,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    run_cross_band_window_comparator_demo_v1_3()
