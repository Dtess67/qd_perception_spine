from .sensor_event import SensorEvent

def rising_light_sequence():
    """
    Generates a sequence of light intensity events that gradually drift upward.
    """
    return [
        SensorEvent("light_sensor", "intensity", 0.0, 10.0, "lux", "optical"),
        SensorEvent("light_sensor", "intensity", 1.0, 11.5, "lux", "optical"),
        SensorEvent("light_sensor", "intensity", 2.0, 13.0, "lux", "optical"),
        SensorEvent("light_sensor", "intensity", 3.0, 14.5, "lux", "optical"),
    ]

def falling_temperature_sequence():
    """
    Generates a sequence of temperature events that gradually drift downward.
    """
    return [
        SensorEvent("temp_sensor", "ambient", 0.0, 25.0, "celsius", "thermal"),
        SensorEvent("temp_sensor", "ambient", 5.0, 24.0, "celsius", "thermal"),
        SensorEvent("temp_sensor", "ambient", 10.0, 23.0, "celsius", "thermal"),
    ]

def touch_spike_sequence():
    """
    Generates a sequence where a touch sensor experience a sudden sharp spike.
    """
    return [
        SensorEvent("touch_sensor", "pressure", 0.0, 0.1, "psi", "tactile"),
        SensorEvent("touch_sensor", "pressure", 0.1, 10.0, "psi", "tactile"), # Sudden Spike
        SensorEvent("touch_sensor", "pressure", 0.2, 10.1, "psi", "tactile"), # Steady at peak
    ]
