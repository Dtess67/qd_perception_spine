"""
Demo for persistent multi-family bridge and single-family edge detection.

Shows how symbols that repeatedly fall into tension or boundary zones
earn neutral persistent boundary statuses (FAMILY_BRIDGE, FAMILY_EDGE)
before or instead of joining a family.
"""

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

def run_demo():
    print("=== QD Neutral Family Bridge/Edge Demo (v1) ===")
    memory = NeutralFamilyMemoryV1()
    
    # 1. Setup two anchor families
    # Family A: low axes
    sig_a = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    # Family B: mid-high axes
    sig_b = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    spread = {"axis_a": 0.02, "axis_b": 0.02, "axis_c": 0.02, "axis_d": 0.02}
    
    print("\n[Setup] Minting two anchor families...")
    memory.join_or_create_family("sym_anchor_a", sig_a, spread, 10)
    memory.join_or_create_family("sym_anchor_b", sig_b, spread, 10)
    
    print(f"Family A: fam_01 (center ~0.1)")
    print(f"Family B: fam_02 (center ~0.5)")

    # 2. Scenario: Persistent Bridge
    # A symbol that lives right between them (~0.3)
    # Distance to A: 0.2, Distance to B: 0.2
    sig_bridge = {"axis_a": 0.3, "axis_b": 0.3, "axis_c": 0.3, "axis_d": 0.3}
    
    print("\n--- Scenario 1: Persistent Multi-Family Bridge ---")
    print(f"Target signature: {sig_bridge}")
    print("Status code: BRIDGE_PERSISTENCE_THRESHOLD = 3")
    
    for i in range(1, 5):
        decision = memory.join_or_create_family("sym_bridge_01", sig_bridge, spread, 1)
        status = memory.get_boundary_status("sym_bridge_01")
        print(f"Obs {i}: Status={decision.status}, Earned Status={status}")
        print(f"  Rationale: {decision.rationale}")

    # 3. Scenario: Persistent Edge
    # A symbol that lives in the borderline band of Family B
    # HOLD_THRESHOLD is 0.25. DISTANCE_THRESHOLD is 0.15.
    # We'll place it at distance 0.20 from Family B.
    # Center B is 0.5. Let's put this at 0.7.
    # Distance to B: |0.7 - 0.5| = 0.2 (between 0.15 and 0.25)
    sig_edge = {"axis_a": 0.7, "axis_b": 0.7, "axis_c": 0.7, "axis_d": 0.7}
    
    print("\n--- Scenario 2: Persistent Single-Family Edge ---")
    print(f"Target signature: {sig_edge}")
    print("Status code: EDGE_PERSISTENCE_THRESHOLD = 3")
    
    for i in range(1, 5):
        decision = memory.join_or_create_family("sym_edge_01", sig_edge, spread, 1)
        status = memory.get_boundary_status("sym_edge_01")
        print(f"Obs {i}: Status={decision.status}, Earned Status={status}")
        print(f"  Rationale: {decision.rationale}")

    # 4. Scenario: Resolution from Bridge to Family
    # A symbol starts as a bridge, then moves decisively toward one family.
    sig_moving = {"axis_a": 0.3, "axis_b": 0.3, "axis_c": 0.3, "axis_d": 0.3}
    print("\n--- Scenario 3: Bridge Resolution to Family ---")
    
    print("Observations 1-3: Establish Bridge status...")
    for i in range(1, 4):
        memory.join_or_create_family("sym_resolving", sig_moving, spread, 1)
    
    print(f"Current Earned Status: {memory.get_boundary_status('sym_resolving')}")
    
    print("\nObservation 4: Move decisively toward Family B (center ~0.5)...")
    sig_resolved = {"axis_a": 0.49, "axis_b": 0.49, "axis_c": 0.49, "axis_d": 0.49}
    # Persistence for join is 2.
    for i in range(4, 6):
        decision = memory.join_or_create_family("sym_resolving", sig_resolved, spread, 1)
        print(f"Obs {i}: Status={decision.status}, Family={decision.family_id}")
        print(f"  Rationale: {decision.rationale}")

    print("\nFinal Family Audit:")
    for fam_id in ["fam_01", "fam_02"]:
        record = memory.get_family_record(fam_id)
        print(f" {fam_id}: Members={record.member_symbol_ids}")

if __name__ == "__main__":
    run_demo()
