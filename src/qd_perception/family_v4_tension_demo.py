from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

def run_tension_demo():
    print("--- Neutral Multi-Family Tension Demo v1 ---")
    memory = NeutralFamilyMemoryV1()
    
    # 1. Setup two families
    # fam_01: Stable Low
    sig_low = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    spr_low = {"axis_a": 0.02, "axis_b": 0.02, "axis_c": 0.02, "axis_d": 0.02}
    memory.join_or_create_family("sym_low_base", sig_low, spr_low, 10)
    print(f"Created fam_01: center at {sig_low['axis_a']:.2f}, spread {spr_low['axis_a']:.2f}")
    
    # fam_02: Stable High (Gap 0.4 > 0.25 HOLD_THRESHOLD)
    sig_high = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    spr_high = {"axis_a": 0.02, "axis_b": 0.02, "axis_c": 0.02, "axis_d": 0.02}
    memory.join_or_create_family("sym_high_base", sig_high, spr_high, 10)
    print(f"Created fam_02: center at {sig_high['axis_a']:.2f}, spread {spr_high['axis_a']:.2f}")
    
    # Scenario A: Clear Match
    print("\nScenario A: Clear Match (Symbol near fam_01)")
    sig_a = {"axis_a": 0.12, "axis_b": 0.12, "axis_c": 0.12, "axis_d": 0.12}
    # Persistence 1
    decision_a1 = memory.join_or_create_family("sym_a", sig_a, spr_low, 1)
    print(f"Observation 1: {decision_a1.status} - {decision_a1.rationale}")
    # Persistence 2
    decision_a2 = memory.join_or_create_family("sym_a", sig_a, spr_low, 1)
    print(f"Observation 2: {decision_a2.status} - {decision_a2.rationale}")
    
    # Scenario B: Multi-Family Tension
    print("\nScenario B: Multi-Family Tension (Symbol between fam_01 and fam_02)")
    sig_b = {"axis_a": 0.30, "axis_b": 0.30, "axis_c": 0.30, "axis_d": 0.30}
    # Distance to fam_01 (0.1) is 0.2
    # Distance to fam_02 (0.5) is 0.2
    # Margin 0.0 < 0.05 threshold
    decision_b = memory.join_or_create_family("sym_b", sig_b, spr_low, 1)
    print(f"Observation 1: {decision_b.status} - {decision_b.rationale}")
    
    # Scenario C: Decisive Margin (Symbol closer to fam_02)
    print("\nScenario C: Decisive Margin (Symbol much closer to fam_02)")
    sig_c = {"axis_a": 0.42, "axis_b": 0.42, "axis_c": 0.42, "axis_d": 0.42}
    # Distance to fam_02 (0.5) is 0.08
    # Distance to fam_01 (0.1) is 0.32 (outside HOLD_THRESHOLD)
    # No tension, just join fam_02
    # Persistence 1
    decision_c1 = memory.join_or_create_family("sym_c", sig_c, spr_high, 1)
    print(f"Observation 1: {decision_c1.status} - {decision_c1.rationale}")
    # Persistence 2
    decision_c2 = memory.join_or_create_family("sym_c", sig_c, spr_high, 1)
    print(f"Observation 2: {decision_c2.status} - {decision_c2.rationale}")
    
    # Scenario D: Clear No-Match
    print("\nScenario D: Clear No-Match (Isolated symbol)")
    sig_d = {"axis_a": 0.6, "axis_b": 0.6, "axis_c": 0.6, "axis_d": 0.6}
    decision_d = memory.join_or_create_family("sym_d", sig_d, spr_low, 1)
    print(f"Result: {decision_d.status} - {decision_d.rationale}")

    print("\n--- Final Family Audit ---")
    for fam_id in sorted(memory._families.keys()):
        record = memory.get_family_record(fam_id)
        print(f"Family {fam_id}: Members: {record.member_symbol_ids}")

if __name__ == "__main__":
    run_tension_demo()
