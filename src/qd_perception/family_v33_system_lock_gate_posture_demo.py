"""
Demo for System Lock Consumer Gate v1.1 (get_system_lock_gate_posture).

Shows:
- SYSTEM_GATE_LOCKED when umbrella lock is locked
- SYSTEM_GATE_UNAVAILABLE when umbrella lock is unavailable
- SYSTEM_GATE_INCONSISTENT when umbrella lock is inconsistent
- preserved system_stage_lock sub-audit
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
            "event_id": "gate_evt_01",
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


def run_system_lock_gate_posture_demo() -> None:
    ledger_path = "runs/family_v33_system_lock_gate_posture_demo.jsonl"
    if not os.path.exists("runs"):
        os.makedirs("runs")
    if os.path.exists(ledger_path):
        os.remove(ledger_path)
    _seed_green_ledger(ledger_path)

    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    result = mem.get_system_lock_gate_posture()

    _divider("System Lock Gate Posture: Green Ledger")
    print(json.dumps(result, indent=2, sort_keys=True))

    _divider("Gate Posture Summary")
    print(f"  gate_state:  {result['gate_state']}")
    print(f"  gate_reason: {result['gate_reason']}")
    print(f"  umbrella:    {result['system_stage_lock']['lock_state']}")

    _divider("Explanation Lines")
    for line in result["explanation_lines"]:
        print(f"  {line}")

    # Demonstrate UNAVAILABLE with empty ledger
    _divider("System Lock Gate Posture: Empty Ledger")
    empty_path = "runs/family_v33_system_lock_gate_posture_empty_demo.jsonl"
    if os.path.exists(empty_path):
        os.remove(empty_path)
    with open(empty_path, "w", encoding="utf-8"):
        pass
    mem_empty = NeutralFamilyMemoryV1(durable_ledger_path=empty_path)
    result_empty = mem_empty.get_system_lock_gate_posture()
    print(f"  gate_state:  {result_empty['gate_state']}")
    print(f"  gate_reason: {result_empty['gate_reason']}")
    print(f"  umbrella:    {result_empty['system_stage_lock']['lock_state']}")


if __name__ == "__main__":
    run_system_lock_gate_posture_demo()
