import pytest
from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1,
    family_diag_confidence,
    family_last_tested,
    CAUSES,
    STEP_COUNTER,
    CAUSE_COMPLEXITY
)
import qd_perception.neutral_family_memory_v1 as nfm

def reset_curiosity_state():
    family_diag_confidence.clear()
    family_last_tested.clear()
    nfm.STEP_COUNTER = 0

def test_higher_confidence_wins_all_else_equal():
    reset_curiosity_state()
    fid = "F_CONF"
    # All complexity/recency equal (not tested yet)
    # EDGE_BAND_PROXIMITY: complexity 1
    # JOIN_PERSISTENCE: complexity 2
    # REUNION_FRICTION: complexity 3
    
    # Give higher confidence to a more complex cause to see if it overcomes simplicity
    family_diag_confidence[fid] = {
        "EDGE_BAND_PROXIMITY": 0.1,
        "JOIN_PERSISTENCE": 0.9,
        "REUNION_FRICTION": 0.0
    }
    
    memory = NeutralFamilyMemoryV1()
    cause, score, mode = memory._select_next_cause(fid, exclude=set())
    
    # Score calculation: (conf * 0.6) + (simplicity * 0.3) - (recent * 0.3)
    # EDGE: (0.1 * 0.6) + (1/1 * 0.3) = 0.06 + 0.3 = 0.36
    # JOIN: (0.9 * 0.6) + (1/2 * 0.3) = 0.54 + 0.15 = 0.69
    # JOIN should win despite being more complex
    assert cause == "JOIN_PERSISTENCE"
    assert mode == "FALSIFY" # It's the top cause

def test_simpler_cause_wins_when_confidences_equal():
    reset_curiosity_state()
    fid = "F_SIMPLE"
    family_diag_confidence[fid] = {
        "EDGE_BAND_PROXIMITY": 0.3,
        "JOIN_PERSISTENCE": 0.3,
        "REUNION_FRICTION": 0.3
    }
    
    memory = NeutralFamilyMemoryV1()
    cause, score, mode = memory._select_next_cause(fid, exclude=set())
    
    # EDGE simplicity = 1.0
    # JOIN simplicity = 0.5
    # REUNION simplicity = 0.33
    # EDGE should win
    assert cause == "EDGE_BAND_PROXIMITY"

def test_recently_tested_cause_is_penalized():
    reset_curiosity_state()
    fid = "F_RECENT"
    nfm.STEP_COUNTER = 10
    family_diag_confidence[fid] = {
        "EDGE_BAND_PROXIMITY": 0.5,
        "JOIN_PERSISTENCE": 0.5,
        "REUNION_FRICTION": 0.5
    }
    # Mark EDGE as recently tested (at step 9, current is 10)
    family_last_tested[fid] = {
        "EDGE_BAND_PROXIMITY": 9,
        "JOIN_PERSISTENCE": 0,
        "REUNION_FRICTION": 0
    }
    
    memory = NeutralFamilyMemoryV1()
    cause, score, mode = memory._select_next_cause(fid, exclude=set())
    
    # EDGE score will be penalized by 0.3
    # JOIN score = (0.5*0.6) + (0.5*0.3) = 0.3 + 0.15 = 0.45
    # EDGE score = (0.5*0.6) + (1.0*0.3) - 0.3 = 0.3 + 0.3 - 0.3 = 0.3
    # JOIN should win
    assert cause == "JOIN_PERSISTENCE"

def test_selector_returns_different_causes_across_steps():
    reset_curiosity_state()
    fid = "F_MULTI"
    family_diag_confidence[fid] = {
        "EDGE_BAND_PROXIMITY": 0.33,
        "JOIN_PERSISTENCE": 0.33,
        "REUNION_FRICTION": 0.34
    }
    
    memory = NeutralFamilyMemoryV1()
    
    # Step 1
    nfm.STEP_COUNTER = 1
    cause1, score1, mode1 = memory._select_next_cause(fid, exclude=set())
    family_last_tested[fid] = {c: -100 for c in CAUSES}
    family_last_tested[fid][cause1] = nfm.STEP_COUNTER
    
    # Step 2
    nfm.STEP_COUNTER = 2
    cause2, score2, mode2 = memory._select_next_cause(fid, exclude=set())
    
    # Should not be the same cause because cause1 is "recent" (2-1 < 2)
    assert cause1 != cause2

def test_falsification_mode_triggers_for_top_confidence_cause():
    reset_curiosity_state()
    fid = "F_FALSIFY"
    family_diag_confidence[fid] = {
        "EDGE_BAND_PROXIMITY": 0.2,
        "JOIN_PERSISTENCE": 0.8,
        "REUNION_FRICTION": 0.0
    }
    
    memory = NeutralFamilyMemoryV1()
    
    # Select top cause
    cause, score, mode = memory._select_next_cause(fid, exclude=set())
    assert cause == "JOIN_PERSISTENCE"
    assert mode == "FALSIFY"
    
    # Select non-top cause (by excluding top)
    cause2, score2, mode2 = memory._select_next_cause(fid, exclude={"JOIN_PERSISTENCE"})
    assert cause2 == "EDGE_BAND_PROXIMITY"
    assert mode2 == "PROBE"
