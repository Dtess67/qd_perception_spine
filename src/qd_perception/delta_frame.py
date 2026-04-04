from dataclasses import dataclass
from typing import Optional
from .sensor_event import SensorEvent

@dataclass
class DeltaFrame:
    """
    Represents the calculated difference between two sensor events.
    Focuses on change rather than absolute state.
    """
    source: str
    channel: str
    previous_value: Optional[float]
    current_value: float
    delta: float            # current_value - previous_value
    direction: str          # "rising", "falling", "steady", or "unknown"
    magnitude: float        # absolute value of the change
    rate: Optional[float]   # delta / dt (delta per unit of time)
    is_novel: bool          # True if this change is considered a significant first-time event

class DeltaCalculator:
    """
    Computes differences between the last known sensor state and the new incoming event.
    """
    # Threshold for considering a value 'steady' vs slightly noisy/drifting
    STEADY_THRESHOLD = 0.0001
    # Threshold for tagging a change as 'novel' (significant magnitude)
    NOVELTY_THRESHOLD = 5.0

    def compute(self, previous_event: Optional[SensorEvent], current_event: SensorEvent) -> DeltaFrame:
        """
        Derives a DeltaFrame by comparing the new event to the optional previous one.
        """
        source = current_event.source
        channel = current_event.channel
        current_val = current_event.value
        
        # Default starting values for the very first event
        if previous_event is None:
            return DeltaFrame(
                source=source,
                channel=channel,
                previous_value=None,
                current_value=current_val,
                delta=0.0,
                direction="unknown",
                magnitude=0.0,
                rate=None,
                is_novel=True # The first sight of a channel is inherently novel
            )

        # Calculate standard change metrics
        prev_val = previous_event.value
        delta = current_val - prev_val
        magnitude = abs(delta)
        
        # Determine direction
        if magnitude <= self.STEADY_THRESHOLD:
            direction = "steady"
        elif delta > 0:
            direction = "rising"
        else:
            direction = "falling"

        # Calculate rate (change per second) if time has elapsed
        dt = current_event.timestamp - previous_event.timestamp
        rate = (delta / dt) if dt > 0 else 0.0

        # Simple novelty rule: large jumps are novel
        is_novel = magnitude >= self.NOVELTY_THRESHOLD

        return DeltaFrame(
            source=source,
            channel=channel,
            previous_value=prev_val,
            current_value=current_val,
            delta=delta,
            direction=direction,
            magnitude=magnitude,
            rate=rate,
            is_novel=is_novel
        )
