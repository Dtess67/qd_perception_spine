"""
Demo for Cross-Band Evidence Review Summary v1.0 (get_cross_band_evidence_review_summary).

Shows:
- READY state on locked surface with evidence
- PARTIAL state when coverage is thin
- UNAVAILABLE state when required surfaces are missing
"""

import json
import os
import sys

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _divider(title: str) -> None:
    print("\n" + ("=" * 72))
    print(title)
    print("=" * 72)


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


def _seed_green_ledger(path: str) -> None:
    # Event 1: Fission with clear pressure signal
    _write_event(
        path,
        {
            "event_id": "cb_evt_01",
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
    # Event 2: Reunion with clear pressure signal
    _write_event(
        path,
        {
            "event_id": "cb_evt_02",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 2,
            "source_family_ids": ["fam_02", "fam_03"],
            "successor_family_ids": ["fam_04"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_02", "fam_03"], "PRESSURE_STRETCHED"),
                "post_event_pressure": _pressure_payload(["fam_04"], "PRESSURE_STABLE"),
            },
        },
    )


def run_cross_band_evidence_review_demo() -> None:
    ledger_path = "runs/family_v34_cross_band_evidence_review_demo.jsonl"
    if not os.path.exists("runs"):
        os.makedirs("runs")
    if os.path.exists(ledger_path):
        os.remove(ledger_path)
    _seed_green_ledger(ledger_path)

    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    result = mem.get_cross_band_evidence_review_summary()

    _divider("Cross-Band Evidence Review: Green Ledger")
    print(json.dumps(result, indent=2, sort_keys=True))

    _divider("Review Summary")
    print(f"  review_state:  {result['review_state']}")
    print(f"  review_reason: {result['review_reason']}")
    print(f"  auditable:     {result['evidence_scope']['total_auditable_events']}")
    print(f"  lock_state:    {result['evidence_scope']['stage_lock_state']}")

    _divider("Evidence Counts")
    for bucket, count in result["evidence_counts"].items():
        print(f"  {bucket}: {count}")

    _divider("Explanation Lines")
    for line in result["explanation_lines"]:
        print(f"  {line}")

    # Demonstrate UNAVAILABLE with empty ledger
    _divider("Cross-Band Evidence Review: Empty Ledger")
    empty_path = "runs/family_v34_cross_band_evidence_review_empty_demo.jsonl"
    if os.path.exists(empty_path):
        os.remove(empty_path)
    with open(empty_path, "w", encoding="utf-8"):
        pass
    mem_empty = NeutralFamilyMemoryV1(durable_ledger_path=empty_path)
    result_empty = mem_empty.get_cross_band_evidence_review_summary()
    print(f"  review_state:  {result_empty['review_state']}")
    print(f"  review_reason: {result_empty['review_reason']}")


if __name__ == "__main__":
    run_cross_band_evidence_review_demo()
