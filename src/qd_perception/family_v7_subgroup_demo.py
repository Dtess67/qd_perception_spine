import sys
import os

# Ensure src is in PYTHONPATH
sys.path.append(os.path.join(os.getcwd(), "src"))

from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

def print_divider(label: str):
    print(f"\n{'='*20} {label} {'='*20}")

def run_subgroup_demo():
    print("QD Perception: Internal Subgroup Detection v1 Demo")
    
    memory = NeutralFamilyMemoryV1()
    
    # 1. Coherent Single-Cloud Family
    print_divider("Scenario 1: Coherent Single-Cloud Family")
    # Small variations around a single center
    center_a = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    spread_v = {"axis_a": 0.05, "axis_b": 0.05, "axis_c": 0.05, "axis_d": 0.05}
    
    symbols = []
    for i in range(4):
        sig = {k: v + (0.02 * i) for k, v in center_a.items()}
        sym_id = f"sym_stable_{i}"
        # Symbols must earn join (threshold 2)
        for _ in range(2):
            memory.join_or_create_family(sym_id, sig, spread_v, 10)
        symbols.append(sym_id)
        
    record = memory.get_family_record("fam_01")
    print(f"Family: {record.family_id}")
    print(f"Members: {record.member_symbol_ids}")
    print(f"Subgroup Count: {record.subgroup_count}")
    print(f"Fracture Status: {record.fracture_status}")
    print(f"Rationale: Family remains coherent around a single center.")

    # 2. Broad but Still Single-Cloud Family
    print_divider("Scenario 2: Broad Single-Cloud Family")
    # Many symbols scattered widely but without distinct clusters
    memory_broad = NeutralFamilyMemoryV1()
    center_b = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    
    for i in range(10):
        # Scatter symbols in a uniform broad range
        # OFFSET MUST BE SMALLER THAN DISTANCE_THRESHOLD (0.15) or they won't join
        offset = (i % 5) * 0.03 # max 0.12
        sig = {k: v + offset for k, v in center_b.items()}
        # Must earn join
        for _ in range(2):
            memory_broad.join_or_create_family(f"sym_broad_{i}", sig, spread_v, 10)
        
    record_b = memory_broad.get_family_record("fam_01")
    print(f"Family: {record_b.family_id}")
    print(f"Subgroup Count: {record_b.subgroup_count}")
    print(f"Fracture Status: {record_b.fracture_status}")
    print(f"Rationale: Broad spread triggers FRACTURE_HOLD, but no dual-center detected yet.")

    # 3. Family with Two Persistent Internal Subgroups (Bifurcation)
    print_divider("Scenario 3: Dual-Center Internal Subgroups")
    memory_dual = NeutralFamilyMemoryV1()
    
    # Cluster 1 (far left)
    c1 = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    # Cluster 2 (far right)
    c2 = {"axis_a": 0.9, "axis_b": 0.9, "axis_c": 0.9, "axis_d": 0.9}
    
    # A central bridge to hold them together in one family for the demo
    bridge = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    
    print("-> Creating a bridge-based single family...")
    # Mint family with bridge
    memory_dual.join_or_create_family("sym_bridge", bridge, spread_v, 10)
    
    # Add c1 members (must be within DISTANCE_THRESHOLD 0.15 of family centroid or each other)
    # Actually, family centroid will move. Let's use a chain of symbols.
    
    # Bridge -> b1 (0.35) -> b2 (0.2) -> c1 (0.1)
    # Bridge -> b3 (0.65) -> b4 (0.8) -> c2 (0.9)
    
    chain = [0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]
    for val in chain:
        sig = {"axis_a": val, "axis_b": val, "axis_c": val, "axis_d": val}
        sym_id = f"sym_{val}"
        for _ in range(2): # Earn join
            memory_dual.join_or_create_family(sym_id, sig, spread_v, 10)
            
    print(f"Initial Members: {memory_dual.get_family_record('fam_01').member_symbol_ids}")

    # Now we have a very broad family. 
    # Let's see if we can detect the dual centers.
    # We need to observe the symbols multiple times to trigger SUBGROUP_PERSISTENCE_THRESHOLD=3
    
    print("-> Observing dual clusters multiple times...")
    for i in range(3):
        memory_dual.join_or_create_family("sym_0.1", {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}, spread_v, 10)
        memory_dual.join_or_create_family("sym_0.9", {"axis_a": 0.9, "axis_b": 0.9, "axis_c": 0.9, "axis_d": 0.9}, spread_v, 10)
        rec = memory_dual.get_family_record("fam_01")
        print(f"Hit {i+1}: Subgroup Evidence={rec.subgroup_evidence_counter}, Count={rec.subgroup_count}")

    record_dual = memory_dual.get_family_record("fam_01")
    print(f"Final Family: {record_dual.family_id}")
    print(f"Subgroup Count: {record_dual.subgroup_count}")
    print(f"Fracture Status: {record_dual.fracture_status}")
    print(f"Rationale: Persistence of two distinct internal centers triggers subgroup count=2.")

    print_divider("Demo Complete")

if __name__ == "__main__":
    run_subgroup_demo()
