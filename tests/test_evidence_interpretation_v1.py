import pytest
from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1,
    family_diag_evidence,
    family_diag_confidence,
    family_diag_last_run,
    CAUSES
)

@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state before each test."""
    family_diag_evidence.clear()
    family_diag_confidence.clear()
    family_diag_last_run.clear()
    yield

def test_equal_evidence_results_in_equal_confidence():
    memory = NeutralFamilyMemoryV1()
    family_id = "F_EQUAL"
    
    # Manually populate evidence
    family_diag_evidence[family_id] = {
        "EDGE_BAND_PROXIMITY": 2,
        "JOIN_PERSISTENCE": 2,
        "REUNION_FRICTION": 0
    }
    
    memory._interpret_evidence(family_id)
    
    conf = family_diag_confidence[family_id]
    assert conf["EDGE_BAND_PROXIMITY"] == 0.5
    assert conf["JOIN_PERSISTENCE"] == 0.5
    assert conf["REUNION_FRICTION"] == 0.0

def test_unequal_evidence_results_in_proportional_confidence():
    memory = NeutralFamilyMemoryV1()
    family_id = "F_PROPORTIONAL"
    
    # 3 total evidence (1+2+0)
    family_diag_evidence[family_id] = {
        "EDGE_BAND_PROXIMITY": 1,
        "JOIN_PERSISTENCE": 2,
        "REUNION_FRICTION": 0
    }
    
    memory._interpret_evidence(family_id)
    
    conf = family_diag_confidence[family_id]
    assert conf["EDGE_BAND_PROXIMITY"] == pytest.approx(0.3333, abs=0.001)
    assert conf["JOIN_PERSISTENCE"] == pytest.approx(0.6667, abs=0.001)
    assert conf["REUNION_FRICTION"] == 0.0

def test_single_cause_results_in_full_confidence():
    memory = NeutralFamilyMemoryV1()
    family_id = "F_SINGLE"
    
    family_diag_evidence[family_id] = {
        "EDGE_BAND_PROXIMITY": 5,
        "JOIN_PERSISTENCE": 0,
        "REUNION_FRICTION": 0
    }
    
    memory._interpret_evidence(family_id)
    
    conf = family_diag_confidence[family_id]
    assert conf["EDGE_BAND_PROXIMITY"] == 1.0
    assert conf["JOIN_PERSISTENCE"] == 0.0
    assert conf["REUNION_FRICTION"] == 0.0

def test_no_evidence_results_in_all_zeros():
    memory = NeutralFamilyMemoryV1()
    family_id = "F_NONE"
    
    # Empty or zero evidence
    family_diag_evidence[family_id] = {cause: 0 for cause in CAUSES}
    
    memory._interpret_evidence(family_id)
    
    conf = family_diag_confidence[family_id]
    for cause in CAUSES:
        assert conf[cause] == 0.0

def test_multiple_causes_remain_present_no_collapse():
    memory = NeutralFamilyMemoryV1()
    family_id = "F_MULTI"
    
    family_diag_evidence[family_id] = {
        "EDGE_BAND_PROXIMITY": 10,
        "JOIN_PERSISTENCE": 9,
        "REUNION_FRICTION": 1
    }
    
    memory._interpret_evidence(family_id)
    
    conf = family_diag_confidence[family_id]
    # Even though one is slightly higher, all are present
    assert conf["EDGE_BAND_PROXIMITY"] == 0.5
    assert conf["JOIN_PERSISTENCE"] == 0.45
    assert conf["REUNION_FRICTION"] == 0.05
    assert sum(conf.values()) == pytest.approx(1.0)
