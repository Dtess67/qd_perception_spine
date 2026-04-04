"""
Demo of the glyph-earning process for stable structural patterns in the QD perception spine.
Shows how repeated similar sensory sequences can stabilize into a neutral glyph.
"""

import sys
import os

# Ensure we can import from src
sys.path.append(os.path.join(os.getcwd(), "src"))

from qd_perception.simulated_sources import (
    rising_light_sequence,
    touch_spike_sequence,
    falling_temperature_sequence
)
from qd_perception.perception_pipeline import PerceptionPipeline
from qd_perception.neutral_state_vector import NeutralStateMapper
from qd_perception.pattern_family_analyzer import (
    PatternFamilyAnalyzer,
    PatternPlacement
)

def run_family_simulation(analyzer, pipeline, mapper, scenario_gen, family_id, repeat_count=3):
    """
    Simulates a sensory scenario multiple times and records the resulting 
    structural placements into a family for analysis.
    """
    print(f"\n--- Simulating Family: {family_id} ({repeat_count} runs) ---")
    
    for r in range(repeat_count):
        scenario_name = f"{family_id}_run_{r+1}"
        events = scenario_gen()
        previous_event = None
        
        # We only care about the 'final' or most significant state of the sequence 
        # for this simple stabilization demo.
        last_placement = None
        
        for i, current_event in enumerate(events):
            result = pipeline.run(previous_event, current_event)
            vector = mapper.map(result)
            
            last_placement = PatternPlacement(
                scenario_name=scenario_name,
                event_index=i,
                region_id=vector.region_id,
                axis_a=vector.axis_a,
                axis_b=vector.axis_b,
                axis_c=vector.axis_c,
                axis_d=vector.axis_d
            )
            previous_event = current_event
        
        # Record the placement from the end of the sequence
        if last_placement:
            analyzer.record_placement(family_id, last_placement)
            print(f" Run {r+1} completed: Landed in {last_placement.region_id}")

def main():
    pipeline = PerceptionPipeline()
    mapper = NeutralStateMapper()
    analyzer = PatternFamilyAnalyzer()

    # 1. Repeated Gradual Rise (Light) - Should stabilize
    run_family_simulation(
        analyzer, pipeline, mapper, 
        rising_light_sequence, 
        "family_gradual_rise", 
        repeat_count=4
    )

    # 2. Repeated Spike (Touch) - Should stabilize
    run_family_simulation(
        analyzer, pipeline, mapper, 
        touch_spike_sequence, 
        "family_spike", 
        repeat_count=3
    )

    # 3. Repeated Stable Signal (Temp) - Should stabilize
    # We'll use falling temperature but only the first few events which are often stable 
    # or just create a custom stable one if needed. 
    # Actually falling_temperature is gradual, let's just use it and see.
    run_family_simulation(
        analyzer, pipeline, mapper, 
        falling_temperature_sequence, 
        "family_stable", 
        repeat_count=3
    )

    # 4. Mixed/Noisy Family - Should NOT stabilize
    print("\n--- Simulating Family: family_mixed_noise (3 runs) ---")
    # Manually inject scattered placements
    mixed_family = "family_mixed_noise"
    analyzer.record_placement(mixed_family, PatternPlacement(
        "mixed_run_1", 0, "region_steady_low", 0.1, 0.1, 0.1, 0.1
    ))
    analyzer.record_placement(mixed_family, PatternPlacement(
        "mixed_run_2", 0, "region_spike_high", 0.9, 0.9, 0.1, 0.9
    ))
    analyzer.record_placement(mixed_family, PatternPlacement(
        "mixed_run_3", 0, "region_shift_mid", 0.5, 0.5, 0.5, 0.5
    ))
    print(" Mixed runs completed (forced variance)")

    # Summarize Results
    print("\n" + "="*60)
    print("PATTERN FAMILY STABILITY & GLYPH EARNING AUDIT")
    print("="*60)

    families = ["family_gradual_rise", "family_spike", "family_stable", "family_mixed_noise"]
    
    for f_id in families:
        summary = analyzer.summarize_family(f_id)
        print(f"\nFamily ID:         {summary.family_id}")
        print(f"Dominant Region:   {summary.dominant_region_id}")
        print(f"Placement Count:   {summary.placement_count}")
        print(f"Stability Score:   {summary.stability_score:.2f}")
        
        glyph_display = summary.glyph_id if summary.glyph_id else "NOT YET EARNED"
        print(f"Glyph ID:          {glyph_display}")
        print(f"Rationale:         {summary.rationale}")
        print("-" * 40)

if __name__ == "__main__":
    main()
