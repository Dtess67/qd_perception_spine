from dataclasses import dataclass
from typing import Optional
from .perception_pipeline import PerceptionResult

@dataclass
class CandidateState:
    """
    Represents a pre-expression candidate internal state derived from perception.
    This state captures the system's posture (uncertainty, risk, evidence) 
    before it is translated into human-readable language.
    """
    truth_state: int             # -1, 0, +1 (conclusion posture)
    uncertainty: float           # 0.0 to 1.0 (epistemic confidence)
    harm_risk: float             # 0.0 to 1.0 (safety posture)
    action_tendency: int         # -1 inhibit, 0 hold, +1 act (behavioral posture)
    emotional_weight: float      # 0.0 to 1.0 (signal intensity/urgency)
    evidence_level: float        # 0.0 to 1.0 (data sufficiency)
    domain: Optional[str]        # "general", "safety", etc.
    rationale: str               # Why this state was chosen

class PerceptionStateMapper:
    """
    Translates a PerceptionResult into a CandidateState.
    This bridge converts structural features of perception (change, intensity, pattern)
    into the internal parameters used by the expression system.
    """

    def map(self, result: PerceptionResult) -> CandidateState:
        """
        Maps a PerceptionResult to a CandidateState using deterministic rules.
        Focuses on internal posture rather than linguistic conclusion.
        """
        status_code = result.status_code
        feature = result.feature_frame
        concept = result.proto_concept
        
        # Default neutral posture
        truth_state = 0
        uncertainty = 0.5
        harm_risk = 0.1
        action_tendency = 0
        emotional_weight = 0.2
        evidence_level = 0.5
        domain = feature.source  # Use sensor source as initial domain
        
        rationale_parts = [f"Mapped from perception status: {status_code}."]

        # Mapping based on status_code and features
        if status_code == "FIRST_EVENT":
            truth_state = 0
            uncertainty = 0.9      # Very high uncertainty for first data point
            harm_risk = 0.1
            action_tendency = 0    # Hold
            emotional_weight = 0.3
            evidence_level = 0.1   # Very low evidence
            rationale_parts.append("Initial sensor contact: high uncertainty, minimal evidence.")

        elif status_code == "GRADUAL_SHIFT":
            truth_state = 0
            uncertainty = 0.5
            harm_risk = 0.1
            action_tendency = 0
            emotional_weight = 0.5 # Moderate intensity
            evidence_level = 0.6   # Moderate evidence as trend emerges
            rationale_parts.append("Detecting gradual change: monitoring trend with moderate evidence.")

        elif status_code == "SUDDEN_RISE":
            truth_state = 0
            uncertainty = 0.8      # High uncertainty due to spike
            harm_risk = 0.6        # Elevated risk from sudden change
            action_tendency = -1   # Inhibit/Caution
            emotional_weight = 0.9 # High intensity
            evidence_level = 0.7   # High local evidence of change
            rationale_parts.append("Sudden upward spike detected: high intensity, elevated harm risk, inhibiting action.")

        elif status_code == "SUDDEN_DROP":
            truth_state = 0
            uncertainty = 0.8      # High uncertainty
            harm_risk = 0.4        # Moderate risk
            action_tendency = 0    # Hold
            emotional_weight = 0.8 # High intensity
            evidence_level = 0.7   # High local evidence
            rationale_parts.append("Sudden downward drop detected: high intensity, monitoring for stability.")

        elif status_code == "STABLE_SIGNAL":
            truth_state = 0
            uncertainty = 0.1      # Low uncertainty
            harm_risk = 0.05       # Low risk
            action_tendency = 0
            emotional_weight = 0.1 # Low intensity
            evidence_level = 0.9   # High evidence of stability
            rationale_parts.append("Signal is stable and familiar: low uncertainty, high confidence in state.")

        elif status_code == "UNRESOLVED_PATTERN":
            truth_state = 0
            uncertainty = 0.95     # Extremely high uncertainty
            harm_risk = 0.3        # Potential risk from unknown pattern
            action_tendency = 0
            # Emotional weight varies by novelty/intensity
            emotional_weight = 0.6 if feature.novelty == "novel" else 0.3
            evidence_level = 0.2   # Low useful evidence
            rationale_parts.append("Unresolved or novel pattern: extremely high uncertainty, low evidence.")
        
        # Generic Success fallback if status_code doesn't match specific logic above
        else:
            rationale_parts.append("Generic successful perception mapping applied.")

        # Ensure values are within valid bounds
        clamped_uncertainty = max(0.0, min(1.0, uncertainty))
        clamped_harm_risk = max(0.0, min(1.0, harm_risk))
        clamped_emotional_weight = max(0.0, min(1.0, emotional_weight))
        clamped_evidence_level = max(0.0, min(1.0, evidence_level))
        
        # Ensure discrete values are within valid bounds
        valid_truth = max(-1, min(1, truth_state))
        valid_action = max(-1, min(1, action_tendency))

        return CandidateState(
            truth_state=valid_truth,
            uncertainty=clamped_uncertainty,
            harm_risk=clamped_harm_risk,
            action_tendency=valid_action,
            emotional_weight=clamped_emotional_weight,
            evidence_level=clamped_evidence_level,
            domain=domain,
            rationale=" ".join(rationale_parts)
        )
