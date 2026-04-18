from dataclasses import dataclass
from .feature_frame import FeatureFrame

@dataclass(frozen=True)
class ProtoStructuralSignatureV1:
    """
    Structural intermediary contract for proto-concept outcomes.

    This signature is the authoritative control surface for downstream logic.
    Human-readable names are compatibility/debug metadata only.
    """
    direction_code: int       # -1 falling, 0 steady, +1 rising, 9 unknown
    change_mode_code: int     # 0 steady, 1 drift, 2 spike, 9 unresolved
    magnitude_band_code: int  # 0 low, 1 medium, 2 high
    novelty_code: int         # 0 familiar, 1 novel
    resolution_code: int      # 0 matched, 1 unresolved
    confidence: float

@dataclass
class ProtoConcept:
    """
    Represents a pre-linguistic mental 'token' or label assigned to a stimulus pattern.
    This acts as a bridge between raw sensory patterns and higher concepts.
    """
    signature: ProtoStructuralSignatureV1
    name: str           # Compatibility/debug label only; non-authoritative for control logic.
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

        direction_code = self._direction_code_for_trend(trend)
        magnitude_band_code = self._magnitude_code_for_intensity(intensity)
        novelty_code = self._novelty_code_for_value(novelty)

        # Pattern: Sudden upward spike
        if trend == "rising" and intensity == "high" and pattern == "spike":
            signature = ProtoStructuralSignatureV1(
                direction_code=1,
                change_mode_code=2,
                magnitude_band_code=2,
                novelty_code=novelty_code,
                resolution_code=0,
                confidence=0.9,
            )
            return ProtoConcept(
                signature=signature,
                name=self._bridge_name_for_signature(signature),
                confidence=signature.confidence,
                rationale=f"High-intensity spike detected ({trend})"
            )

        # Pattern: Sudden downward spike
        if trend == "falling" and intensity == "high" and pattern == "spike":
            signature = ProtoStructuralSignatureV1(
                direction_code=-1,
                change_mode_code=2,
                magnitude_band_code=2,
                novelty_code=novelty_code,
                resolution_code=0,
                confidence=0.9,
            )
            return ProtoConcept(
                signature=signature,
                name=self._bridge_name_for_signature(signature),
                confidence=signature.confidence,
                rationale=f"High-intensity spike detected ({trend})"
            )

        # Pattern: Stable background signal
        if trend == "steady" and novelty == "familiar":
            signature = ProtoStructuralSignatureV1(
                direction_code=0,
                change_mode_code=0,
                magnitude_band_code=magnitude_band_code,
                novelty_code=0,
                resolution_code=0,
                confidence=0.95,
            )
            return ProtoConcept(
                signature=signature,
                name=self._bridge_name_for_signature(signature),
                confidence=signature.confidence,
                rationale="Steady signal with familiar novelty"
            )

        # Pattern: Gradual movement
        if trend in ["rising", "falling"] and intensity == "medium" and pattern == "drift":
            signature = ProtoStructuralSignatureV1(
                direction_code=direction_code,
                change_mode_code=1,
                magnitude_band_code=1,
                novelty_code=novelty_code,
                resolution_code=0,
                confidence=0.7,
            )
            return ProtoConcept(
                signature=signature,
                name=self._bridge_name_for_signature(signature),
                confidence=signature.confidence,
                rationale=f"Medium-intensity {trend} drift detected"
            )

        # Default fallback
        signature = ProtoStructuralSignatureV1(
            direction_code=direction_code,
            change_mode_code=9,
            magnitude_band_code=magnitude_band_code,
            novelty_code=novelty_code,
            resolution_code=1,
            confidence=0.5,
        )
        return ProtoConcept(
            signature=signature,
            name=self._bridge_name_for_signature(signature),
            confidence=signature.confidence,
            rationale=f"Pattern ({trend}, {intensity}, {pattern}, {novelty}) not explicitly matched"
        )

    @staticmethod
    def _direction_code_for_trend(trend: str) -> int:
        if trend == "rising":
            return 1
        if trend == "falling":
            return -1
        if trend == "steady":
            return 0
        return 9

    @staticmethod
    def _magnitude_code_for_intensity(intensity: str) -> int:
        if intensity == "low":
            return 0
        if intensity == "medium":
            return 1
        if intensity == "high":
            return 2
        return 0

    @staticmethod
    def _novelty_code_for_value(novelty: str) -> int:
        return 1 if novelty == "novel" else 0

    @staticmethod
    def _bridge_name_for_signature(signature: ProtoStructuralSignatureV1) -> str:
        """
        Compatibility/debug-only naming derived from structural outcome.
        """
        if signature.resolution_code == 1 or signature.change_mode_code == 9:
            return "unresolved_pattern"

        if signature.change_mode_code == 2 and signature.magnitude_band_code == 2:
            if signature.direction_code == 1:
                return "sudden_rise"
            if signature.direction_code == -1:
                return "sudden_drop"

        if (
            signature.change_mode_code == 0
            and signature.direction_code == 0
            and signature.novelty_code == 0
        ):
            return "stable_signal"

        if (
            signature.change_mode_code == 1
            and signature.magnitude_band_code == 1
            and signature.direction_code in (-1, 1)
        ):
            return "gradual_shift"

        return "unresolved_pattern"
