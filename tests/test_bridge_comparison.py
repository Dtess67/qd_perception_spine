import pytest
from qd_perception.sensor_event import SensorEvent
from qd_perception.perception_pipeline import PerceptionPipeline
from qd_perception.perception_to_state import PerceptionStateMapper, CandidateState
from qd_perception.neutral_state_vector import NeutralStateMapper, NeutralStateVector

def test_bridge_comparison_harness():
    """
    Verifies that the same PerceptionResult can be processed by both bridges 
    independently and both return valid, non-colliding results.
    """
    pipeline = PerceptionPipeline()
    state_mapper = PerceptionStateMapper()
    neutral_mapper = NeutralStateMapper()
    
    # 1. Simulate a sudden spike event
    event1 = SensorEvent(source="touch", channel="t1", timestamp=1.0, value=0.1)
    event2 = SensorEvent(source="touch", channel="t1", timestamp=1.1, value=10.1) # Magnitude 10.0 jump

    # Process event
    result = pipeline.run(event1, event2)

    # 2. Process same result through both bridges
    candidate_state = state_mapper.map(result)
    neutral_vector = neutral_mapper.map(result)

    # 3. Assertions for CandidateState (Semantic Bridge)
    assert isinstance(candidate_state, CandidateState)
    assert candidate_state.truth_state == 0
    assert candidate_state.harm_risk >= 0.4 # SUDDEN_RISE usually elevates risk
    assert candidate_state.rationale is not None

    # 4. Assertions for NeutralStateVector (Structural Bridge)
    assert isinstance(neutral_vector, NeutralStateVector)
    assert neutral_vector.axis_b > 0.5 # High intensity
    assert neutral_vector.axis_d > 0.5 # Sharpness / spike
    assert neutral_vector.region_id != ""
    assert "spike" in neutral_vector.region_id.lower() or "high" in neutral_vector.region_id.lower()
    
    # 5. Independence check
    # Ensure changing one doesn't affect the other (they are different types, but good to be explicit)
    assert id(candidate_state) != id(neutral_vector)

def test_stable_bridge_comparison():
    """
    Verifies that a stable signal produces consistent and valid outputs from both bridges.
    """
    pipeline = PerceptionPipeline()
    state_mapper = PerceptionStateMapper()
    neutral_mapper = NeutralStateMapper()
    
    # 1. Repeated stable events
    event1 = SensorEvent(source="light", channel="l1", timestamp=1.0, value=10.0)
    event2 = SensorEvent(source="light", channel="l1", timestamp=2.0, value=10.0)
    
    result = pipeline.run(event1, event2)
    
    candidate_state = state_mapper.map(result)
    neutral_vector = neutral_mapper.map(result)
    
    # Semantic: STABLE_SIGNAL => Low uncertainty, high evidence
    assert candidate_state.uncertainty < 0.3
    assert candidate_state.evidence_level > 0.7
    
    # Structural: region_steady_low (low novelty/intensity/sharpness)
    assert neutral_vector.region_id == "region_steady_low"
    assert neutral_vector.axis_a <= 0.2 # Novelty
    assert neutral_vector.axis_b <= 0.2 # Intensity
    assert neutral_vector.axis_d <= 0.2 # Sharpness
