from qd_perception.perception_pipeline import PerceptionPipeline
from qd_perception.sensor_event import SensorEvent
from qd_perception.simulated_sources import (
    rising_light_sequence,
    touch_spike_sequence
)
from qd_perception.demo_export import serialize_result

def test_rising_light_sequence_analysis():
    """
    Ensures that the gradual shift in a rising light sequence is correctly identified.
    """
    pipeline = PerceptionPipeline()
    events = rising_light_sequence()
    previous = None
    
    concepts = []
    status_codes = []
    for event in events:
        result = pipeline.run(previous, event)
        concepts.append(result.proto_concept.name)
        status_codes.append(result.status_code)
        previous = event
    
    # In our sequence, we expect a gradual_shift after the first event
    assert "gradual_shift" in concepts
    assert concepts[1] == "gradual_shift"
    assert status_codes[1] == "GRADUAL_SHIFT"

def test_touch_spike_sequence_analysis():
    """
    Ensures that a sudden sharp increase in pressure is detected as a sudden_rise.
    """
    pipeline = PerceptionPipeline()
    events = touch_spike_sequence()
    
    # Event 0: baseline
    # Event 1: spike (0.1 to 10.0 = 9.9 delta)
    res0 = pipeline.run(None, events[0])
    res1 = pipeline.run(events[0], events[1])
    
    assert res1.feature_frame.trend == "rising"
    assert res1.feature_frame.intensity == "high"
    assert res1.feature_frame.pattern == "spike"
    assert res1.proto_concept.name == "sudden_rise"
    assert res1.status_code == "SUDDEN_RISE"

def test_steady_repeated_values():
    """
    Verifies that stable signals are identified correctly over time.
    """
    pipeline = PerceptionPipeline()
    e1 = SensorEvent("sensor", "ch", 0.0, 10.0)
    e2 = SensorEvent("sensor", "ch", 1.0, 10.0) # Identical
    
    res1 = pipeline.run(None, e1)
    res2 = pipeline.run(e1, e2)
    
    # e2 is familiar (not a large jump from e1) and steady
    assert res2.feature_frame.trend == "steady"
    assert res2.feature_frame.novelty == "familiar"
    assert res2.proto_concept.name == "stable_signal"
    assert res2.status_code == "STABLE_SIGNAL"

def test_pipeline_returns_full_structured_result():
    """
    Ensures that the pipeline returns all necessary layers of analysis.
    """
    pipeline = PerceptionPipeline()
    e1 = SensorEvent("sensor", "ch", 0.0, 10.0)
    
    result = pipeline.run(None, e1)
    
    assert result.event == e1
    assert result.delta_frame is not None
    assert result.feature_frame is not None
    assert result.proto_concept is not None
    assert result.status_code == "FIRST_EVENT"
    assert result.status_label is not None

def test_serialize_result_helper():
    """
    Verifies that the serialize_result helper correctly handles PerceptionResult.
    """
    pipeline = PerceptionPipeline()
    e1 = SensorEvent("sensor", "ch", 0.0, 10.0)
    result = pipeline.run(None, e1)
    
    serialized = serialize_result(result)
    assert isinstance(serialized, dict)
    assert serialized["status_code"] == "FIRST_EVENT"
    assert serialized["event"]["value"] == 10.0
    assert "delta_frame" in serialized
    assert "proto_concept" in serialized
