from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

def run_geometry_demo():
    print("=== Neutral Family Geometry v1 Demo ===")
    memory = NeutralFamilyMemoryV1()
    
    # 1. Create a tight family (small spread)
    print("\nScenario 1: Creating a tight structural family")
    sym_tight = "sym_tight_01"
    sig_tight = {"axis_a": 0.2, "axis_b": 0.2, "axis_c": 0.2, "axis_d": 0.2}
    spread_tight = {"axis_a": 0.02, "axis_b": 0.02, "axis_c": 0.02, "axis_d": 0.02}
    memory.join_or_create_family(sym_tight, sig_tight, spread_tight, 100)
    
    fam_1 = memory.get_family_record("fam_01")
    print(f"Family {fam_1.family_id} created with members: {fam_1.member_symbol_ids}")
    print(f"  Mint Center: {fam_1.mint_signature}")
    print(f"  Mint Spread: {fam_1.mint_spread}")
    
    # 2. Create a broad family (large spread)
    print("\nScenario 2: Creating a broad structural family")
    sym_broad = "sym_broad_01"
    sig_broad = {"axis_a": 0.7, "axis_b": 0.7, "axis_c": 0.7, "axis_d": 0.7}
    spread_broad = {"axis_a": 0.25, "axis_b": 0.25, "axis_c": 0.25, "axis_d": 0.25}
    memory.join_or_create_family(sym_broad, sig_broad, spread_broad, 100)
    
    fam_2 = memory.get_family_record("fam_02")
    print(f"Family {fam_2.family_id} created with members: {fam_2.member_symbol_ids}")
    print(f"  Mint Center: {fam_2.mint_signature}")
    print(f"  Mint Spread: {fam_2.mint_spread}")
    
    # 3. Test symbol near tight family center but outside envelope
    print("\nScenario 3: Symbol near tight family center but outside its envelope")
    sym_near = "sym_near_01"
    # Distance is 0.05, which is < DISTANCE_THRESHOLD (0.15) but > avg spread (0.02)
    sig_near = {"axis_a": 0.25, "axis_b": 0.25, "axis_c": 0.25, "axis_d": 0.25}
    spread_near = {"axis_a": 0.02, "axis_b": 0.02, "axis_c": 0.02, "axis_d": 0.02}
    
    decision = memory.evaluate_symbol(sym_near, sig_near, spread_near)
    print(f"Decision for {sym_near}: {decision.status}")
    print(f"Rationale: {decision.rationale}")
    
    # 4. Evolution of family geometry on join
    print("\nScenario 4: Joining symbols and evolving family geometry")
    # sym_near joins fam_01 after persistence
    for i in range(1, memory.JOIN_PERSISTENCE_THRESHOLD + 1):
        decision = memory.join_or_create_family(sym_near, sig_near, spread_near, 50)
        print(f"  Observation {i}: {decision.status} ({decision.family_id})")
        
    fam_1_evolved = memory.get_family_record("fam_01")
    print(f"Family {fam_1_evolved.family_id} members: {fam_1_evolved.member_symbol_ids}")
    print(f"  Mint Center (Anchor):    {fam_1_evolved.mint_signature}")
    print(f"  Current Center (Live):   {fam_1_evolved.current_signature}")
    print(f"  Mint Spread (Anchor):    {fam_1_evolved.mint_spread}")
    print(f"  Current Spread (Live):   {fam_1_evolved.current_spread}")
    print(f"  Total Observations:      {fam_1_evolved.observation_count}")

if __name__ == "__main__":
    run_geometry_demo()
