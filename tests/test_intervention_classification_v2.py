import pytest
from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1,
    family_hold_directions,
    family_hold_history,
    family_hold_trend,
    family_drift_streak,
    family_drift_score,
    family_diag_evidence,
    family_diag_confidence,
    family_diag_last_run,
    family_action_eligible,
    family_intervention_type,
    CAUSES,
    STREAK_SCALE,
    MAX_ATTENTION,
    AMBIGUITY_GAP,
    HIGH_ATTENTION
)
from qd_perception_spine.entrenchment_v1 import family_suspect, family_authority

@pytest.fixture(autouse=True)
def reset_state():
    family_hold_directions.clear()
    family_hold_history.clear()
    family_hold_trend.clear()
    family_drift_streak.clear()
    family_drift_score.clear()
    family_diag_evidence.clear()
    family_diag_confidence.clear()
    family_diag_last_run.clear()
    family_action_eligible.clear()
    family_intervention_type.clear()
    family_suspect.clear()
    family_authority.clear()

def test_equal_confidence_low_attention_results_in_monitor():
    fid = "F_EQUAL_LOW"
    memory = NeutralFamilyMemoryV1()
    
    family_action_eligible[fid] = True
    # top >= 0.5, but gap < AMBIGUITY_GAP (0.15)
    # attention < HIGH_ATTENTION (1.3)
    # streak 1 -> attention = 1.0 + 1/6 = 1.17
    family_diag_confidence[fid] = {CAUSES[0]: 0.5, CAUSES[1]: 0.5}
    family_drift_streak[fid] = 1
    
    memory._classify_intervention(fid)
    # In v0.1 this was STABILIZE, now MONITOR
    assert family_intervention_type[fid] == "MONITOR"

def test_equal_confidence_high_attention_results_in_stabilize():
    fid = "F_EQUAL_HIGH"
    memory = NeutralFamilyMemoryV1()
    
    family_action_eligible[fid] = True
    # top >= 0.5, but gap < AMBIGUITY_GAP (0.15)
    # attention >= HIGH_ATTENTION (1.3)
    # streak 2 -> attention = 1.0 + 2/6 = 1.33
    family_diag_confidence[fid] = {CAUSES[0]: 0.5, CAUSES[1]: 0.5}
    family_drift_streak[fid] = 2
    
    memory._classify_intervention(fid)
    assert family_intervention_type[fid] == "STABILIZE"

def test_clear_cause_still_isolate():
    fid = "F_CLEAR_CAUSE"
    memory = NeutralFamilyMemoryV1()
    
    family_action_eligible[fid] = True
    # top >= 0.6 and gap >= 0.2 (gap > AMBIGUITY_GAP)
    family_diag_confidence[fid] = {CAUSES[0]: 0.7, CAUSES[1]: 0.3}
    family_drift_streak[fid] = 1
    
    memory._classify_intervention(fid)
    assert family_intervention_type[fid] == "ISOLATE"

def test_high_confidence_high_attention_still_suppress():
    fid = "F_HIGH_PRESSURE"
    memory = NeutralFamilyMemoryV1()
    
    family_action_eligible[fid] = True
    # top >= 0.7 and attention >= 1.4
    # streak 3 -> attention 1.5
    family_diag_confidence[fid] = {CAUSES[0]: 0.8, CAUSES[1]: 0.2}
    family_drift_streak[fid] = 3
    
    memory._classify_intervention(fid)
    assert family_intervention_type[fid] == "SUPPRESS"

def test_low_confidence_still_monitor():
    fid = "F_LOW_CONF"
    memory = NeutralFamilyMemoryV1()
    
    family_action_eligible[fid] = True
    # top < 0.5
    family_diag_confidence[fid] = {CAUSES[0]: 0.4, CAUSES[1]: 0.4, CAUSES[2]: 0.2}
    family_drift_streak[fid] = 5
    
    memory._classify_intervention(fid)
    assert family_intervention_type[fid] == "MONITOR"
