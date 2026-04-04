import pytest
from qd_perception.sensor_event import SensorEvent
from qd_perception.perception_pipeline import PerceptionPipeline
from qd_perception.neutral_state_vector import NeutralStateMapper

def test_first_event_produces_valid_vector():
    pipeline = PerceptionPipeline()
    mapper = NeutralStateMapper()
    
    event = SensorEvent(source="light", channel="vis", timestamp=1.0, value=100.0)
    result = pipeline.run(None, event)
    
    vector = mapper.map(result)
    
    assert 0.0 <= vector.axis_a <= 1.0
    assert 0.0 <= vector.axis_b <= 1.0
    assert 0.0 <= vector.axis_c <= 1.0
    assert 0.0 <= vector.axis_d <= 1.0
    assert isinstance(vector.region_id, str)
    assert len(vector.region_id) > 0
    # First event should have high novelty (axis_a)
    assert vector.axis_a >= 0.7

def test_sudden_rise_impacts_axes():
    pipeline = PerceptionPipeline()
    mapper = NeutralStateMapper()
    
    e1 = SensorEvent(source="touch", channel="t1", timestamp=1.0, value=0.1)
    e2 = SensorEvent(source="touch", channel="t1", timestamp=1.1, value=50.0)
    
    _ = pipeline.run(None, e1)
    result = pipeline.run(e1, e2)
    
    vector = mapper.map(result)
    
    # Sudden rise should have high intensity (axis_b) and high disruption (axis_d)
    assert vector.axis_b > 0.6
    assert vector.axis_d > 0.7
    assert vector.region_id == "region_spike_high"

def test_stable_signal_impacts_axes():
    pipeline = PerceptionPipeline()
    mapper = NeutralStateMapper()
    
    e1 = SensorEvent(source="light", channel="vis", timestamp=1.0, value=100.0)
    e2 = SensorEvent(source="light", channel="vis", timestamp=2.0, value=100.0)
    
    _ = pipeline.run(None, e1)
    result = pipeline.run(e1, e2)
    
    vector = mapper.map(result)
    
    # Stable signal should have high stability (axis_c) and low disruption (axis_d)
    assert vector.axis_c > 0.7
    assert vector.axis_d < 0.3
    assert vector.region_id == "region_steady_low"

def test_different_regions_for_different_scenarios():
    pipeline = PerceptionPipeline()
    mapper = NeutralStateMapper()
    
    # Scenario 1: Spike
    spike_result = pipeline.run(
        SensorEvent(source="s", channel="c", timestamp=1.0, value=0.0),
        SensorEvent(source="s", channel="c", timestamp=1.1, value=10.0)
    )
    spike_vector = mapper.map(spike_result)
    
    # Scenario 2: Steady
    steady_result = pipeline.run(
        SensorEvent(source="s", channel="c", timestamp=1.0, value=10.0),
        SensorEvent(source="s", channel="c", timestamp=2.0, value=10.0)
    )
    steady_vector = mapper.map(steady_result)
    
    assert spike_vector.region_id != steady_vector.region_id

def test_axis_clamping():
    # We'll mock a result or use extreme values to force clamping if possible
    # but the mapper already uses min/max. We just verify the output is clamped.
    pipeline = PerceptionPipeline()
    mapper = NeutralStateMapper()
    
    e1 = SensorEvent(source="s", channel="c", timestamp=1.0, value=0.0)
    e2 = SensorEvent(source="s", channel="c", timestamp=1.1, value=1000000.0)
    
    result = pipeline.run(e1, e2)
    vector = mapper.map(result)
    
    assert vector.axis_a <= 1.0
    assert vector.axis_b <= 1.0
    assert vector.axis_c <= 1.0
    assert vector.axis_d <= 1.0
