from qd_perception.sensor_event import SensorEvent
from qd_perception.delta_frame import DeltaCalculator

def test_first_event_behavior():
    """
    Ensures that the very first event in a sequence is handled as a baseline.
    """
    calc = DeltaCalculator()
    event = SensorEvent("test", "ch1", 10.0, 50.0)
    
    delta = calc.compute(None, event)
    
    assert delta.previous_value is None
    assert delta.delta == 0.0
    assert delta.direction == "unknown"
    assert delta.is_novel is True

def test_rising_delta():
    """
    Verifies that an upward change is correctly detected.
    """
    calc = DeltaCalculator()
    e1 = SensorEvent("test", "ch1", 0.0, 10.0)
    e2 = SensorEvent("test", "ch1", 1.0, 12.0)
    
    delta = calc.compute(e1, e2)
    
    assert delta.delta == 2.0
    assert delta.direction == "rising"
    assert delta.magnitude == 2.0
    assert delta.rate == 2.0 # 2 units / 1 sec

def test_falling_delta():
    """
    Verifies that a downward change is correctly detected.
    """
    calc = DeltaCalculator()
    e1 = SensorEvent("test", "ch1", 0.0, 20.0)
    e2 = SensorEvent("test", "ch1", 2.0, 15.0)
    
    delta = calc.compute(e1, e2)
    
    assert delta.delta == -5.0
    assert delta.direction == "falling"
    assert delta.magnitude == 5.0
    assert delta.rate == -2.5 # -5 units / 2 sec

def test_steady_threshold_behavior():
    """
    Ensures that very small changes are classified as 'steady' rather than rising/falling.
    """
    calc = DeltaCalculator()
    # Use a change smaller than STEADY_THRESHOLD (0.0001)
    e1 = SensorEvent("test", "ch1", 0.0, 10.0)
    e2 = SensorEvent("test", "ch1", 1.0, 10.00001)
    
    delta = calc.compute(e1, e2)
    
    assert delta.direction == "steady"
    assert delta.magnitude < calc.STEADY_THRESHOLD
