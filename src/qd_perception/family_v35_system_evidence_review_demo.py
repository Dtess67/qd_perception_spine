"""
Demo for System-Wide Evidence Review v1.1 (get_system_evidence_review_summary).

Shows:
- PARTIAL state on a healthy locked stack when observability evidence-review surface is absent
- UNAVAILABLE state when evidence is absent (empty ledger)
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
    _write_event(
        path,
        {
            "event_id": "sys_ev_01",
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
            "event_id": "sys_ev_02",
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


def run_system_evidence_review_demo() -> None:
    if not os.path.exists("runs"):
        os.makedirs("runs")

    green_path = "runs/family_v35_system_evidence_review_green_demo.jsonl"
    if os.path.exists(green_path):
        os.remove(green_path)
    _seed_green_ledger(green_path)

    mem = NeutralFamilyMemoryV1(durable_ledger_path=green_path)
    result = mem.get_system_evidence_review_summary()

    _divider("System-Wide Evidence Review: Green Ledger")
    print(json.dumps(result, indent=2, sort_keys=True))

    _divider("Review Summary")
    print(f"  review_state:  {result['review_state']}")
    print(f"  review_reason: {result['review_reason']}")
    print(f"  gate_state:    {result['evidence_scope']['system_gate_state']}")
    print(f"  auditable:     {result['evidence_counts']['total_auditable_events']}")

    empty_path = "runs/family_v35_system_evidence_review_empty_demo.jsonl"
    if os.path.exists(empty_path):
        os.remove(empty_path)
    with open(empty_path, "w", encoding="utf-8"):
        pass

    mem_empty = NeutralFamilyMemoryV1(durable_ledger_path=empty_path)
    empty_result = mem_empty.get_system_evidence_review_summary()

    _divider("System-Wide Evidence Review: Empty Ledger")
    print(f"  review_state:  {empty_result['review_state']}")
    print(f"  review_reason: {empty_result['review_reason']}")
    print(f"  auditable:     {empty_result['evidence_counts']['total_auditable_events']}")


if __name__ == "__main__":
    run_system_evidence_review_demo()
