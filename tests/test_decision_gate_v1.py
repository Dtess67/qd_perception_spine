import pytest
from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1, family_hold_directions, family_suspect,
    family_hold_history, family_drift_streak, family_diag_confidence,
    family_action_eligible, family_diag_evidence, family_hold_trend,
    family_drift_score, family_diag_last_run, family_diag_confidence,
    MIN_STREAK, MIN_ATTENTION, MIN_CONFIDENCE, MIN_CONF_GAP, TREND_WINDOW,
    MAX_HISTORY
)

@pytest.fixture(autouse=True)
def reset_globals():
    family_hold_directions.clear()
    family_suspect.clear()
    family_hold_history.clear()
    family_hold_trend.clear()
    family_drift_score.clear()
    family_drift_streak.clear()
    family_diag_evidence.clear()
    family_diag_confidence.clear()
    family_diag_last_run.clear()
    family_action_eligible.clear()
    yield

def test_no_drift_not_eligible():
    memory = NeutralFamilyMemoryV1()
    fid = "F1"
    
    # 1. Effect is not real (streak=0)
    # 2. No evidence
    # 3. No history for trajectory
    
    memory._update_decision_gate(fid)
    assert family_action_eligible.get(fid) is False

def test_drift_low_evidence_not_eligible():
    memory = NeutralFamilyMemoryV1()
    fid = "F1"
    
    # 1. Effect is real
    family_drift_streak[fid] = MIN_STREAK # 2
    # attention_multiplier will be 1.0 + 2/6 = 1.33 >= 1.1
    
    # 2. Low evidence
    family_diag_confidence[fid] = {"CAUSE1": 0.4, "CAUSE2": 0.3}
    # top = 0.4 < 0.6, gap = 0.1 < 0.2
    
    # 3. Worsening trajectory
    family_hold_history[fid] = [{"A": 1}, {"A": 2}, {"A": 3}] # scalar: 1, 2, 3 -> increasing
    
    memory._update_decision_gate(fid)
    assert family_action_eligible.get(fid) is False

def test_drift_evidence_flat_trend_not_eligible():
    memory = NeutralFamilyMemoryV1()
    fid = "F1"
    
    # 1. Effect is real
    family_drift_streak[fid] = 2
    
    # 2. Sufficient evidence (top >= 0.6)
    family_diag_confidence[fid] = {"CAUSE1": 0.7, "CAUSE2": 0.3}
    
    # 3. Flat trajectory (not worsening)
    family_hold_history[fid] = [{"A": 5}, {"A": 5}, {"A": 5}] # scalar: 5, 5, 5 -> not scalars[-1] > scalars[0]
    
    memory._update_decision_gate(fid)
    assert family_action_eligible.get(fid) is False

def test_drift_evidence_worsening_trend_eligible():
    memory = NeutralFamilyMemoryV1()
    fid = "F1"
    
    # 1. Effect is real
    family_drift_streak[fid] = 2 # streak=2, mult=1.33
    
    # 2. Sufficient evidence (top >= 0.6)
    family_diag_confidence[fid] = {"CAUSE1": 0.65, "CAUSE2": 0.35}
    
    # 3. Worsening trajectory
    family_hold_history[fid] = [{"A": 1}, {"A": 2}, {"A": 4}] # scalar: 1, 2, 4 -> 4 > 1
    
    memory._update_decision_gate(fid)
    assert family_action_eligible.get(fid) is True

def test_competing_causes_gap_rule():
    memory = NeutralFamilyMemoryV1()
    fid = "F1"
    
    # Effect real
    family_drift_streak[fid] = 2
    # Worsening trend
    family_hold_history[fid] = [{"A": 1}, {"A": 2}, {"A": 3}]
    
    # Case A: Low top (0.5), but large gap (0.5 - 0.2 = 0.3 > 0.2) -> eligible
    family_diag_confidence[fid] = {"CAUSE1": 0.5, "CAUSE2": 0.2, "CAUSE3": 0.1}
    memory._update_decision_gate(fid)
    assert family_action_eligible.get(fid) is True
    
    # Case B: Low top (0.5), small gap (0.5 - 0.4 = 0.1 < 0.2) -> not eligible
    family_diag_confidence[fid] = {"CAUSE1": 0.5, "CAUSE2": 0.4, "CAUSE3": 0.1}
    memory._update_decision_gate(fid)
    assert family_action_eligible.get(fid) is False

def test_no_mutation_of_other_systems():
    memory = NeutralFamilyMemoryV1()
    fid = "F1"
    
    # Setup state
    family_suspect[fid] = False
    family_drift_streak[fid] = 2
    family_diag_confidence[fid] = {"CAUSE1": 0.8}
    family_hold_history[fid] = [{"A": 1}, {"A": 2}, {"A": 3}]
    
    # Trigger gate
    memory._update_decision_gate(fid)
    
    # Verify gate
    assert family_action_eligible[fid] is True
    
    # Verify no mutation
    assert family_suspect[fid] is False
    assert family_drift_streak[fid] == 2
    assert family_diag_confidence[fid] == {"CAUSE1": 0.8}
    assert len(family_hold_history[fid]) == 3
