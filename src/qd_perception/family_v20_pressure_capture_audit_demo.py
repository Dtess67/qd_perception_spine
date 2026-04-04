"""
Demo for Pressure Capture Integrity / Replay Audit v1.3.

Shows:
- unavailable (event not found)
- unavailable (event without pressure_snapshot)
- valid pressure_snapshot audit
- invalid pressure_snapshot audit
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


def _seed_family(mem: NeutralFamilyMemoryV1, prefix: str, member_count: int) -> tuple[str, list[str]]:
    spread = _spr(0.05)
    members: list[str] = []
    for i in range(member_count):
        sid = f"{prefix}_{i}"
        members.append(sid)
        mem.join_or_create_family(sid, _sig(0.50), spread, 10)
        if i > 0:
            mem.join_or_create_family(sid, _sig(0.50), spread, 10)
    return "fam_01", members


def _append_invalid_event(ledger_path: str) -> str:
    event_id = "audit_invalid_evt_0001"
    record = {
        "event_id": event_id,
        "event_type": "FAMILY_FISSION_V1",
        "event_order": 9001,
        "source_family_ids": ["fam_90"],
        "successor_family_ids": ["fam_91", "fam_92"],
        "pressure_snapshot": {
            "pre_event_pressure": {
                "family_ids": ["fam_90"],
                "family_pressure_by_id": {"fam_90": {"pressure_state": "PRESSURE_STABLE"}},
            },
            "post_event_pressure": None,
            "capture_attempted": True,
            "capture_succeeded": True,
            "capture_mode": "EVENT_WRITE_TIME",
            "capture_reason": "PRESSURE_CAPTURE_FULL",
            "pre_capture_status_by_family": {"fam_90": "PRESSURE_CAPTURED"},
            "post_capture_status_by_family": {
                "fam_91": "PRESSURE_UNAVAILABLE",
                "fam_92": "PRESSURE_UNAVAILABLE",
            },
        },
    }
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return event_id


def _append_legacy_event_without_snapshot(ledger_path: str) -> str:
    event_id = "audit_legacy_evt_0001"
    record = {
        "event_id": event_id,
        "event_type": "FAMILY_REUNION_V1",
        "event_order": 9000,
        "source_family_ids": ["fam_80", "fam_81"],
        "successor_family_ids": ["fam_82"],
    }
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return event_id


def run_pressure_capture_audit_demo_v1_3() -> None:
    ledger_path = "runs/family_v20_pressure_capture_audit_demo.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)

    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)
    fam_id, members = _seed_family(mem, "sym_v20", 8)
    mem._execute_family_fission(fam_id, members[:4], members[4:], "demo valid capture audit")
    valid_event_id = mem.get_fission_events()[0]["event_id"]
    legacy_event_id = _append_legacy_event_without_snapshot(ledger_path)
    invalid_event_id = _append_invalid_event(ledger_path)

    _divider("Event Not Found")
    print(json.dumps(mem.get_transition_pressure_capture_audit("evt_missing_0001"), indent=2, sort_keys=True))

    _divider("Event Without pressure_snapshot")
    print(json.dumps(mem.get_transition_pressure_capture_audit(legacy_event_id), indent=2, sort_keys=True))

    _divider("Valid pressure_snapshot Audit")
    print(json.dumps(mem.get_transition_pressure_capture_audit(valid_event_id), indent=2, sort_keys=True))

    _divider("Invalid pressure_snapshot Audit")
    print(json.dumps(mem.get_transition_pressure_capture_audit(invalid_event_id), indent=2, sort_keys=True))


if __name__ == "__main__":
    run_pressure_capture_audit_demo_v1_3()
