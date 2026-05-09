import pytest
from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1,
    family_diag_confidence,
    family_diag_evidence,
    CAUSES,
    MIN_CONF,
    MAX_CONF
)

@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global tracking structures before each test."""
    family_diag_confidence.clear()
    family_diag_evidence.clear()
    yield

def test_pass_increases_confidence():
    memory = NeutralFamilyMemoryV1()
    fid = "F_TEST"
    cause = CAUSES[0]
    
    # Start at 0.5
    family_diag_confidence[fid] = {c: 0.5 for c in CAUSES}
    
    memory._update_confidence(fid, cause, "PASS")
    
    # Expected: 0.5 + 0.1 * (1 - 0.5) = 0.5 + 0.05 = 0.55
    assert family_diag_confidence[fid][cause] == 0.55

def test_fail_decreases_confidence():
    memory = NeutralFamilyMemoryV1()
    fid = "F_TEST"
    cause = CAUSES[0]
    
    # Start at 0.5
    family_diag_confidence[fid] = {c: 0.5 for c in CAUSES}
    
    memory._update_confidence(fid, cause, "FAIL")
    
    # Expected: 0.5 - 0.08 * 0.5 = 0.5 - 0.04 = 0.46
    assert family_diag_confidence[fid][cause] == 0.46

def test_unclear_no_change():
    memory = NeutralFamilyMemoryV1()
    fid = "F_TEST"
    cause = CAUSES[0]
    
    # Start at 0.5
    family_diag_confidence[fid] = {c: 0.5 for c in CAUSES}
    
    memory._update_confidence(fid, cause, "UNCLEAR")
    
    assert family_diag_confidence[fid][cause] == 0.5

def test_confidence_caps_at_max():
    memory = NeutralFamilyMemoryV1()
    fid = "F_TEST"
    cause = CAUSES[0]
    
    # Start at 0.94
    family_diag_confidence[fid] = {c: 0.94 for c in CAUSES}
    
    # One PASS: 0.94 + 0.1*(0.06) = 0.946
    memory._update_confidence(fid, cause, "PASS")
    assert family_diag_confidence[fid][cause] == 0.946
    
    # Second PASS: 0.946 + 0.1*(0.054) = 0.9514 -> Capped at 0.95
    memory._update_confidence(fid, cause, "PASS")
    assert family_diag_confidence[fid][cause] == MAX_CONF

def test_confidence_floors_at_min():
    memory = NeutralFamilyMemoryV1()
    fid = "F_TEST"
    cause = CAUSES[0]
    
    # Start at 0.05
    family_diag_confidence[fid] = {c: 0.05 for c in CAUSES}
    
    # One FAIL: 0.05 - 0.08*0.05 = 0.046 -> Capped at 0.05
    memory._update_confidence(fid, cause, "FAIL")
    assert family_diag_confidence[fid][cause] == MIN_CONF

def test_repeated_fail_drives_confidence_down_gradually():
    memory = NeutralFamilyMemoryV1()
    fid = "F_TEST"
    cause = CAUSES[0]
    
    # Start at 0.8
    family_diag_confidence[fid] = {c: 0.8 for c in CAUSES}
    
    # FAIL 1: 0.8 - 0.08*0.8 = 0.736
    memory._update_confidence(fid, cause, "FAIL")
    assert family_diag_confidence[fid][cause] == 0.736
    
    # FAIL 2: 0.736 - 0.08*0.736 = 0.6771
    memory._update_confidence(fid, cause, "FAIL")
    assert family_diag_confidence[fid][cause] == 0.6771
    
    # Still above floor
    assert family_diag_confidence[fid][cause] > MIN_CONF
