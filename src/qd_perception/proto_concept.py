from dataclasses import dataclass
from .feature_frame import FeatureFrame

@dataclass
class ProtoConcept:
    """
    Represents a pre-linguistic mental 'token' or label assigned to a stimulus pattern.
    This acts as a bridge between raw sensory patterns and higher concepts.
    """
    name: str           # The label of the concept
    confidence: float   # 0.0 to 1.0 confidence in the classification
    rationale: str      # A brief description of why this label was chosen

class ProtoConceptAssigner:
    """
    Matches feature patterns to specific proto-concept labels.
    Uses simple deterministic rules.
    """
    def assign(self, feature_frame: FeatureFrame) -> ProtoConcept:
        """
        Determines the most likely ProtoConcept for a given set of features.
        """
        trend = feature_frame.trend
        intensity = feature_frame.intensity
        pattern = feature_frame.pattern
        novelty = feature_frame.novelty

        # Pattern: Sudden upward spike
        if trend == "rising" and intensity == "high" and pattern == "spike":
            return ProtoConcept(
                name="sudden_rise",
                confidence=0.9,
                rationale=f"High-intensity spike detected ({trend})"
            )

        # Pattern: Sudden downward spike
        if trend == "falling" and intensity == "high" and pattern == "spike":
            return ProtoConcept(
                name="sudden_drop",
                confidence=0.9,
                rationale=f"High-intensity spike detected ({trend})"
            )

        # Pattern: Stable background signal
        if trend == "steady" and novelty == "familiar":
            return ProtoConcept(
                name="stable_signal",
                confidence=0.95,
                rationale="Steady signal with familiar novelty"
            )

        # Pattern: Gradual movement
        if trend in ["rising", "falling"] and intensity == "medium" and pattern == "drift":
            return ProtoConcept(
                name="gradual_shift",
                confidence=0.7,
                rationale=f"Medium-intensity {trend} drift detected"
            )

        # Default fallback
        return ProtoConcept(
            name="unresolved_pattern",
            confidence=0.5,
            rationale=f"Pattern ({trend}, {intensity}, {pattern}, {novelty}) not explicitly matched"
        )
