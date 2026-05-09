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

def test_slow_directional_drift_not_detected():
    """
    Scenario:
    - family_id = "F_DRIFT"
    - imbalance BELOW ASYMMETRY_THRESHOLD (3)
    - total BELOW HOLD_THRESHOLD (5)
    """
    mem = NeutralFamilyMemoryV1()
    fam_id = "F_DRIFT"
    
    # Initialize family
    mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 10)
    # Rename
    old_id = "fam_01"
    rec = mem._families.pop(old_id)
    rec.family_id = fam_id
    mem._families[fam_id] = rec
    mem._symbol_to_family["sym_0"] = fam_id

    mem.JOIN_PERSISTENCE_THRESHOLD = 50
    mem.EDGE_PERSISTENCE_THRESHOLD = 50
    
    # Distances in NeutralFamilyMemoryV1:
    # axes = ["axis_a", "axis_b", "axis_c", "axis_d"]
    # dist = sum(abs(sig1[axis] - sig2[axis])) / 4
    
    # Case A: JOIN_PERSISTENCE (dist < 0.15)
    # sig1 = 0.1, sig2 = 0.14. dist = 0.04 < 0.15.
    mem.join_or_create_family("sym_drift_A1", _sig(0.14), _spr(0.05), 1) 
    mem.join_or_create_family("sym_drift_A2", _sig(0.14), _spr(0.05), 1) 
    
    # Case B: EDGE_BAND_PROXIMITY (0.15 <= dist <= 0.25)
    # sig1 = 0.1, sig2 = 0.3. dist = 0.2. (0.15 < 0.2 < 0.25)
    mem.join_or_create_family("sym_drift_B1", _sig(0.3), _spr(0.05), 1)
    
    dist_dict = family_hold_directions.get(fam_id, {})
    print(f"\n[test_slow_directional_drift_not_detected] counts: {dist_dict}")
    
    assert family_suspect.get(fam_id, False) is False
    assert dist_dict.get("JOIN_PERSISTENCE") == 2
    assert dist_dict.get("EDGE_BAND_PROXIMITY") == 1

def test_low_frequency_instability_not_flagged():
    """
    Scenario:
    - Apply HOLD events intermittently:
        HOLD -> success -> HOLD -> success -> HOLD...
    Never reach HOLD_THRESHOLD
    """
    mem = NeutralFamilyMemoryV1()
    fam_id = "F_INSTABLE"
    
    # Initialize
    mem.join_or_create_family("sym_base", _sig(0.5), _spr(0.05), 10)
    old_id = "fam_01"
    rec = mem._families.pop(old_id)
    rec.family_id = fam_id
    mem._families[fam_id] = rec
    mem._symbol_to_family["sym_base"] = fam_id

    # Pattern: 1 hold, 1 success (decay), repeat.
    mem.JOIN_PERSISTENCE_THRESHOLD = 50
    for i in range(10):
        # 1 HOLD event
        mem.join_or_create_family(f"sym_hold_{i}", _sig(0.51), _spr(0.05), 1)
        # 1 Success event (decay)
        mem.join_or_create_family("sym_base", _sig(0.5), _spr(0.05), 1)

    dist_dict = family_hold_directions.get(fam_id, {})
    print(f"\n[test_low_frequency_instability_not_flagged] counts: {dist_dict}")
    total_hold = sum(dist_dict.values())
    assert total_hold == 0
    assert family_suspect.get(fam_id, False) is False

def test_coalition_masks_drift():
    """
    Scenario:
    - Drift is distributed across directions so no single direction spikes
    """
    mem = NeutralFamilyMemoryV1()
    fam_id = "F_DRIFT_COALITION"
    
    # Initialize
    mem.join_or_create_family("sym_target", _sig(0.1), _spr(0.01), 10)
    old_id = "fam_01"
    rec = mem._families.pop(old_id)
    rec.family_id = fam_id
    mem._families[fam_id] = rec
    mem._symbol_to_family["sym_target"] = fam_id

    mem.JOIN_PERSISTENCE_THRESHOLD = 50
    mem.EDGE_PERSISTENCE_THRESHOLD = 50
    
    # JOIN_PERSISTENCE: 2 hits
    mem.join_or_create_family("sym_p1", _sig(0.11), _spr(0.01), 1)
    mem.join_or_create_family("sym_p2", _sig(0.11), _spr(0.01), 1)
    
    # EDGE_BAND_PROXIMITY: 2 hits
    mem.join_or_create_family("sym_e1", _sig(0.3), _spr(0.01), 1)
    mem.join_or_create_family("sym_e2", _sig(0.3), _spr(0.01), 1)
    
    dist_dict = family_hold_directions.get(fam_id, {})
    print(f"\n[test_coalition_masks_drift] counts: {dist_dict}")
    total_hold = sum(dist_dict.values())
    assert total_hold == 4
    assert family_suspect.get(fam_id, False) is False

def test_long_term_undetected_drift():
    """
    Scenario:
    - drift exists undetected
    """
    mem = NeutralFamilyMemoryV1()
    fam_id = "F_LONG_DRIFT"
    
    # Initialize
    mem.join_or_create_family("sym_base", _sig(0.5), _spr(0.05), 10)
    old_id = "fam_01"
    rec = mem._families.pop(old_id)
    rec.family_id = fam_id
    mem._families[fam_id] = rec
    mem._symbol_to_family["sym_base"] = fam_id

    mem.JOIN_PERSISTENCE_THRESHOLD = 1000
    mem.EDGE_PERSISTENCE_THRESHOLD = 1000
    
    # Pattern: 2 holds in JOIN_PERSISTENCE, 2 in EDGE_BAND_PROXIMITY. Total=4. Diff=0.
    mem.join_or_create_family("sym_hold_A1", _sig(0.51), _spr(0.05), 1)
    mem.join_or_create_family("sym_hold_A2", _sig(0.51), _spr(0.05), 1)
    mem.join_or_create_family("sym_hold_B1", _sig(0.7), _spr(0.05), 1)
    mem.join_or_create_family("sym_hold_B2", _sig(0.7), _spr(0.05), 1)

    dist = family_hold_directions.get(fam_id, {})
    print(f"\n[test_long_term_undetected_drift] final counts: {dist}")
    
    total_hold = sum(dist.values())
    counts = list(dist.values())
    max_dir = max(counts) if counts else 0
    min_dir = min(counts) if counts else 0
    diff = max_dir - min_dir
    
    assert total_hold < HOLD_THRESHOLD
    assert diff < ASYMMETRY_THRESHOLD
    assert family_suspect.get(fam_id, False) is False
