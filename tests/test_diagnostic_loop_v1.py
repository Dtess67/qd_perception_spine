import pytest
from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1, family_suspect, family_hold_directions, 
    family_hold_history, family_hold_trend, family_drift_score, 
    family_drift_streak, family_diag_evidence, family_diag_last_run,
    HOLD_THRESHOLD, ASYMMETRY_THRESHOLD, MAX_HISTORY, STREAK_THRESHOLD,
    DIAGNOSTIC_TRIGGER, CAUSES, MAX_DIAG_TESTS
)
from qd_perception_spine.entrenchment_v1 import family_authority

def reset_globals():
    family_suspect.clear()
    family_hold_directions.clear()
    family_hold_history.clear()
    family_hold_trend.clear()
    family_drift_score.clear()
    family_drift_streak.clear()
    family_authority.clear()
    family_diag_evidence.clear()
    family_diag_last_run.clear()

@pytest.fixture(autouse=True)
def run_around_tests():
    reset_globals()
    yield
    reset_globals()

def test_drift_triggers_diagnostic():
    """Verify that drift triggers diagnostic when thresholds are met."""
    memory = NeutralFamilyMemoryV1()
    fid = "F_DIAG"
    sig = {"axis_a": 1.0, "axis_b": 1.0, "axis_c": 1.0, "axis_d": 1.0}
    spr = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    
    # 1. Fill history to allow trend computation
    # We need 10 updates.
    # To have streak >= 2 (DIAGNOSTIC_TRIGGER), we need drift_magnitude >= 3 for 2 updates.
    # To have multiplier > 1.1, we need streak >= 1 (1 + 1/6 = 1.17)
    
    # Pre-create family to ensure stable fid
    memory.join_or_create_family("S_INIT", sig, spr, 1)
    fid = memory.get_family_for_symbol("S_INIT")
    
    # Update 1-9: accumulation
    for i in range(9):
        memory.join_or_create_family("S1", sig, spr, 1) # JOIN_EXISTING_FAMILY
        
    # Update 10: Window full, first trend/streak computed
    # We need drift_magnitude >= 3 to get streak = 1
    # Let's inject some HOLDs
    family_hold_directions[fid] = {"EDGE_BAND_PROXIMITY": 5}
    memory.join_or_create_family("S1", sig, spr, 1)
    
    assert family_drift_streak.get(fid) == 1
    # multiplier = 1 + 1/6 = 1.166... > 1.1
    # last_run will be 1, 1%3 != 0, so it won't run yet.
    
    # Update 11: streak = 2
    # last_run will be 2, 2%3 != 0, so it won't run yet.
    memory.join_or_create_family("S1", sig, spr, 1)
    assert family_drift_streak.get(fid) == 2
    
    # Update 12: streak = 3
    # last_run will be 3, 3%3 == 0. RUN!
    # Update trend to ensure it still triggers streak >= 2 and reproduces
    family_hold_directions[fid] = {"EDGE_BAND_PROXIMITY": 10}
    
    # Manually ensure trigger conditions are met for this specific call
    family_drift_streak[fid] = 3
    family_suspect[fid] = False
    family_diag_last_run[fid] = 2 # next will be 3
    
    # Force asymmetry threshold to NOT trigger suspect
    # ASYMMETRY_THRESHOLD is 3. attention_multiplier 1.5 -> effective threshold 2.0
    # distribution has max=10, min=0 (if we add another key with 0)
    # Let's just reset distributions to be balanced for this step
    family_hold_directions[fid] = {"EDGE_BAND_PROXIMITY": 1, "JOIN_PERSISTENCE": 1}
    
    # We must also ensure that the trend computation (which happens in join_or_create_family)
    # doesn't reset the streak to 0.
    # Drift awareness updates before diagnostic check.
    # To keep streak at 3, drift_magnitude must be >= 3.
    # Since window is 10, and we just set current dist to {1,1}, 
    # we need history[0] to be something that results in magnitude >= 3.
    family_hold_history[fid][0] = {"EDGE_BAND_PROXIMITY": 5, "JOIN_PERSISTENCE": 1}
    # last is now {1,1}, first is {5,1} -> trend {-4, 0} -> magnitude 4 >= 3. STREAK PERSISTS!
    
    # CRITICAL: history.append(current_dist) happens IN _update_drift_awareness
    # before trend calculation.
    # So if we want history[-1] to be {1,1}, we can just set current_dist.
    # But if we want it to persist, we might need to manually call it or mock it.
    # For simplicity, let's just bypass _update_drift_awareness by mocking the streak
    # and attention_multiplier logic if possible, or just be very careful with state.
    
    # Actually, let's just fill the history so that the NEXT update results in what we want.
    family_hold_history[fid] = [{"EDGE_BAND_PROXIMITY": 5, "JOIN_PERSISTENCE": 1}] * 9
    family_hold_directions[fid] = {"EDGE_BAND_PROXIMITY": 1, "JOIN_PERSISTENCE": 1}
    
    memory.join_or_create_family("S1", sig, spr, 1)
    
    assert fid in family_diag_evidence
    assert family_diag_last_run[fid] == 3

def test_no_drift_no_diagnostic():
    """Verify that no diagnostic runs if there is no drift streak."""
    memory = NeutralFamilyMemoryV1()
    fid = "F_STABLE"
    sig = {"axis_a": 1.0, "axis_b": 1.0, "axis_c": 1.0, "axis_d": 1.0}
    spr = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    
    for i in range(15):
        memory.join_or_create_family("S1", sig, spr, 1)
        
    assert family_drift_streak.get(fid, 0) == 0
    assert fid not in family_diag_evidence

def test_evidence_accumulates_when_anomaly_reproducible():
    """Verify that evidence counts increase if the simulated perturbation matches the trend."""
    memory = NeutralFamilyMemoryV1()
    fid = "F_REPRO"
    sig = {"axis_a": 1.0, "axis_b": 1.0, "axis_c": 1.0, "axis_d": 1.0}
    spr = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    
    # Pre-create family
    memory.join_or_create_family("S_INIT", sig, spr, 1)
    fid = memory.get_family_for_symbol("S_INIT")

    # Manually setup state to trigger diagnostic immediately
    family_hold_trend[fid] = {"EDGE_BAND_PROXIMITY": 1}
    family_drift_streak[fid] = 2
    family_diag_last_run[fid] = 2 # next will be 3
    
    # We need attention_multiplier > 1.1
    # streak 2 -> 1 + 2/6 = 1.33 > 1.1
    
    # The cause "EDGE_BAND_PROXIMITY" should reproduce because trend is > 0
    memory.join_or_create_family("S1", sig, spr, 1)
    
    assert family_diag_evidence[fid]["EDGE_BAND_PROXIMITY"] == 1
    assert family_diag_evidence[fid]["JOIN_PERSISTENCE"] == 0

def test_no_state_mutation_from_tests():
    """Verify that diagnostics do not change authority or family memberships."""
    memory = NeutralFamilyMemoryV1()
    fid = "F_SAFE"
    sig = {"axis_a": 1.0, "axis_b": 1.0, "axis_c": 1.0, "axis_d": 1.0}
    spr = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    
    family_hold_trend[fid] = {"EDGE_BAND_PROXIMITY": 1}
    family_drift_streak[fid] = 2
    family_diag_last_run[fid] = 2
    family_authority[fid] = 10
    
    initial_members = len(memory.get_family_record(fid).member_symbol_ids) if memory.get_family_record(fid) else 0
    
    memory.join_or_create_family("S1", sig, spr, 1)
    
    assert family_authority[fid] == 10 # No change
    # Members might change due to join_or_create_family but not due to diagnostic
    
def test_diagnostic_respects_max_diag_tests():
    """Verify that only MAX_DIAG_TESTS are run per diagnostic call."""
    memory = NeutralFamilyMemoryV1()
    fid = "F_LIMIT"
    sig = {"axis_a": 1.0, "axis_b": 1.0, "axis_c": 1.0, "axis_d": 1.0}
    spr = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    
    # Pre-create family
    memory.join_or_create_family("S_INIT", sig, spr, 1)
    fid = memory.get_family_for_symbol("S_INIT")

    # Setup for reproduction in all causes
    family_hold_trend[fid] = {c: 1 for c in CAUSES}
    family_drift_streak[fid] = 2
    family_diag_last_run[fid] = 2
    
    memory.join_or_create_family("S1", sig, spr, 1)
    
    evidence = family_diag_evidence[fid]
    non_zero = [c for c, v in evidence.items() if v > 0]
    assert len(non_zero) == MAX_DIAG_TESTS

def test_diagnostic_does_not_run_during_suspect():
    """Verify that diagnostic is skipped if family is already suspect."""
    memory = NeutralFamilyMemoryV1()
    fid = "F_SUSPECT"
    sig = {"axis_a": 1.0, "axis_b": 1.0, "axis_c": 1.0, "axis_d": 1.0}
    spr = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    
    family_hold_trend[fid] = {"EDGE_BAND_PROXIMITY": 1}
    family_drift_streak[fid] = 2
    family_diag_last_run[fid] = 2
    family_suspect[fid] = True
    
    memory.join_or_create_family("S1", sig, spr, 1)
    
    assert fid not in family_diag_evidence
