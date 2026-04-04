from qd_perception.perception_pipeline import PerceptionPipeline
from qd_perception.simulated_sources import (
    rising_light_sequence,
    falling_temperature_sequence,
    touch_spike_sequence
)
from qd_perception.perception_to_state import PerceptionStateMapper
from qd_perception.neutral_state_vector import NeutralStateMapper
from qd_perception.symbol_memory import SymbolMemory

def run_comparison_demo():
    """
    Runs a comparison between the semantic (CandidateState) bridge and 
    the structural (NeutralStateVector) bridge across simulated sequences.
    
    This demo shows how the same sensory seed (PerceptionResult) is
    interpreted by two different internal mapping philosophies.
    """
    pipeline = PerceptionPipeline()
    state_mapper = PerceptionStateMapper()
    neutral_mapper = NeutralStateMapper()
    symbol_memory = SymbolMemory(hit_threshold=2, stability_threshold=0.6)
    
    scenarios = [
        ("Rising Light Sequence", rising_light_sequence()),
        ("Falling Temperature Sequence", falling_temperature_sequence()),
        ("Touch Spike Sequence", touch_spike_sequence())
    ]
    
    print("=" * 70)
    print(" QD PERCEPTION: BRIDGE COMPARISON DEMO ")
    print("=" * 70)
    print("Comparing Semantic (Authored) vs Structural (Neutral) interpretation layers.")
    print("=" * 70 + "\n")
    
    for name, events in scenarios:
        print(f"--- SCENARIO: {name} ---")
        previous_event = None
        
        for event in events:
            # 1. Process Event through Perception Pipeline
            result = pipeline.run(previous_event, event)
            
            # 2. Get interpretation from both bridges
            candidate_state = state_mapper.map(result)
            neutral_vector = neutral_mapper.map(result)
            
            # 3. Print Event Summary
            print(f"\n[EVENT] t={event.timestamp:.1f}s | val={event.value} | {result.status_code} - {result.status_label}")
            print(f"Concept: {result.proto_concept.name} | Rationale: {result.proto_concept.rationale}")
            
            # 4. Print Semantic Bridge interpretation
            print(f"  > [SEMANTIC BRIDGE] CandidateState:")
            print(f"    Posture: T={candidate_state.truth_state} | U={candidate_state.uncertainty:.2f} | H={candidate_state.harm_risk:.2f} | A={candidate_state.action_tendency}")
            print(f"    Rationale: {candidate_state.rationale}")
            
            # 5. Print Structural Bridge interpretation
            print(f"  > [STRUCTURAL BRIDGE] NeutralStateVector:")
            print(f"    Region: {neutral_vector.region_id} | A(Nov)={neutral_vector.axis_a:.2f} | B(Int)={neutral_vector.axis_b:.2f} | D(Shp)={neutral_vector.axis_d:.2f}")
            print(f"    Rationale: {neutral_vector.rationale}")
            
            # 6. Symbol Memory check (Neutral Lane)
            # Use a dummy stability score for this demo based on axis_c (pattern stability)
            stability_score = neutral_vector.axis_c 
            memory_entry = symbol_memory.observe(neutral_vector.region_id, stability_score, event_index=0)
            
            if memory_entry.symbol_id.startswith("sym_"):
                print(f"  > [SYMBOL EARNED] {memory_entry.symbol_id} (Stable)")
            else:
                print(f"  > [SYMBOL PENDING] No stable symbol yet for {neutral_vector.region_id}")

            # 7. Comparison Note
            # Explain the relationship between the two interpretation layers.
            if result.status_code == "FIRST_EVENT":
                note = "Semantic bridge maps toward communicative posture; neutral bridge maps toward structural region."
            elif "SPIKE" in neutral_vector.region_id or "RISE" in result.status_code:
                note = "Both bridges respond to magnitude disruption, but preserve different levels of interpretation."
            else:
                note = "Both arise from the same sensory seed but use different conceptual primitives."
            
            print(f"  [NOTE] {note}")
            
            previous_event = event
        
        print("\n" + "-" * 70)

    print("\n" + "=" * 70)
    print(" COMPARISON DEMO COMPLETE ")
    print("=" * 70)

if __name__ == "__main__":
    run_comparison_demo()
