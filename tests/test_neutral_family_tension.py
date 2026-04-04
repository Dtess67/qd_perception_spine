import pytest
from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

def test_single_family_match_no_tension():
    """Verify that a symbol near only one family joins as expected."""
    memory = NeutralFamilyMemoryV1()
    
    # Create one family
    sig_a = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    spread_a = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
    memory.join_or_create_family("sym_a", sig_a, spread_a, 10)
    
    # Evaluate a symbol that is close to the only family
    sig_test = {"axis_a": 0.12, "axis_b": 0.12, "axis_c": 0.12, "axis_d": 0.12}
    spread_test = spread_a.copy()
    
    # First hit -> FAMILY_HOLD (due to persistence threshold=2)
    decision1 = memory.evaluate_symbol("sym_test", sig_test, spread_test)
    assert decision1.status == "FAMILY_HOLD"
    memory.join_or_create_family("sym_test", sig_test, spread_test, 1)
    
    # Second hit -> JOIN_EXISTING_FAMILY
    decision2 = memory.evaluate_symbol("sym_test", sig_test, spread_test)
    assert decision2.status == "JOIN_EXISTING_FAMILY"
    assert decision2.family_id == "fam_01"

def test_multi_family_tension_hold():
    """Verify that a symbol near two families with insufficient margin triggers tension."""
    memory = NeutralFamilyMemoryV1()
    
    # Create two families far enough to be separate
    # fam_01 center at 0.1
    sig_1 = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    memory.join_or_create_family("sym_1", sig_1, {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}, 10)

    # fam_02 center at 0.5 (Distance 0.4 > 0.25)
    sig_2 = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    memory.join_or_create_family("sym_2", sig_2, {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}, 10)

    # Test symbol at 0.3 (exactly in the middle)
    # Distance to both is 0.2. Margin = 0.0 < 0.05
    # Both are within HOLD_THRESHOLD (0.25)
    sig_test = {"axis_a": 0.3, "axis_b": 0.3, "axis_c": 0.3, "axis_d": 0.3}
    decision = memory.evaluate_symbol("sym_test", sig_test, sig_1)

    assert decision.status == "FAMILY_TENSION"
    assert decision.family_id is None
    assert "Structural tension detected" in decision.rationale

def test_multi_family_decisive_margin_wins():
    """Verify that a symbol near two families with decisive margin joins the stronger family."""
    memory = NeutralFamilyMemoryV1()
    
    # fam_01 at 0.1
    sig_1 = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    memory.join_or_create_family("sym_1", sig_1, {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}, 10)
    
    # fam_02 at 0.6
    sig_2 = {"axis_a": 0.6, "axis_b": 0.6, "axis_c": 0.6, "axis_d": 0.6}
    memory.join_or_create_family("sym_2", sig_2, {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}, 10)
    
    # Test symbol at 0.15
    # Dist to fam_01 = 0.05
    # Dist to fam_02 = 0.45 (Outside HOLD_THRESHOLD)
    # No tension, just join fam_01
    sig_test = {"axis_a": 0.15, "axis_b": 0.15, "axis_c": 0.15, "axis_d": 0.15}
    
    # Persistence 1 -> HOLD
    memory.join_or_create_family("sym_test", sig_test, sig_1, 1)
    # Persistence 2 -> JOIN fam_01
    decision = memory.join_or_create_family("sym_test", sig_test, sig_1, 1)
    
    assert decision.status == "JOIN_EXISTING_FAMILY"
    assert decision.family_id == "fam_01"

def test_no_family_match_separation():
    """Verify that a symbol near no family remains unassigned."""
    memory = NeutralFamilyMemoryV1()
    
    # fam_01 at 0.1
    sig_1 = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    memory.join_or_create_family("sym_1", sig_1, sig_1, 10)
    
    # symbol at 0.5 (dist 0.4 > 0.25)
    sig_test = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    decision = memory.evaluate_symbol("sym_test", sig_test, sig_1)
    
    assert decision.status == "NEW_FAMILY"
