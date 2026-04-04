# tests/test_state_adapter.py
# Tests for the CandidateState to FieldState adapter.

import pytest
from qd_perception.perception_to_state import CandidateState
from qd_perception.state_adapter import adapt_to_field_state_payload

def test_adapter_basic_mapping():
    """
    Verifies that a CandidateState maps correctly to the expected payload shape.
    """
    candidate = CandidateState(
        truth_state=1,
        uncertainty=0.2,
        harm_risk=0.1,
        action_tendency=1,
        emotional_weight=0.8,
        evidence_level=0.9,
        domain="test_source",
        rationale="Test rationale"
    )
    
    payload = adapt_to_field_state_payload(candidate)
    
    assert payload["truth_state"] == 1
    assert payload["uncertainty"] == 0.2
    assert payload["harm_risk"] == 0.1
    assert payload["action_tendency"] == 1
    assert payload["emotional_weight"] == 0.8
    assert payload["evidence_level"] == 0.9
    assert payload["domain"] == "test_source"

def test_adapter_clamping():
    """
    Verifies that the adapter clamps out-of-range values.
    """
    candidate = CandidateState(
        truth_state=5,         # Should clamp to 1
        uncertainty=1.5,       # Should clamp to 1.0
        harm_risk=-0.5,        # Should clamp to 0.0
        action_tendency=-10,   # Should clamp to -1
        emotional_weight=2.0,  # Should clamp to 1.0
        evidence_level=-1.0,   # Should clamp to 0.0
        domain=None,
        rationale="Out of bounds test"
    )
    
    payload = adapt_to_field_state_payload(candidate)
    
    assert payload["truth_state"] == 1
    assert payload["uncertainty"] == 1.0
    assert payload["harm_risk"] == 0.0
    assert payload["action_tendency"] == -1
    assert payload["emotional_weight"] == 1.0
    assert payload["evidence_level"] == 0.0
    assert payload["domain"] is None

def test_adapter_types():
    """
    Verifies that the adapter ensures correct types (int for discrete, float for ranges).
    """
    candidate = CandidateState(
        truth_state=0,
        uncertainty=0,        # Int input
        harm_risk=1,          # Int input
        action_tendency=0,
        emotional_weight=0.5,
        evidence_level=0.5,
        domain="safety",
        rationale="Type test"
    )
    
    payload = adapt_to_field_state_payload(candidate)
    
    assert isinstance(payload["truth_state"], int)
    assert isinstance(payload["action_tendency"], int)
    assert isinstance(payload["uncertainty"], float)
    assert isinstance(payload["harm_risk"], float)
