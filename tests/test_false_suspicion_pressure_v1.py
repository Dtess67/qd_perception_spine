import pytest
from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1,
    family_hold_directions,
    HOLD_THRESHOLD,
    ASYMMETRY_THRESHOLD,
    family_hold_history,
    family_hold_trend,
    family_drift_score
)
from qd_perception_spine.entrenchment_v1 import (
    family_authority,
    family_suspect
)

def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}

def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}

@pytest.fixture(autouse=True)
def reset_globals():
    """Resets global structures before each test."""
    family_hold_directions.clear()
    family_hold_history.clear()
    family_hold_trend.clear()
    family_drift_score.clear()
    family_authority.clear()
    family_suspect.clear()

def test_suspect_family_can_recover_after_successes():
    mem = NeutralFamilyMemoryV1()
    # JOIN_PERSISTENCE_THRESHOLD = 2 in production
    fid = "fam_01"
    signature = _sig(0.1)
    spread = _spr(0.05)
    
    # 1. Establish family
    mem.join_or_create_family("sym_init", signature, spread, 10)
    
    # 2. Accumulate HOLD events to trigger suspicion
    for i in range(HOLD_THRESHOLD):
        # Force a HOLD by making it just outside DISTANCE_THRESHOLD (0.15) but inside HOLD_THRESHOLD (0.25)
        hold_sig = _sig(0.3) 
        mem.join_or_create_family(f"sym_hold_{i}", hold_sig, spread, 1)
        
    assert family_suspect.get(fid) is True
    
    # 3. Repeated successful non-HOLD events (JOIN_EXISTING_FAMILY)
    # Each success decays counts by 1
    for i in range(HOLD_THRESHOLD + 1):
        mem.join_or_create_family("sym_init", signature, spread, 1)
        
    # 4. Expected: suspect flag eventually becomes False
    assert family_suspect.get(fid) is False

def test_brief_directional_imbalance_does_not_permanently_freeze():
    mem = NeutralFamilyMemoryV1()
    fid = "fam_01"
    signature = _sig(0.1)
    spread = _spr(0.05)
    
    # 1. Establish family
    mem.join_or_create_family("sym_init", signature, spread, 10)
    
    # 2. Trigger asymmetry-based suspicion
    # ASYMMETRY_THRESHOLD = 3
    # We need to trigger 3 HOLDs of one type and 0 of others
    for i in range(ASYMMETRY_THRESHOLD):
        # hold_mode will be EDGE_BAND_PROXIMITY because dist ~ 0.2
        hold_sig = _sig(0.3)
        mem.join_or_create_family(f"sym_edge_{i}", hold_sig, spread, 1)
        
    assert family_suspect.get(fid) is True
    
    # 3. Follow with balanced/non-HOLD successes
    for _ in range(ASYMMETRY_THRESHOLD + 1):
        mem.join_or_create_family("sym_init", signature, spread, 1)
        
    # 4. Expected: suspect flag clears
    assert family_suspect.get(fid) is False
    
    # 5. Verify authority can increment again
    # Use a mock rollback event or just check handle_rollback logic
    from qd_perception_spine.entrenchment_v1 import RollbackEvent, handle_rollback
    event = RollbackEvent(participants=[fid])
    handle_rollback(event)
    assert event.authority_incremented is True
    assert family_authority.get(fid) == 1

def test_authority_resumes_after_suspicion_clears():
    from qd_perception_spine.entrenchment_v1 import RollbackEvent, handle_rollback
    mem = NeutralFamilyMemoryV1()
    fid = "fam_01"
    signature = _sig(0.1)
    spread = _spr(0.05)
    
    # 1. Establish family and make it suspect
    mem.join_or_create_family("sym_init", signature, spread, 10)
    for i in range(HOLD_THRESHOLD):
        mem.join_or_create_family(f"sym_hold_{i}", _sig(0.3), spread, 1)
    
    assert family_suspect.get(fid) is True
    
    # 2. Trigger rollback
    event1 = RollbackEvent(participants=[fid])
    handle_rollback(event1)
    
    # Expected: authority does NOT increment
    assert event1.authority_incremented is False
    assert family_authority.get(fid, 0) == 0
    
    # 3. Clear suspicion through non-HOLD decay
    for _ in range(HOLD_THRESHOLD + 1):
        mem.join_or_create_family("sym_init", signature, spread, 1)
        
    assert family_suspect.get(fid) is False
    
    # 4. Trigger rollback again
    event2 = RollbackEvent(participants=[fid])
    handle_rollback(event2)
    
    # Expected: authority increments normally
    assert event2.authority_incremented is True
    assert family_authority.get(fid) == 1

def test_suspect_family_does_not_freeze_unrelated_families():
    from qd_perception_spine.entrenchment_v1 import RollbackEvent, handle_rollback
    mem = NeutralFamilyMemoryV1()
    
    # F_BAD (fam_01) - suspect
    mem.join_or_create_family("sym_bad", _sig(0.1), _spr(0.05), 10)
    for i in range(HOLD_THRESHOLD):
        mem.join_or_create_family(f"sym_bad_hold_{i}", _sig(0.3), _spr(0.05), 1)
    
    # F_GOOD (fam_02) - not suspect
    mem.join_or_create_family("sym_good", _sig(0.8), _spr(0.05), 10)
    
    assert family_suspect.get("fam_01") is True
    assert family_suspect.get("fam_02", False) is False
    
    # Trigger rollback involving only F_GOOD
    event = RollbackEvent(participants=["fam_02"])
    handle_rollback(event)
    
    # Expected: F_GOOD authority increments normally
    assert event.authority_incremented is True
    assert family_authority.get("fam_02") == 1
    # F_BAD status should not have changed
    assert family_authority.get("fam_01", 0) == 0
