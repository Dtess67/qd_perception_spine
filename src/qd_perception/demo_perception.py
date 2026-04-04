from qd_perception.perception_pipeline import PerceptionPipeline
from qd_perception.simulated_sources import (
    rising_light_sequence,
    falling_temperature_sequence,
    touch_spike_sequence
)
from qd_perception.demo_export import export_perception_runs, serialize_result
from qd_perception.perception_to_state import PerceptionStateMapper
from qd_perception.neutral_state_vector import NeutralStateMapper

def run_demo_sequence(name, events):
    """
    Helper to run a named sequence of events through the perception pipeline
    and return the results for audit exporting.
    """
    pipeline = PerceptionPipeline()
    state_mapper = PerceptionStateMapper()
    neutral_mapper = NeutralStateMapper()
    previous_event = None
    
    scenario_results = []
    
    print("=" * 60)
    print(f" SCENARIO: {name}")
    print("=" * 60)
    
    for event in events:
        result = pipeline.run(previous_event, event)
        
        # Display key info including status labels
        print(f"\n[EVENT] t={event.timestamp:.1f} s | val={event.value} {event.units or ''}")
        print(f"  Status: {result.status_code} - {result.status_label}")
        
        df = result.delta_frame
        print(f"  Delta: {df.delta:+.2f} ({df.direction}) | Rate: {df.rate or 0.0:+.2f}/s | Novel: {df.is_novel}")
        
        ff = result.feature_frame
        print(f"  Features: Trend={ff.trend}, Intensity={ff.intensity}, Pattern={ff.pattern}, Novelty={ff.novelty}")
        
        pc = result.proto_concept
        print(f"  CONCEPT: >> {pc.name} << (Conf: {pc.confidence:.2f})")
        print(f"  Rationale: {pc.rationale}")
        
        # Bridge to CandidateState
        state = state_mapper.map(result)
        print(f"  [STATE BRIDGE] CandidateState:")
        print(f"    Truth: {state.truth_state} | Uncertainty: {state.uncertainty:.2f} | Harm: {state.harm_risk:.2f}")
        print(f"    Action: {state.action_tendency} | Emotion: {state.emotional_weight:.2f} | Evidence: {state.evidence_level:.2f}")
        print(f"    Rationale: {state.rationale}")
        
        # Bridge to NeutralStateVector (Parallel Experiment)
        neutral_vector = neutral_mapper.map(result)
        print(f"  [NEUTRAL VECTOR] Region: {neutral_vector.region_id}")
        print(f"    A: {neutral_vector.axis_a:.2f} (Novelty) | B: {neutral_vector.axis_b:.2f} (Intensity)")
        print(f"    C: {neutral_vector.axis_c:.2f} (Stability) | D: {neutral_vector.axis_d:.2f} (Sharpness)")
        print(f"    Rationale: {neutral_vector.rationale}")
        
        # Store serialized data for export
        scenario_results.append({
            "event": serialize_result(event),
            "status_code": result.status_code,
            "status_label": result.status_label,
            "delta_frame": serialize_result(df),
            "feature_frame": serialize_result(ff),
            "proto_concept": serialize_result(pc),
            "candidate_state": serialize_result(state),
            "neutral_state_vector": serialize_result(neutral_vector)
        })
        
        previous_event = event
    
    return {
        "scenario_name": name,
        "input_events": [serialize_result(e) for e in events],
        "final_result": serialize_result(scenario_results[-1]) if scenario_results else None,
        "steps": scenario_results
    }

def main():
    """
    Main entry point for the perception demo.
    Executes several simulated sensor scenarios and exports the results.
    """
    print("--- QD PERCEPTION SPINE DEMO ---")
    print("Demonstrating the transformation of raw stimuli into pre-linguistic concepts.\n")
    
    all_scenarios = []
    
    # 1. Rising Light Sequence (Gradual Shift)
    all_scenarios.append(run_demo_sequence("Rising Light (Gradual)", rising_light_sequence()))
    
    # 2. Falling Temperature Sequence (Gradual Shift)
    all_scenarios.append(run_demo_sequence("Falling Temperature (Gradual)", falling_temperature_sequence()))
    
    # 3. Touch Spike Sequence (Sudden Rise)
    all_scenarios.append(run_demo_sequence("Tactile Spike (Sudden)", touch_spike_sequence()))
    
    # Export all scenarios to JSON
    export_perception_runs(all_scenarios)
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
