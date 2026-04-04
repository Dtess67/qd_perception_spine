"""
Demo for Cross-Band Self-Check Audit v1.0a patch.

Shows tightened directional classification and precedence:
- reunion + STABLE -> alignment observed
- reunion + STRETCHED -> partial
- reunion + UNCLEAR -> partial
- fission + STRETCHED -> partial
- topology-only contradiction signal does not harden to contradiction
- no directional evidence -> unavailable
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
            "event_id": "patch_evt_reunion_stable",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 1,
            "source_family_ids": ["fam_01", "fam_02"],
            "successor_family_ids": ["fam_03"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_01", "fam_02"], "PRESSURE_STABLE"),
                "post_event_pressure": _pressure_payload(["fam_03"], "PRESSURE_STABLE"),
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "patch_evt_reunion_stretched",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 2,
            "source_family_ids": ["fam_10", "fam_11"],
            "successor_family_ids": ["fam_12"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_10", "fam_11"], "PRESSURE_STRETCHED"),
                "post_event_pressure": _pressure_payload(["fam_12"], "PRESSURE_STABLE"),
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "patch_evt_reunion_unclear",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 3,
            "source_family_ids": ["fam_20", "fam_21"],
            "successor_family_ids": ["fam_22"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_20", "fam_21"], "PRESSURE_UNCLEAR"),
                "post_event_pressure": _pressure_payload(["fam_22"], "PRESSURE_STABLE"),
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "patch_evt_fission_stretched",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 4,
            "source_family_ids": ["fam_30"],
            "successor_family_ids": ["fam_31", "fam_32"],
            "pressure_snapshot": {
                "pre_event_pressure": _pressure_payload(["fam_30"], "PRESSURE_STRETCHED"),
                "post_event_pressure": _pressure_payload(["fam_31", "fam_32"], "PRESSURE_STABLE"),
            },
        },
    )
    _write_event(
        path,
        {
            "event_id": "patch_evt_no_directional",
            "event_type": "FAMILY_FISSION_V1",
            "event_order": 5,
            "source_family_ids": ["fam_40"],
            "successor_family_ids": ["fam_41", "fam_42"],
        },
    )
    _write_event(
        path,
        {
            "event_id": "patch_evt_topology_only",
            "event_type": "FAMILY_REUNION_V1",
            "event_order": 6,
            "source_family_ids": ["fam_50", "fam_51"],
            "successor_family_ids": ["fam_52"],
        },
    )


def run_cross_band_self_check_patch_demo_v1_0a() -> None:
    ledger_path = "runs/family_v28_cross_band_self_check_patch_demo.jsonl"
    if os.path.exists(ledger_path):
        os.remove(ledger_path)
    _seed_ledger(ledger_path)

    mem = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)

    _divider("Reunion + STABLE => Alignment")
    print(json.dumps(mem.get_transition_cross_band_self_check("patch_evt_reunion_stable"), indent=2, sort_keys=True))

    _divider("Reunion + STRETCHED => Partial")
    print(json.dumps(mem.get_transition_cross_band_self_check("patch_evt_reunion_stretched"), indent=2, sort_keys=True))

    _divider("Reunion + UNCLEAR => Partial")
    print(json.dumps(mem.get_transition_cross_band_self_check("patch_evt_reunion_unclear"), indent=2, sort_keys=True))

    _divider("Fission + STRETCHED => Partial")
    print(json.dumps(mem.get_transition_cross_band_self_check("patch_evt_fission_stretched"), indent=2, sort_keys=True))

    _divider("No Directional Evidence => Unavailable")
    print(json.dumps(mem.get_transition_cross_band_self_check("patch_evt_no_directional"), indent=2, sort_keys=True))

    mem_topology_only = NeutralFamilyMemoryV1(durable_ledger_path=ledger_path)

    def patched_topology(_event_id: str) -> dict:
        return {
            "event_id": "patch_evt_topology_only",
            "found": True,
            "topology_available": True,
            "topology_warnings": ["TOPOLOGY_COMPRESSION_RISK"],
            "event_identity": {
                "event_type": "FAMILY_REUNION_V1",
                "event_order": 6,
                "ledger_write_order": 6,
                "duplicate_event_id_count_in_ledger": 1,
            },
            "participants": {
                "source_family_ids": ["fam_50", "fam_51"],
                "successor_family_ids": ["fam_52"],
                "participant_family_ids": ["fam_50", "fam_51", "fam_52"],
            },
            "participant_topology": [
                {
                    "family_id": "fam_50",
                    "found": True,
                    "topology_available": True,
                    "shape_class": "SHAPE_DUAL_LOBE",
                    "compression_risk": True,
                }
            ],
            "compression_risk_family_ids": ["fam_50"],
        }

    mem_topology_only.get_transition_topology_audit = patched_topology
    _divider("Topology-Only Contradiction Signal => Partial (Not Hard Contradiction)")
    print(json.dumps(mem_topology_only.get_transition_cross_band_self_check("patch_evt_topology_only"), indent=2, sort_keys=True))


if __name__ == "__main__":
    run_cross_band_self_check_patch_demo_v1_0a()
