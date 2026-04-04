import pytest
from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

def test_clear_family_join_with_persistence():
    """Verifies that a symbol within DISTANCE_THRESHOLD joins after persistence is met."""
    memory = NeutralFamilyMemoryV1()
    
    # Setup initial family with symbol sym_01
    sig_1 = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    spread_1 = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
    memory.join_or_create_family("sym_01", sig_1, spread_1, 5)
    
    # sym_02 is very close (dist 0.01), but needs persistence (threshold=2)
    sig_2 = {"axis_a": 0.11, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    spread_2 = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
    
    # First observation -> FAMILY_HOLD (requires persistence)
    decision_1 = memory.join_or_create_family("sym_02", sig_2, spread_2, 5)
    assert decision_1.status == "FAMILY_HOLD"
    assert decision_1.family_id == "fam_01"
    assert memory.get_family_for_symbol("sym_02") is None
    
    # Second observation -> JOIN_EXISTING_FAMILY (persistence met)
    decision_2 = memory.join_or_create_family("sym_02", sig_2, spread_2, 5)
    assert decision_2.status == "JOIN_EXISTING_FAMILY"
    assert decision_2.family_id == "fam_01"
    assert memory.get_family_for_symbol("sym_02") == "fam_01"

def test_borderline_family_hold():
    """Verifies that a symbol in the borderline band remains in FAMILY_HOLD."""
    memory = NeutralFamilyMemoryV1()
    
    # fam_01
    sig_1 = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    spread_1 = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
    memory.join_or_create_family("sym_01", sig_1, spread_1, 5)
    
    # sym_02 is in borderline band (dist ~0.2)
    # 0.15 (DISTANCE_THRESHOLD) < 0.2 < 0.25 (HOLD_THRESHOLD)
    sig_2 = {"axis_a": 0.9, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    # Distance = (0.8 + 0 + 0 + 0) / 4 = 0.2
    
    # Even with persistence, it earns a boundary status rather than joining
    for _ in range(2):
        decision = memory.join_or_create_family("sym_02", sig_2, spread_1, 5)
        assert decision.status == "FAMILY_HOLD"
            
    # Third hit earns EDGE status
    decision = memory.join_or_create_family("sym_02", sig_2, spread_1, 5)
    assert decision.status == "FAMILY_EDGE"
    
    assert memory.get_family_for_symbol("sym_02") is None

def test_clear_separation_no_family_match():
    """Verifies that a clearly distant symbol starts a new family."""
    memory = NeutralFamilyMemoryV1()
    
    # fam_01
    sig_1 = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    memory.join_or_create_family("sym_01", sig_1, sig_1, 5)
    
    # sym_02 is far away (dist 0.8)
    sig_2 = {"axis_a": 0.9, "axis_b": 0.9, "axis_c": 0.9, "axis_d": 0.9}
    
    decision = memory.join_or_create_family("sym_02", sig_2, sig_1, 5)
    assert decision.status == "NEW_FAMILY"
    assert decision.family_id == "fam_02"
    assert memory.get_family_for_symbol("sym_02") == "fam_02"

def test_symbol_identity_preserved_during_hold():
    """Ensures that being in FAMILY_HOLD does not overwrite the symbol's own ID or state."""
    memory = NeutralFamilyMemoryV1()
    
    # Setup a family
    memory.join_or_create_family("sym_01", {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}, {}, 5)
    
    # Borderline symbol
    sig_border = {"axis_a": 0.3, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1} # dist 0.05
    # Wait, 0.3-0.1 = 0.2. (0.2+0+0+0)/4 = 0.05. 0.05 < 0.15. So it is JOIN_DISTANCE.
    
    # Let's use dist 0.2 again
    sig_hold = {"axis_a": 0.9, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1} # dist 0.2
    
    decision = memory.join_or_create_family("sym_hold_test", sig_hold, {}, 5)
    assert decision.status == "FAMILY_HOLD"
    assert decision.symbol_id == "sym_hold_test"
    assert memory.get_family_for_symbol("sym_hold_test") is None
