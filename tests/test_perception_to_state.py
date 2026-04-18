import pytest
from qd_perception.sensor_event import SensorEvent
from qd_perception.perception_pipeline import PerceptionPipeline
from qd_perception.perception_to_state import PerceptionStateMapper, CandidateState

def test_first_event_mapping():
    """FIRST_EVENT should map to high uncertainty and low evidence."""
    pipeline = PerceptionPipeline()
    mapper = PerceptionStateMapper()
    
    event = SensorEvent(source="light", channel="lux", timestamp=1.0, value=100.0)
    result = pipeline.run(None, event)
    
    state = mapper.map(result)
    
    assert state.uncertainty >= 0.8
    assert state.evidence_level <= 0.2
    assert state.truth_state == 0
    assert "Initial sensor contact" in state.rationale

def test_sudden_rise_mapping():
    """SUDDEN_RISE should map to elevated harm and emotional weight."""
    pipeline = PerceptionPipeline()
    mapper = PerceptionStateMapper()
    
    event1 = SensorEvent(source="touch", channel="pressure", timestamp=1.0, value=10.0)
    event2 = SensorEvent(source="touch", channel="pressure", timestamp=1.1, value=100.0)
    
    _ = pipeline.run(None, event1)
    result = pipeline.run(event1, event2)
    
    state = mapper.map(result)
    
    assert result.status_code == "SUDDEN_RISE"
    assert state.harm_risk >= 0.5
    assert state.emotional_weight >= 0.8
    assert state.action_tendency == -1  # Inhibit due to high risk/spike
    assert "Sudden upward spike" in state.rationale

def test_stable_signal_mapping():
    """STABLE_SIGNAL should map to low uncertainty and high evidence."""
    pipeline = PerceptionPipeline()
    mapper = PerceptionStateMapper()
    
    event1 = SensorEvent(source="temp", channel="celsius", timestamp=1.0, value=20.0)
    event2 = SensorEvent(source="temp", channel="celsius", timestamp=2.0, value=20.0)
    
    _ = pipeline.run(None, event1)
    result = pipeline.run(event1, event2)
    
    state = mapper.map(result)
    
    assert result.status_code == "STABLE_SIGNAL"
    assert state.uncertainty <= 0.2
    assert state.evidence_level >= 0.8
    assert state.harm_risk <= 0.1

def test_unresolved_pattern_mapping():
    """UNRESOLVED_PATTERN should map to very high uncertainty."""
    pipeline = PerceptionPipeline()
    mapper = PerceptionStateMapper()
    
    # Create a situation that might lead to unresolved pattern or novel spike
    # Forcing it by mocking or just checking the logic if we can trigger it.
    # In current FeatureExtractor, high magnitude with first event is novel spike.
    # Let's try to get UNRESOLVED_PATTERN if possible, or just test the mapper logic directly.
    
    from qd_perception.delta_frame import DeltaFrame
    from qd_perception.feature_frame import FeatureFrame
    from qd_perception.proto_concept import ProtoConcept, ProtoStructuralSignatureV1
    from qd_perception.perception_pipeline import PerceptionResult
    
    mock_event = SensorEvent(source="unknown", channel="x", timestamp=1.0, value=50.0)
    mock_delta = DeltaFrame(source="unknown", channel="x", previous_value=40.0, current_value=50.0, 
                            delta=10.0, direction="rising", magnitude=10.0, rate=10.0, is_novel=True)
    mock_feature = FeatureFrame(source="unknown", channel="x", trend="rising", intensity="medium", 
                                pattern="drift", novelty="novel")
    mock_concept = ProtoConcept(
        signature=ProtoStructuralSignatureV1(
            direction_code=1,
            change_mode_code=9,
            magnitude_band_code=1,
            novelty_code=1,
            resolution_code=1,
            confidence=0.5,
        ),
        name="unresolved_pattern",
        confidence=0.5,
        rationale="Unknown",
    )
    
    result = PerceptionResult(
        event=mock_event,
        delta_frame=mock_delta,
        feature_frame=mock_feature,
        proto_concept=mock_concept,
        status_code="UNRESOLVED_PATTERN",
        status_label="Unresolved"
    )
    
    state = mapper.map(result)
    
    assert state.uncertainty >= 0.9
    assert state.evidence_level <= 0.3
    assert "Unresolved or novel pattern" in state.rationale

def test_numeric_ranges():
    """All mapped numeric values must remain in valid range [0, 1] or {-1, 0, 1}."""
    pipeline = PerceptionPipeline()
    mapper = PerceptionStateMapper()
    
    # Test across multiple simulated events
    event1 = SensorEvent(source="light", channel="lux", timestamp=1.0, value=0.0)
    event2 = SensorEvent(source="light", channel="lux", timestamp=2.0, value=1000.0) # Huge spike
    
    res1 = pipeline.run(None, event1)
    res2 = pipeline.run(event1, event2)
    
    for res in [res1, res2]:
        state = mapper.map(res)
        assert -1 <= state.truth_state <= 1
        assert 0.0 <= state.uncertainty <= 1.0
        assert 0.0 <= state.harm_risk <= 1.0
        assert -1 <= state.action_tendency <= 1
        assert 0.0 <= state.emotional_weight <= 1.0
        assert 0.0 <= state.evidence_level <= 1.0
