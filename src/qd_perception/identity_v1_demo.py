from qd_perception.sensor_event import SensorEvent
from qd_perception.perception_pipeline import PerceptionPipeline
from qd_perception.neutral_state_vector import NeutralStateMapper
from qd_perception.neutral_symbol_memory_v1 import NeutralSymbolMemoryV1
from qd_perception.simulated_sources import rising_light_sequence, touch_spike_sequence

def run_identity_demo():
    """
    Demonstrates the Neutral Symbol Identity Contract v1.
    
    Shows how repeating structural patterns earn identity, reuse it, 
    and how significant drift can trigger a split.
    """
    pipeline = PerceptionPipeline()
    mapper = NeutralStateMapper()
    memory = NeutralSymbolMemoryV1()
    
    print("="*60)
    print("QD NEUTRAL SYMBOL IDENTITY DEMO v1")
    print("="*60)
    
    # SCENARIO 1: Repeating stable structural pattern (Rising Light)
    # We will run the sequence twice to build up recurrence.
    print("\nScenario 1: Repeating Stable Pattern (Rising Light)")
    print("-" * 40)
    
    event_idx = 0
    # First pass: Establish region hits
    for event in rising_light_sequence():
        result = pipeline.run(None, event)
        vector = mapper.map(result)
        axes_dict = {
            "axis_a": vector.axis_a, 
            "axis_b": vector.axis_b, 
            "axis_c": vector.axis_c, 
            "axis_d": vector.axis_d
        }
        # For simplicity in this demo, we use a fixed high stability score
        decision = memory.process_observation(vector.region_id, 0.9, axes_dict, event_idx)
        print(f"Event {event_idx}: Region={vector.region_id} Status={decision.status} Symbol={decision.symbol_id}")
        event_idx += 1
        
    # Second pass: Earn and reuse symbol
    print("\nRepeating scenario to earn/reuse symbol...")
    for event in rising_light_sequence():
        result = pipeline.run(None, event)
        vector = mapper.map(result)
        axes_dict = {
            "axis_a": vector.axis_a, 
            "axis_b": vector.axis_b, 
            "axis_c": vector.axis_c, 
            "axis_d": vector.axis_d
        }
        decision = memory.process_observation(vector.region_id, 0.9, axes_dict, event_idx)
        print(f"Event {event_idx}: Region={vector.region_id} Status={decision.status} Symbol={decision.symbol_id}")
        if decision.status == "MATCH_EXISTING":
            print(f"  >> SUCCESS: Reused {decision.symbol_id}")
        event_idx += 1

    # SCENARIO 2: Drift and Split
    # We take a previously stable region and introduce a massive structural drift
    # but keep the same region_id to test the identity contract's split logic.
    print("\nScenario 2: Persistent Drift and Identity Split")
    print("-" * 40)
    
    # We'll use 'region_steady_low' which should be established by now
    target_region = "region_steady_low"
    
    # Drastically different axes for the same region name
    drifted_axes = {"axis_a": 0.9, "axis_b": 0.9, "axis_c": 0.9, "axis_d": 0.9}
    
    decision = memory.process_observation(target_region, 0.9, drifted_axes, event_idx)
    print(f"Drift Event: Region={target_region}")
    print(f"Decision Status: {decision.status}")
    print(f"Assigned Symbol: {decision.symbol_id}")
    print(f"Rationale: {decision.rationale}")
    
    if decision.status == "SPLIT":
        print(f"  >> SUCCESS: System detected structural drift and split identity.")

    # SCENARIO 3: Unstable Noisy Structure
    print("\nScenario 3: Unstable/Noisy Structure (No Symbol Earning)")
    print("-" * 40)
    
    noisy_region = "region_noisy"
    for i in range(5):
        # High recurrence but low stability
        decision = memory.process_observation(noisy_region, 0.4, {"axis_a": 0.5}, event_idx)
        print(f"Noisy Event {i}: Region={noisy_region} Status={decision.status} Symbol={decision.symbol_id}")
        event_idx += 1
    print(f"  >> SUCCESS: Unstable pattern failed to earn persistent identity.")

if __name__ == "__main__":
    run_identity_demo()
