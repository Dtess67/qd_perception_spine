"""
Demo for the Neutral Symbol Family Hold/Uncertainty Lane (v2).
Showcases borderline cases being held and persistence-based kinship earning.
"""

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

def run_demo():
    print("=== QD Neutral Symbol Family Hold Demo (v2) ===")
    memory = NeutralFamilyMemoryV1()
    
    # 1. Establish initial family (fam_01)
    print("\n[Scenario 1: Establish Initial Family]")
    sig_1 = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    spread_1 = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
    decision_1 = memory.join_or_create_family("sym_01", sig_1, spread_1, 10)
    print(f"Symbol sym_01: Status={decision_1.status}, Family={decision_1.family_id}")
    print(f"Rationale: {decision_1.rationale}")

    # 2. Borderline Case (Distance = 0.2, between 0.15 and 0.25)
    print("\n[Scenario 2: Borderline Kinship (Hold Band)]")
    sig_border = {"axis_a": 0.9, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1} # dist 0.2
    for i in range(1, 4):
        decision = memory.join_or_create_family("sym_border", sig_border, spread_1, 5)
        print(f"Observation {i} for sym_border: Status={decision.status}, Family={decision.family_id}")
        print(f"Rationale: {decision.rationale}")
    
    # 3. Near-miss earning join through persistence (Distance = 0.1, below 0.15)
    print("\n[Scenario 3: Persistence-based Kinship Earning]")
    sig_near = {"axis_a": 0.5, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1} # dist 0.1
    for i in range(1, 4):
        decision = memory.join_or_create_family("sym_near", sig_near, spread_1, 5)
        print(f"Observation {i} for sym_near: Status={decision.status}, Family={decision.family_id}")
        print(f"Rationale: {decision.rationale}")

    # 4. Clear Separation
    print("\n[Scenario 4: Clear Separation]")
    sig_far = {"axis_a": 0.9, "axis_b": 0.9, "axis_c": 0.9, "axis_d": 0.9} # dist 0.8
    decision_far = memory.join_or_create_family("sym_far", sig_far, spread_1, 5)
    print(f"Symbol sym_far: Status={decision_far.status}, Family={decision_far.family_id}")
    print(f"Rationale: {decision_far.rationale}")

    print("\n=== Final Family Audit ===")
    for fam_id in ["fam_01", "fam_02"]:
        record = memory.get_family_record(fam_id)
        if record:
            print(f"\nFamily: {fam_id}")
            print(f" - Members: {record.member_symbol_ids}")
            print(f" - Total Observations: {record.observation_count}")
            print(f" - Combined Signature: {record.combined_signature}")

if __name__ == "__main__":
    run_demo()
