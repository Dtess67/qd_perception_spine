from dataclasses import dataclass
from typing import Optional

@dataclass
class SensorEvent:
    """
    Represents a raw stimulus capture from a sensor at a specific point in time.
    This is the base input for the QD perception system.
    """
    source: str                 # Name of the physical or virtual sensor source
    channel: str                # Specific channel or sub-identifier (e.g. 'intensity', 'x', 'temp')
    timestamp: float            # Time of the event (usually seconds since start)
    value: float                # Raw numeric value of the sensor reading
    units: Optional[str] = None # Optional unit of measure (e.g. 'lux', 'celsius')
    event_type: Optional[str] = None # Optional classification (e.g. 'optical', 'thermal')
