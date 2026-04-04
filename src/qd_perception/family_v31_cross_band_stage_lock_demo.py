"""
Demo for Cross-Band Consistency / Stage Lock v1.4.

Shows:
- stage-locked state on a green ledger
- lock on an empty ledger (honest unavailable handling)
- contract_surface and check_results shape
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
            "event_id": "cbsl_evt_01",
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
            "event_id": "cbsl_evt_02",
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
            "event_id": "cbsl_evt_03",
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
    # Event without pressure_snapshot — honest unavailable case
    _write_event(
        path,
        {
            "event_id": "cbsl_evt_04",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 4,
            "source_family_ids": ["fam_30"],
            "successor_family_ids": ["fam_31", "fam_32"],
        },
    )


def run_cross_band_stage_lock_demo_v1_4() -> None:
    ledger_path = "runs/family_v31_cross_band_stage_lock_demo.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)
    _seed_ledger(ledger_path)

    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)

    _divider("Cross-Band Stage Lock: Green Ledger")
    result = mem.get_cross_band_stage_lock_audit()
    print(json.dumps(result, indent=2, sort_keys=True))

    _divider("Cross-Band Stage Lock: Summary")
    print(f"  lock_state:    {result['lock_state']}")
    print(f"  checks_run:    {result['checks_run']}")
    print(f"  checks_passed: {result['checks_passed']}")
    print(f"  checks_failed: {result['checks_failed']}")
    for line in result["explanation_lines"]:
        print(f"  {line}")

    _divider("Cross-Band Stage Lock: Empty Ledger")
    empty_path = "runs/family_v31_cross_band_stage_lock_empty_demo.jsonl"
    if os.path.exists(empty_path):
        os.remove(empty_path)
    open(empty_path, "w").close()
    mem_empty = NeutralFamilyMemoryV1(durable_ledger_path=empty_path)
    result_empty = mem_empty.get_cross_band_stage_lock_audit()
    print(json.dumps(result_empty, indent=2, sort_keys=True))
    print(f"  lock_state: {result_empty['lock_state']}")


if __name__ == "__main__":
    run_cross_band_stage_lock_demo_v1_4()
