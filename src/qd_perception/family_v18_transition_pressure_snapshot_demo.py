"""
Demo for Transition Pressure Snapshot v1.1.

Shows:
- event not found
- event found with no recoverable pressure snapshot
- partial recoverability
- full recoverability
"""

import json
import os

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1


def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _divider(title: str) -> None:
    print("\n" + ("=" * 72))
    print(title)
    print(("=" * 72))


def _emit_fission_and_reunion_chain(mem: NeutralFamilyMemoryV1) -> None:
    spread = _spr(0.05)
    for i in range(8):
        sid = f"sym_p_{i}"
        for _ in range(2):
            mem.join_or_create_family(sid, _sig(0.5 + (i * 0.01)), spread, 10)

    for _ in range(30):
        for i in range(3):
            mem.join_or_create_family(f"sym_p_{i}", _sig(0.1), spread, 10)
        for i in range(5, 8):
            mem.join_or_create_family(f"sym_p_{i}", _sig(0.9), spread, 10)
        if mem.get_fission_events():
            break

    fission_evt = mem.get_fission_events()[0]
    group_1 = list(fission_evt["partition"]["group_1_member_ids"])
    group_2 = list(fission_evt["partition"]["group_2_member_ids"])

    for _ in range(40):
        for sid in group_1:
            mem.join_or_create_family(sid, _sig(0.20), spread, 10)
        for sid in group_2:
            mem.join_or_create_family(sid, _sig(0.22), spread, 10)
        if mem.get_reunion_events():
            break


def _append_demo_snapshot_events(ledger_path: str) -> tuple[str, str]:
    partial_event_id = "snapshot_evt_partial_0001"
    full_event_id = "snapshot_evt_full_0001"
    partial_record = {
        "event_id": partial_event_id,
        "event_type": "FAMILY_REUNION_V1",
        "event_order": 9001,
        "source_family_ids": ["fam_20", "fam_21"],
        "successor_family_ids": ["fam_22"],
        "pressure_snapshot": {
            "post_event_pressure": {
                "family_pressure_by_id": {
                    "fam_22": {
                        "pressure_state": "PRESSURE_STABLE",
                        "scorecard": {
                            "diagnostic_scale": "0_to_1_comparative_not_probability",
                            "stability_index": 0.82,
                        },
                    }
                }
            }
        },
    }
    full_record = {
        "event_id": full_event_id,
        "event_type": "FAMILY_FISSION_V1",
        "event_order": 9002,
        "source_family_ids": ["fam_30"],
        "successor_family_ids": ["fam_31", "fam_32"],
        "pressure_snapshot": {
            "pre_event_pressure": {
                "family_pressure_by_id": {
                    "fam_30": {"pressure_state": "PRESSURE_FISSION_PRONE"}
                }
            },
            "post_event_pressure": {
                "family_pressure_by_id": {
                    "fam_31": {"pressure_state": "PRESSURE_STABLE"},
                    "fam_32": {"pressure_state": "PRESSURE_STRETCHED"},
                }
            },
        },
    }
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(partial_record, sort_keys=True, separators=(",", ":")) + "\n")
        f.write(json.dumps(full_record, sort_keys=True, separators=(",", ":")) + "\n")
    return partial_event_id, full_event_id


def run_transition_pressure_snapshot_demo_v1_1() -> None:
    ledger_path = "runs/family_transition_pressure_snapshot_demo_v1.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)

    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    _emit_fission_and_reunion_chain(mem)
    partial_event_id, full_event_id = _append_demo_snapshot_events(ledger_path)
    fission_event_id = mem.get_fission_events()[0]["event_id"]

    _divider("Unknown Event")
    print(json.dumps(mem.get_transition_pressure_snapshot("evt_missing_0001"), indent=2, sort_keys=True))

    _divider("Recorded Event Without Recoverable Snapshot")
    print(json.dumps(mem.get_transition_pressure_snapshot(fission_event_id), indent=2, sort_keys=True))

    _divider("Partial Recoverable Snapshot")
    print(json.dumps(mem.get_transition_pressure_snapshot(partial_event_id), indent=2, sort_keys=True))

    _divider("Full Recoverable Snapshot")
    print(json.dumps(mem.get_transition_pressure_snapshot(full_event_id), indent=2, sort_keys=True))


if __name__ == "__main__":
    run_transition_pressure_snapshot_demo_v1_1()
