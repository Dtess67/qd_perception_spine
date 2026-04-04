# src/qd_perception/state_adapter.py
# Adapter for converting CandidateState to expression-compatible FieldState payload.

from .perception_to_state import CandidateState

def adapt_to_field_state_payload(candidate: CandidateState) -> dict:
    """
    Converts a CandidateState from the perception spine into a dictionary
    matching the FieldState contract in qd_expression_spine.
    
    This is a deterministic handshake function that ensures values are
    clamped and mapped correctly before being passed to the expression pipeline.
    """
    
    # Simple explicit mapping of fields.
    # We return a dictionary because we don't want to import FieldState 
    # directly here to keep the modules decoupled at the logic level,
    # though the demo will use both.
    
    payload = {
        "truth_state": int(max(-1, min(1, candidate.truth_state))),
        "uncertainty": float(max(0.0, min(1.0, candidate.uncertainty))),
        "harm_risk": float(max(0.0, min(1.0, candidate.harm_risk))),
        "action_tendency": int(max(-1, min(1, candidate.action_tendency))),
        "emotional_weight": float(max(0.0, min(1.0, candidate.emotional_weight))),
        "evidence_level": float(max(0.0, min(1.0, candidate.evidence_level))),
        "domain": candidate.domain
    }
    
    return payload
