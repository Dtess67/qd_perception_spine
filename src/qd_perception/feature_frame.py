from dataclasses import dataclass
from .delta_frame import DeltaFrame

@dataclass
class FeatureFrame:
    """
    Translates raw delta numbers into more qualitative categories.
    Adds a layer of abstraction suitable for pattern recognition.
    """
    source: str
    channel: str
    trend: str         # "rising", "falling", "steady", or "unknown"
    intensity: str     # "low", "medium", "high"
    pattern: str       # "spike", "drift", "steady", or "unknown"
    novelty: str       # "novel" or "familiar"

class FeatureExtractor:
    """
    Extracts high-level descriptive features from a DeltaFrame.
    Uses simple thresholds to categorize magnitude and pattern.
    """
    # Thresholds for intensity categorization
    INTENSITY_MED_THRESHOLD = 0.5
    INTENSITY_HIGH_THRESHOLD = 2.0
    # A magnitude above this is classified as a "spike"
    SPIKE_THRESHOLD = 3.0

    def from_delta(self, delta_frame: DeltaFrame) -> FeatureFrame:
        """
        Converts raw delta data into categorized feature labels.
        """
        # Trend is just a higher-level word for direction
        trend = delta_frame.direction
        
        # Categorize Intensity
        mag = delta_frame.magnitude
        if mag < self.INTENSITY_MED_THRESHOLD:
            intensity = "low"
        elif mag < self.INTENSITY_HIGH_THRESHOLD:
            intensity = "medium"
        else:
            intensity = "high"

        # Categorize Pattern
        if trend == "steady" or mag < 0.01:
            pattern = "steady"
        elif mag >= self.SPIKE_THRESHOLD:
            pattern = "spike"
        else:
            pattern = "drift"

        # Categorize Novelty
        novelty_str = "novel" if delta_frame.is_novel else "familiar"

        return FeatureFrame(
            source=delta_frame.source,
            channel=delta_frame.channel,
            trend=trend,
            intensity=intensity,
            pattern=pattern,
            novelty=novelty_str
        )
