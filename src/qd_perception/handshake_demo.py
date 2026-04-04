# src/qd_perception/handshake_demo.py
# Controlled handshake demo between qd_perception_spine and qd_expression_spine.

import os
import sys

# Ensure both spines are in the path for this demo.
# In a real environment, they might be installed as packages.
# For this demo, we assume we are running from qd_perception_spine/ with src added.
# We also need to add qd_expression_spine/src to the path if not already there.

# Add qd_expression_spine/src to path for this demo (adjust if needed)
expr_spine_src = os.path.abspath(os.path.join(os.getcwd(), "..", "qd_expression_spine", "src"))
if os.path.exists(expr_spine_src) and expr_spine_src not in sys.path:
    sys.path.append(expr_spine_src)

# Perception imports
from qd_perception.perception_pipeline import PerceptionPipeline
from qd_perception.perception_to_state import PerceptionStateMapper
from qd_perception.state_adapter import adapt_to_field_state_payload
from qd_perception.simulated_sources import (
    rising_light_sequence,
    falling_temperature_sequence,
    touch_spike_sequence
)

# Expression imports
try:
    from qd_expression.field_state import FieldState
    from qd_expression.expression_pipeline import ExpressionPipeline
except ImportError:
    print("Error: Could not import qd_expression components.")
    print(f"Looked in: {expr_spine_src}")
    print("Please ensure qd_expression_spine/src is available in the parent directory.")
    sys.exit(1)

def run_handshake_demo():
    """
    Runs several simulated sequences from perception, maps them to state,
    adapts them for expression, and runs the expression pipeline.
    """
    perception_pipe = PerceptionPipeline()
    state_mapper = PerceptionStateMapper()
    expression_pipe = ExpressionPipeline()
    
    scenarios = [
        ("Rising Light (Gradual Shift)", rising_light_sequence()),
        ("Falling Temperature (Cooling)", falling_temperature_sequence()),
        ("Touch Spike (Sudden Impact)", touch_spike_sequence()),
    ]
    
    for name, events in scenarios:
        print("\n" + "="*80)
        print(f" SCENARIO: {name}")
        print("="*80)
        
        previous_event = None
        
        for event in events:
            # 1. Run Perception Pipeline
            perception_result = perception_pipe.run(previous_event, event)
            previous_event = event
            
            # 2. Map to CandidateState (Pre-language posture)
            candidate_state = state_mapper.map(perception_result)
            
            # 3. Adapt to Expression FieldState
            payload = adapt_to_field_state_payload(candidate_state)
            field_state = FieldState(**payload)
            
            # 4. Run Expression Pipeline
            expression_result = expression_pipe.run(field_state)
            
            # 5. Output Results
            print(f"\n--- Event: {event.source}/{event.channel} val={event.value} ---")
            print(f"Perception Concept : {perception_result.proto_concept.name} (Status: {perception_result.status_code})")
            print(f"Internal Posture   : Unc={candidate_state.uncertainty:.2f}, Risk={candidate_state.harm_risk:.2f}, Evid={candidate_state.evidence_level:.2f}")
            print(f"Posture Rationale  : {candidate_state.rationale}")
            
            if expression_result.final_text:
                print(f"Selected Meaning   : {expression_result.atom_text} (Status: {expression_result.status_code})")
                print(f"Selected Phrase    : {expression_result.phrase_text}")
                print(f"FINAL OUTPUT       : \"{expression_result.final_text}\"")
            else:
                print(f"Expression Result  : BLOCKED or EMPTY (Status: {expression_result.status_code})")
                if expression_result.validation_errors:
                    print(f"Validation Errors  : {expression_result.validation_errors}")

def main():
    print("Starting QD Spine Handshake Demo...")
    print("Handshaking qd_perception_spine (v0.1.0) with qd_expression_spine (v0.6.1)")
    run_handshake_demo()
    print("\nHandshake demo completed.")

if __name__ == "__main__":
    main()
