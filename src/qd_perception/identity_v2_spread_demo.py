"""
Demo for qd_perception_spine: Structural Envelope (Spread) Awareness.
Shows how the system distinguishes between tight and loose pattern families 
even when they share the same structural center.
"""

from qd_perception.neutral_symbol_memory_v1 import NeutralSymbolMemoryV1

def print_record_envelope(record):
    """Prints a readable summary of a symbol's structural envelope."""
    print(f"--- Symbol: {record.symbol_id} (Region: {record.primary_region_id}) ---")
    print(f"  Hit Count: {record.hit_count}")
    print(f"  Mint Centroid: {record.mint_signature}")
    print(f"  Mint Spread (AAD): {record.mint_spread}")
    print(f"  Current Centroid: {record.current_signature}")
    print(f"  Current Spread: {record.current_spread}")
    print("")

def main():
    print("=== QD Neutral Symbol Envelope Demo (v2 Spread Patch) ===\n")
    memory = NeutralSymbolMemoryV1()
    
    # 1. Simulate a 'tight' pattern family
    # All observations are identical or very close to the center (0.5)
    print("Scenario 1: Stable, tight pattern family (low variation)")
    region_tight = "region_tight_01"
    tight_obs = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    
    for i in range(3):
        memory.process_observation(region_tight, 1.0, tight_obs, i)
    
    sym_tight_id = memory._region_to_symbol[region_tight]
    print_record_envelope(memory._records[sym_tight_id])
    
    # 2. Simulate a 'loose' pattern family
    # Observations are centered at 0.5 but vary significantly
    print("Scenario 2: Volatile but centered pattern family (high variation)")
    region_loose = "region_loose_01"
    loose_obs_list = [
        {"axis_a": 0.2, "axis_b": 0.8, "axis_c": 0.5, "axis_d": 0.5},
        {"axis_a": 0.8, "axis_b": 0.2, "axis_c": 0.5, "axis_d": 0.5},
        {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    ]
    
    for i, obs in enumerate(loose_obs_list):
        memory.process_observation(region_loose, 1.0, obs, i + 10)
        
    sym_loose_id = memory._region_to_symbol[region_loose]
    print_record_envelope(memory._records[sym_loose_id])
    
    # 3. Demonstrate spread updating
    print("Scenario 3: Updating envelope with new outlier observation")
    outlier = {"axis_a": 0.9, "axis_b": 0.1, "axis_c": 0.9, "axis_d": 0.9}
    print(f"Observing outlier for {sym_tight_id}...")
    memory.process_observation(region_tight, 1.0, outlier, 20)
    print_record_envelope(memory._records[sym_tight_id])
    
    print("Conclusion: Both symbols started with similar centroids, but their 'spread' "
          "captured the difference in their structural history.")

if __name__ == "__main__":
    main()
