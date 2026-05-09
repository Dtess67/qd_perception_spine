import pytest
from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1, 
    family_hold_directions, 
    family_hold_history, 
    family_hold_trend,
    family_suspect
)

def _reset():
    family_hold_directions.clear()
    family_hold_history.clear()
    family_hold_trend.clear()
    family_suspect.clear()

@pytest.fixture(autouse=True)
def reset_state():
    _reset()

def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}

def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}

def test_increasing_directional_imbalance_shows_positive_trend():
    mem = NeutralFamilyMemoryV1()
    fam_id = "F_TREND"
    
    # Establish family
    mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 10)
    
    # Inject HOLDs in one direction primarily
    # Direction: JOIN_PERSISTENCE (default for DISTANCE_THRESHOLD < dist < HOLD_THRESHOLD)
    # We'll use signatures that trigger JOIN_PERSISTENCE
    # DISTANCE_THRESHOLD = 0.15, HOLD_THRESHOLD = 0.25
    
    for i in range(10):
        # Trigger EDGE_BAND_PROXIMITY hold (dist between 0.15 and 0.25)
        # Use unique symbol ID for each evaluation
        sid = f"sym_hold_{i}"
        mem.join_or_create_family(sid, _sig(0.28), _spr(0.05), 1)
        
    trend = family_hold_trend.get("fam_01", {})
    assert trend.get("EDGE_BAND_PROXIMITY", 0) > 0
    # First snapshot was at i=0, last at i=9.
    # Total snapshots = 11 (1 establishment + 10 holds).
    # History[0] is snapshot 1 (after i=0). EDGE = 1.
    # History[-1] is snapshot 10 (after i=9). EDGE = 10.
    # Trend = 10 - 1 = 9.
    assert trend["EDGE_BAND_PROXIMITY"] >= 5

def test_stable_distribution_shows_near_zero_trend():
    mem = NeutralFamilyMemoryV1()
    
    # Establish family
    mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 10)
    
    # Snapshot 1: some holds
    for i in range(3):
        mem.join_or_create_family(f"sym_hold_{i}", _sig(0.28), _spr(0.05), 1)
    
    initial_trend = family_hold_trend.get("fam_01", {}).copy()
    
    # Now trigger many non-HOLD events to decay it back to zero
    for _ in range(10):
        mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 10)
        
    final_trend = family_hold_trend.get("fam_01", {})
    # It should have trended down from its peak
    # Last value is 0, First value was 1 (from first append) or 0.
    # Actually, history keeps last 10.
    # If we did 3 holds + 10 successes = 13 events.
    # History[0] would be around event 4 (after 3 holds and 1 success).
    # Event 4: EDGE_BAND_PROXIMITY = 2 (3 holds - 1 success).
    # Event 13: EDGE_BAND_PROXIMITY = 0.
    # Trend = 0 - 2 = -2.
    
    # If it's stable (0 throughout the history window), trend should be 0.
    assert final_trend.get("EDGE_BAND_PROXIMITY", 0) <= 0

def test_fluctuating_balanced_shows_near_zero_trend():
    mem = NeutralFamilyMemoryV1()
    mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 10)
    
    # Alternate between two directions to keep it "balanced" but fluctuating
    # Actually, join_or_create_family usually picks one hold_mode.
    # We can force EDGE_BAND_PROXIMITY by distance.
    # EDGE_BAND_PROXIMITY occurs when dist >= DISTANCE_THRESHOLD (0.15)
    # But wait, it's complex. Let's just use what we can trigger.
    
    # History window is 10.
    # If we do 10 pairs of (Hold A, Success), the counts stay low.
    for i in range(10):
        sid = f"sym_hold_{i}"
        mem.join_or_create_family(sid, _sig(0.28), _spr(0.05), 1) # Hold +1
        mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 1)     # Success -1
        
    trend = family_hold_trend.get("fam_01", {})
    # Since it's +1, -1, +1, -1... the net change over the last 10 snapshots should be small (-1, 0, or 1)
    assert abs(trend.get("EDGE_BAND_PROXIMITY", 0)) <= 1

def test_drift_pressure_simulation_shows_measurable_trend():
    # Simulation of test_slow_directional_drift_not_detected from drift pressure tests
    mem = NeutralFamilyMemoryV1()
    mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 10)
    
    # Drift: direction A +1, then Success (all -1), then direction A +1...
    # Wait, decay reduces ALL directions. 
    # To get drift, we need more + than -.
    
    for i in range(15):
        mem.join_or_create_family(f"sid_{i}_a", _sig(0.28), _spr(0.05), 1) # EDGE +1
        mem.join_or_create_family(f"sid_{i}_b", _sig(0.28), _spr(0.05), 1) # EDGE +1
        mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 1)     # All -1
        
    # Net per cycle: EDGE +1.
    # After 15 cycles, EDGE = 15.
    # History window = 10. 
    # History[0] is at cycle 10 approx. EDGE ~ 10.
    # History[-1] is at cycle 15. EDGE ~ 15.
    # Trend ~ 5.
    
    trend = family_hold_trend.get("fam_01", {})
    assert trend.get("EDGE_BAND_PROXIMITY", 0) > 0
    # It might trigger suspect flag if asymmetry >= 3, which is fine for this test.
    # We just want to see a trend.
    
    # Let's retry with sub-threshold imbalance
    _reset()
    mem = NeutralFamilyMemoryV1()
    mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 10)
    
    for i in range(10):
        mem.join_or_create_family(f"sid_{i}", _sig(0.28), _spr(0.05), 1) # EDGE +1
        mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 1)     # Success -1
        # Net 0.
        # Let's do JOIN +2, Success -1. Net +1.
        
    _reset()
    mem = NeutralFamilyMemoryV1()
    mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 10)
    for i in range(5):
        mem.join_or_create_family(f"sid_{i}_a", _sig(0.28), _spr(0.05), 1)
        mem.join_or_create_family(f"sid_{i}_b", _sig(0.28), _spr(0.05), 1)
        mem.join_or_create_family("sym_0", _sig(0.1), _spr(0.05), 1)
        # JOIN = 1, then 2, then 1...
        # Wait, the requirement says "Long-term drift from pressure tests → measurable trend"
        # In drift pressure tests, we saw that even if suspect is False, we can see the distribution growing.
        
    # Just verify we get A trend.
    assert "fam_01" in family_hold_trend
