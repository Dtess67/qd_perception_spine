import pytest
from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1,
    family_hold_directions,
    family_hold_history,
    family_hold_trend,
    family_drift_score,
    HOLD_THRESHOLD,
    ASYMMETRY_THRESHOLD,
    ATTENTION_THRESHOLD,
    MAX_HISTORY
)
from qd_perception_spine.entrenchment_v1 import (
    family_suspect,
    family_authority
)

def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}

def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}

@pytest.fixture(autouse=True)
def reset_globals():
    family_hold_directions.clear()
    family_hold_history.clear()
    family_hold_trend.clear()
    family_drift_score.clear()
    family_suspect.clear()
    family_authority.clear()
    yield

def test_no_drift_thresholds_unchanged():
    """1. No drift -> thresholds unchanged"""
    mem = NeutralFamilyMemoryV1()
    fam_id = "fam_01"
    
    # Initialize family
    mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 10)
    
    # Total hold = 2 (just below HOLD_THRESHOLD=5)
    mem.JOIN_PERSISTENCE_THRESHOLD = 50
    for i in range(2):
        mem.join_or_create_family(f"sym_h{i}", _sig(0.11), _spr(0.05), 1)
    
    # No trend yet (needs 10 snapshots)
    assert family_drift_score.get(fam_id, 0) == 0
    assert family_suspect.get(fam_id, False) is False

def test_moderate_drift_lowers_thresholds():
    """2. Moderate drift -> thresholds lowered"""
    mem = NeutralFamilyMemoryV1()
    fam_id = "fam_01"
    
    # Initialize family
    mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 10)
    mem.JOIN_PERSISTENCE_THRESHOLD = 50
    
    # We need 10 snapshots.
    # Snapshot 1: 1 HOLD
    mem.join_or_create_family("sym_h_start", _sig(0.11), _spr(0.05), 1)
    # Snapshots 2-9: SUCCESS (decay to 0)
    for i in range(8):
        mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 1)
    # Snapshot 10: 5 HOLDS (one by one)
    # 5th HOLD will trigger suspicion because:
    # After snapshot 10: Trend = 5 - 1 = 4. Drift = 4.
    # Multiplier = 1.5. Adjusted Threshold = 3.33.
    # Total hold is 5. 5 >= 3.33 -> Suspect = True.
    for i in range(5):
        mem.join_or_create_family(f"sym_h_end_{i}", _sig(0.11), _spr(0.05), 1)
        
    assert family_drift_score.get(fam_id, 0) >= ATTENTION_THRESHOLD
    assert family_suspect.get(fam_id, False) is True

def test_drift_increases_hold_sensitivity():
    """3. Drift increases HOLD sensitivity"""
    mem = NeutralFamilyMemoryV1()
    fam_id = "fam_01"
    
    # Initialize
    mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 10)
    mem.JOIN_PERSISTENCE_THRESHOLD = 50
    
    # 1st event: 1 HOLD
    mem.join_or_create_family("sym_h_start", _sig(0.11), _spr(0.05), 1)
    # 2-9: SUCCESS
    for i in range(8):
        mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 1)
    # 10th: 3 more HOLDS (one by one)
    # After 10th call (which is 1st of these 3):
    # Trend = last(2) - first(1) = 1. Drift=1. Multiplier=1.0.
    # Total hold = 2.
    mem.join_or_create_family("sym_h_end_0", _sig(0.11), _spr(0.05), 1)
    # After 11th call (2nd of these 3):
    # Trend = last(3) - first(1) = 2. Drift=2. Multiplier=1.0.
    # Total hold = 3.
    mem.join_or_create_family("sym_h_end_1", _sig(0.11), _spr(0.05), 1)
    # After 12th call (3rd of these 3):
    # Trend = last(4) - first(1) = 3. Drift=3. Multiplier=1.5.
    # Total hold = 4.
    # Adjusted Threshold = 5 / 1.5 = 3.33.
    # 4 >= 3.33 -> Suspect = True.
    mem.join_or_create_family("sym_h_end_2", _sig(0.11), _spr(0.05), 1)
    
    assert family_drift_score.get(fam_id, 0) == 3
    assert family_suspect.get(fam_id, False) is True

def test_drift_increases_asymmetry_sensitivity():
    """4. Drift increases asymmetry sensitivity"""
    mem = NeutralFamilyMemoryV1()
    fam_id = "fam_01"
    
    # Initialize
    mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.01), 10)
    mem.JOIN_PERSISTENCE_THRESHOLD = 50
    mem.EDGE_PERSISTENCE_THRESHOLD = 50
    
    # Create drift = 3
    # 1st: 1 HOLD JOIN
    mem.join_or_create_family("sym_h_start", _sig(0.11), _spr(0.01), 1)
    # 2-9: SUCCESS
    for i in range(8):
        mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.01), 1)
    # 10-12: 3 HOLD JOIN (Trend 4-1=3)
    for i in range(3):
        mem.join_or_create_family(f"sym_h_drift_{i}", _sig(0.11), _spr(0.01), 1)
        
    # Drift = 3. Multiplier = 1.5.
    # Adjusted ASYMMETRY_THRESHOLD = 3 / 1.5 = 2.0.
    # Total hold is now 4.
    
    # Create asymmetry: 
    # JOIN_PERSISTENCE = 4
    # EDGE_BAND_PROXIMITY = 2
    # Diff = 2.
    # 2 >= 2.0 -> Suspect = True.
    mem.join_or_create_family("sym_e1", _sig(0.3), _spr(0.01), 1)
    mem.join_or_create_family("sym_e2", _sig(0.3), _spr(0.01), 1)
    
    assert family_suspect.get(fam_id, False) is True

def test_no_direct_authority_change_from_drift_alone():
    """5. No direct authority change from drift alone"""
    from qd_perception_spine.entrenchment_v1 import RollbackEvent, handle_rollback
    mem = NeutralFamilyMemoryV1()
    fam_id = "fam_01"
    
    # Initialize
    mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 10)
    mem.JOIN_PERSISTENCE_THRESHOLD = 50
    
    initial_auth = family_authority.get(fam_id, 0)
    
    # Provide 10 events but keep drift below threshold
    for i in range(10):
        mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 1)
    
    assert family_drift_score.get(fam_id, 0) == 0
    assert family_authority.get(fam_id, 0) == initial_auth
    assert family_suspect.get(fam_id, False) is False
    
    # Trigger rollback
    event = RollbackEvent(participants=[fam_id])
    handle_rollback(event)
    
    assert family_authority.get(fam_id, 0) == initial_auth + 1
