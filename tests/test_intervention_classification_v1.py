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
    MAX_HISTORY,
    ATTENTION_THRESHOLD,
    STREAK_THRESHOLD,
    STREAK_SCALE,
    MAX_ATTENTION,
    MIN_STREAK,
    MIN_ATTENTION,
    MIN_CONFIDENCE,
    MIN_CONF_GAP,
    TREND_WINDOW
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

def test_not_eligible_results_in_none():
    fid = "F_NOT_ELIGIBLE"
    memory = NeutralFamilyMemoryV1()
    
    # Not eligible
    family_action_eligible[fid] = False
    
    memory._classify_intervention(fid)
    assert family_intervention_type[fid] == "NONE"

def test_low_confidence_results_in_monitor():
    fid = "F_LOW_CONF"
    memory = NeutralFamilyMemoryV1()
    
    family_action_eligible[fid] = True
    # top_val < 0.5
    family_diag_confidence[fid] = {CAUSES[0]: 0.4, CAUSES[1]: 0.3, CAUSES[2]: 0.3}
    
    memory._classify_intervention(fid)
    assert family_intervention_type[fid] == "MONITOR"

def test_moderate_confidence_short_streak_results_in_stabilize():
    fid = "F_MODERATE"
    memory = NeutralFamilyMemoryV1()
    
    family_action_eligible[fid] = True
    # top >= 0.5 and drift <= 3
    family_diag_confidence[fid] = {CAUSES[0]: 0.55, CAUSES[1]: 0.45}
    family_drift_streak[fid] = 2
    
    memory._classify_intervention(fid)
    assert family_intervention_type[fid] == "STABILIZE"

def test_strong_clear_cause_results_in_isolate():
    fid = "F_CLEAR_CAUSE"
    memory = NeutralFamilyMemoryV1()
    
    family_action_eligible[fid] = True
    # top >= 0.6 and gap >= 0.2
    family_diag_confidence[fid] = {CAUSES[0]: 0.65, CAUSES[1]: 0.2, CAUSES[2]: 0.15}
    family_drift_streak[fid] = 4
    
    memory._classify_intervention(fid)
    assert family_intervention_type[fid] == "ISOLATE"

def test_strong_high_attention_results_in_suppress():
    fid = "F_HIGH_ATTENTION"
    memory = NeutralFamilyMemoryV1()
    
    family_action_eligible[fid] = True
    # top >= 0.7 and attention >= 1.4
    # attention = min(1.0 + (streak / 6.0), 1.5)
    # streak 3 -> 1.5
    family_diag_confidence[fid] = {CAUSES[0]: 0.75, CAUSES[1]: 0.25}
    family_drift_streak[fid] = 3
    
    memory._classify_intervention(fid)
    assert family_intervention_type[fid] == "SUPPRESS"

def test_equal_confidences_results_in_stabilize_fallback():
    fid = "F_EQUAL"
    memory = NeutralFamilyMemoryV1()
    
    family_action_eligible[fid] = True
    # top >= 0.5 but no gap and streak > 3
    family_diag_confidence[fid] = {CAUSES[0]: 0.5, CAUSES[1]: 0.5}
    family_drift_streak[fid] = 4
    
    # top_val = 0.5
    # drift = 4 (> 3)
    # gap = 0 (< 0.2)
    # attention = 1.0 + 4/6 = 1.67 -> 1.5
    # itype = STABILIZE (fallback)
    
    memory._classify_intervention(fid)
    assert family_intervention_type[fid] == "STABILIZE"

def test_no_confidence_data_results_in_monitor():
    fid = "F_NO_CONF"
    memory = NeutralFamilyMemoryV1()
    
    family_action_eligible[fid] = True
    family_diag_confidence[fid] = {}
    
    memory._classify_intervention(fid)
    assert family_intervention_type[fid] == "MONITOR"
