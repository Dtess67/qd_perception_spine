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
        signature = result.proto_concept.signature

        # 1. Axis A: Novelty / Unfamiliarity
        # Novel deltas or structurally novel signatures increase axis_a.
        axis_a = 0.0
        if result.delta_frame.is_novel:
            axis_a += 0.7
        if signature.novelty_code == 1:
            axis_a += 0.3
        
        # 2. Axis B: Magnitude / Intensity
        # Tied to structural magnitude band and delta magnitude.
        axis_b = 0.0
        magnitude_band_map = {0: 0.2, 1: 0.5, 2: 0.9}
        axis_b = magnitude_band_map.get(signature.magnitude_band_code, 0.0)
        # Add a small scaling for actual magnitude to differentiate within intensity bands
        axis_b += min(result.delta_frame.magnitude * 0.1, 0.1)

        # 3. Axis C: Trend Persistence / Pattern Stability
        # Structurally steady modes increase persistence.
        axis_c = 0.0
        if signature.change_mode_code == 0:
            axis_c += 0.8
        elif signature.change_mode_code == 1:
            axis_c += 0.4
            
        if (
            signature.change_mode_code == 0
            and signature.direction_code == 0
            and signature.novelty_code == 0
            and signature.resolution_code == 0
        ):
            axis_c += 0.2
            
        # 4. Axis D: Directional Disruption / Spike-like Sharpness
        # Spike-like structural modes increase disruption.
        axis_d = 0.0
        if signature.change_mode_code == 2:
            axis_d += 0.9
        if (
            signature.change_mode_code == 2
            and signature.direction_code in (-1, 1)
            and signature.resolution_code == 0
        ):
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
