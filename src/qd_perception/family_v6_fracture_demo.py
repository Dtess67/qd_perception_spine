"""
Demo for Family Split / Family Fracture v1 in qd_perception_spine.
This script demonstrates how a neutral structural family can earn fracture 
and split-ready statuses when its internal structural spread becomes too broad.
"""

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

def print_divider(label: str):
    print(f"\n{'='*70}")
    print(f" SCENARIO: {label}")
    print(f"{'='*70}")

def print_record(record):
    if not record:
        print("No record found.")
        return
    avg_spread = sum(record.current_spread.values()) / len(record.current_spread)
    print(f"Family ID: {record.family_id}")
    print(f"Members:   {record.member_symbol_ids}")
    print(f"Avg Spread: {avg_spread:.3f} (Max Coherence: 0.35)")
    print(f"Fracture Counter: {record.fracture_counter}")
    print(f"Fracture Status:  {record.fracture_status}")

def main():
    mem = NeutralFamilyMemoryV1()
    
    # 1. Coherent Family
    print_divider("Coherent Family (Stable Unity)")
    sig_center = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    tight_spread = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    
    print("-> sym_01 starts fam_01 (tight)")
    mem.join_or_create_family("sym_01", sig_center, tight_spread, 10)
    
    print("-> sym_02 joins fam_01 (tight)")
    mem.join_or_create_family("sym_02", sig_center, tight_spread, 10)
    mem.join_or_create_family("sym_02", sig_center, tight_spread, 10)
    
    print_record(mem.get_family_record("fam_01"))

    # 2. Fracture Hold
    print_divider("Fracture Hold (Internal Separation/Over-breadth)")
    print("-> sym_03 joins with VERY broad spread (0.8)")
    broad_spread = {"axis_a": 0.8, "axis_b": 0.8, "axis_c": 0.8, "axis_d": 0.8}
    
    # We use a slightly different signature to simulate drift/separation
    sig_drifting = {"axis_a": 0.55, "axis_b": 0.55, "axis_c": 0.55, "axis_d": 0.55}
    mem.join_or_create_family("sym_03", sig_drifting, broad_spread, 10)
    mem.join_or_create_family("sym_03", sig_drifting, broad_spread, 10)
    
    print_record(mem.get_family_record("fam_01"))

    # 3. Persistent Fracture -> Split Ready
    print_divider("Persistent Fracture -> Split Ready")
    print("-> More broad observations join...")
    
    # Observation 2
    mem.join_or_create_family("sym_04", sig_drifting, broad_spread, 10)
    mem.join_or_create_family("sym_04", sig_drifting, broad_spread, 10)
    print("After hit 2:")
    print_record(mem.get_family_record("fam_01"))
    
    # Observation 3 (FRACTURE_PERSISTENCE_THRESHOLD is 3)
    mem.join_or_create_family("sym_05", sig_drifting, broad_spread, 10)
    mem.join_or_create_family("sym_05", sig_drifting, broad_spread, 10)
    print("\nAfter hit 3 (Threshold almost reached):")
    print_record(mem.get_family_record("fam_01"))

    # Observation 4
    mem.join_or_create_family("sym_05", sig_drifting, broad_spread, 10)
    print("\nAfter hit 4 (Threshold reached):")
    print_record(mem.get_family_record("fam_01"))

    # 4. Recovery
    print_divider("Structural Recovery (Healing)")
    print("-> Adding many tight observations to reduce average spread")
    very_tight = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
    # Current hit count is 60 (sym_01:10, sym_02:20, sym_03:20, sym_04:20, sym_05:20)
    # Wait, sym_01:10, sym_02:20 (2 hits), sym_03:20, sym_04:20, sym_05:20 = 90
    # Actually join_or_create_family adds hit_count for each call.
    # sym_01: 10
    # sym_02: 10 + 10 = 20
    # sym_03: 10 + 10 = 20
    # sym_04: 10 + 10 = 20
    # sym_05: 10 + 10 = 20
    # Total: 90
    
    # We add 200 hits of very_tight
    mem.join_or_create_family("sym_06", sig_center, very_tight, 200)
    # _check_for_fracture is called once here. counter goes 3 -> 2
    mem.join_or_create_family("sym_06", sig_center, very_tight, 200)
    # counter goes 2 -> 1
    mem.join_or_create_family("sym_06", sig_center, very_tight, 200)
    # counter goes 1 -> 0
    mem.join_or_create_family("sym_06", sig_center, very_tight, 200)
    # counter goes 0 (remains 0)
    
    print_record(mem.get_family_record("fam_01"))

if __name__ == "__main__":
    main()
