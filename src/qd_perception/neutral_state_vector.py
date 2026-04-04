from dataclasses import dataclass

@dataclass
class NeutralStateVector:
    """
    Represents a structurally neutral internal vector for the QD perception spine.
    Avoids early human-shaped categories like 'harm_risk' or 'uncertainty'.
    
    Fields:
    - axis_a: Responds mainly to novelty or unfamiliarity.
    - axis_b: Responds mainly to magnitude or intensity of stimulus.
    - axis_c: Responds mainly to trend persistence or pattern stability.
    - axis_d: Responds mainly to directional disruption or spike-like sharpness.
    - region_id: A simple label for the current area of the internal structure space.
    - rationale: A structural explanation of why this vector was assigned.
    """
    axis_a: float
    axis_b: float
    axis_c: float
    axis_d: float
    region_id: str
    rationale: str

class NeutralStateMapper:
    """
    Maps PerceptionResult outputs into a NeutralStateVector.
    
    This is an experimental parallel bridge designed to preserve structural 
    neutrality before later translation layers.
    """

    def map(self, result) -> NeutralStateVector:
        """
        Maps a PerceptionResult to a NeutralStateVector based on structural rules.
        """
        # 1. Axis A: Novelty / Unfamiliarity
        # Novel deltas or unresolved patterns increase axis_a.
        axis_a = 0.0
        if result.delta_frame.is_novel:
            axis_a += 0.7
        if result.feature_frame.novelty == "novel":
            axis_a += 0.3
        
        # 2. Axis B: Magnitude / Intensity
        # Directly tied to the intensity string and delta magnitude.
        axis_b = 0.0
        intensity_map = {"low": 0.2, "medium": 0.5, "high": 0.9}
        axis_b = intensity_map.get(result.feature_frame.intensity, 0.0)
        # Add a small scaling for actual magnitude to differentiate within intensity bands
        axis_b += min(result.delta_frame.magnitude * 0.1, 0.1)

        # 3. Axis C: Trend Persistence / Pattern Stability
        # 'steady' patterns or 'stable_signal' concepts increase axis_c.
        axis_c = 0.0
        if result.feature_frame.pattern == "steady":
            axis_c += 0.8
        elif result.feature_frame.pattern == "drift":
            axis_c += 0.4
            
        if result.proto_concept.name == "stable_signal":
            axis_c += 0.2
            
        # 4. Axis D: Directional Disruption / Spike-like Sharpness
        # 'spike' patterns or sudden concepts increase axis_d.
        axis_d = 0.0
        if result.feature_frame.pattern == "spike":
            axis_d += 0.9
        if "sudden" in result.proto_concept.name:
            axis_d += 0.1

        # Clamp all values to [0.0, 1.0]
        axis_a = max(0.0, min(1.0, axis_a))
        axis_b = max(0.0, min(1.0, axis_b))
        axis_c = max(0.0, min(1.0, axis_c))
        axis_d = max(0.0, min(1.0, axis_d))

        # Determine Region ID
        # A simple categorization based on axis levels.
        if axis_d > 0.7:
            region_id = "region_spike_high"
        elif axis_b > 0.6 and axis_c < 0.3:
            region_id = "region_shift_mid"
        elif axis_c > 0.7:
            region_id = "region_steady_low"
        else:
            region_id = "region_unresolved"

        # Construct Rationale
        parts = []
        if axis_a > 0.5: parts.append("high structural novelty")
        if axis_b > 0.5: parts.append("significant stimulus intensity")
        if axis_c > 0.5: parts.append("pattern stability detected")
        if axis_d > 0.5: parts.append("high directional disruption")
        
        if not parts:
            rationale = "Neutral baseline structural mapping."
        else:
            rationale = f"Structural fit based on: {', '.join(parts)}."

        return NeutralStateVector(
            axis_a=axis_a,
            axis_b=axis_b,
            axis_c=axis_c,
            axis_d=axis_d,
            region_id=region_id,
            rationale=rationale
        )
