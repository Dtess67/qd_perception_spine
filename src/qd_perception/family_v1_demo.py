from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

def run_family_demo():
    print("="*60)
    print("QD NEUTRAL SYMBOL FAMILY FORMATION DEMO v1")
    print("="*60)
    print("This demo shows how neutral symbols earn higher-order family identities.")
    print("Rule: Symbols remain distinct. Families are higher-order structural kinship.")
    print("-" * 60)

    memory = NeutralFamilyMemoryV1()

    # 1. Create a stable baseline symbol
    print("\nScenario 1: First Stable Symbol (baseline)")
    sym_01_id = "sym_01"
    sym_01_sig = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    sym_01_spread = {"axis_a": 0.02, "axis_b": 0.02, "axis_c": 0.02, "axis_d": 0.02}
    
    decision1 = memory.join_or_create_family(sym_01_id, sym_01_sig, sym_01_spread, 10)
    print(f"Symbol: {sym_01_id}")
    print(f"Decision: {decision1.status}")
    print(f"Family ID: {decision1.family_id}")
    print(f"Rationale: {decision1.rationale}")

    # 2. Add a symbol that is structurally similar (joins family)
    print("\nScenario 2: Structurally Similar Symbol (joining family)")
    sym_02_id = "sym_02"
    sym_02_sig = {"axis_a": 0.53, "axis_b": 0.53, "axis_c": 0.53, "axis_d": 0.53}
    sym_02_spread = {"axis_a": 0.03, "axis_b": 0.03, "axis_c": 0.03, "axis_d": 0.03}
    
    decision2 = memory.join_or_create_family(sym_02_id, sym_02_sig, sym_02_spread, 5)
    print(f"Symbol: {sym_02_id}")
    print(f"Decision: {decision2.status}")
    print(f"Family ID: {decision2.family_id}")
    print(f"Rationale: {decision2.rationale}")

    # 3. Add a symbol that is structurally distant (starts new family)
    print("\nScenario 3: Structurally Distant Symbol (separate family)")
    sym_03_id = "sym_03"
    sym_03_sig = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    sym_03_spread = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
    
    decision3 = memory.join_or_create_family(sym_03_id, sym_03_sig, sym_03_spread, 8)
    print(f"Symbol: {sym_03_id}")
    print(f"Decision: {decision3.status}")
    print(f"Family ID: {decision3.family_id}")
    print(f"Rationale: {decision3.rationale}")

    # 4. Borderline case (uncertain/no merge)
    print("\nScenario 4: Borderline Structural Proximity (no family match)")
    # Threshold is 0.15. Let's try 0.20 distance
    sym_04_id = "sym_04"
    sym_04_sig = {"axis_a": 0.7, "axis_b": 0.7, "axis_c": 0.7, "axis_d": 0.7}
    sym_04_spread = {"axis_a": 0.05, "axis_b": 0.05, "axis_c": 0.05, "axis_d": 0.05}
    
    decision4 = memory.join_or_create_family(sym_04_id, sym_04_sig, sym_04_spread, 3)
    print(f"Symbol: {sym_04_id}")
    print(f"Decision: {decision4.status}")
    print(f"Family ID: {decision4.family_id}")
    print(f"Rationale: {decision4.rationale}")

    # Final Audit
    print("\n" + "="*60)
    print("FINAL NEUTRAL FAMILY AUDIT")
    print("="*60)
    for fam_id in ["fam_01", "fam_02", "fam_03"]:
        record = memory.get_family_record(fam_id)
        if record:
            print(f"\nFamily ID: {record.family_id}")
            print(f"Members: {record.member_symbol_ids}")
            print(f"Observation Count: {record.observation_count}")
            print(f"Combined Signature: {record.combined_signature}")
            print(f"Combined Spread: {record.combined_spread}")
    print("-" * 60)

if __name__ == "__main__":
    run_family_demo()
