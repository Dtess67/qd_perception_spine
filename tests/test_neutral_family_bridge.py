"""
Tests for persistent multi-family bridge and single-family edge detection.
"""

import pytest
from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

def test_bridge_persistence_earning():
    """Verify that repeated tension earns a persistent bridge status."""
    memory = NeutralFamilyMemoryV1()
    
    # Setup two families
    sig_a = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    sig_b = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    spread = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
    
    memory.join_or_create_family("sym_a", sig_a, spread, 10)
    memory.join_or_create_family("sym_b", sig_b, spread, 10)
    
    # Place symbol in perfect tension
    sig_bridge = {"axis_a": 0.3, "axis_b": 0.3, "axis_c": 0.3, "axis_d": 0.3}
    
    # Threshold is 3 hits
    for i in range(2):
        decision = memory.join_or_create_family("sym_bridge", sig_bridge, spread, 1)
        assert decision.status == "FAMILY_TENSION"
        assert memory.get_boundary_status("sym_bridge") is None
        
    # Third hit should earn it
    decision = memory.join_or_create_family("sym_bridge", sig_bridge, spread, 1)
    assert decision.status == "FAMILY_BRIDGE"
    assert memory.get_boundary_status("sym_bridge") == "FAMILY_BRIDGE"

def test_edge_persistence_earning():
    """Verify that repeated borderline proximity earns a persistent edge status."""
    memory = NeutralFamilyMemoryV1()
    
    # Setup one family
    sig_a = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    spread = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
    memory.join_or_create_family("sym_a", sig_a, spread, 10)
    
    # Place symbol in borderline band (dist 0.2, between 0.15 and 0.25)
    sig_edge = {"axis_a": 0.7, "axis_b": 0.7, "axis_c": 0.7, "axis_d": 0.7}
    
    # Threshold is 3 hits
    for i in range(2):
        decision = memory.join_or_create_family("sym_edge", sig_edge, spread, 1)
        assert decision.status == "FAMILY_HOLD"
        assert memory.get_boundary_status("sym_edge") is None
        
    # Third hit should earn it
    decision = memory.join_or_create_family("sym_edge", sig_edge, spread, 1)
    assert decision.status == "FAMILY_EDGE"
    assert memory.get_boundary_status("sym_edge") == "FAMILY_EDGE"

def test_decisive_lead_overrides_bridge():
    """Verify that a decisive lead allows family assignment even for bridge-qualified symbols."""
    memory = NeutralFamilyMemoryV1()
    
    sig_a = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    sig_b = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    spread = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
    memory.join_or_create_family("sym_a", sig_a, spread, 10)
    memory.join_or_create_family("sym_b", sig_b, spread, 10)
    
    # 1. Establish bridge
    sig_bridge = {"axis_a": 0.3, "axis_b": 0.3, "axis_c": 0.3, "axis_d": 0.3}
    for i in range(3):
        memory.join_or_create_family("sym_test", sig_bridge, spread, 1)
    assert memory.get_boundary_status("sym_test") == "FAMILY_BRIDGE"
    
    # 2. Decisive lead toward A (center 0.1)
    sig_near_a = {"axis_a": 0.11, "axis_b": 0.11, "axis_c": 0.11, "axis_d": 0.11}
    # Persistence for join is 2
    decision = memory.join_or_create_family("sym_test", sig_near_a, spread, 1)
    assert decision.status == "FAMILY_HOLD" # Persistence required
    
    decision = memory.join_or_create_family("sym_test", sig_near_a, spread, 1)
    assert decision.status == "JOIN_EXISTING_FAMILY"
    assert decision.family_id == "fam_01"
    assert memory.get_family_for_symbol("sym_test") == "fam_01"

def test_symbol_identity_remains_distinct():
    """Verify that earning bridge/edge does not overwrite symbol identity."""
    memory = NeutralFamilyMemoryV1()
    # Earning edge for sym_edge_01
    sig_a = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    spread = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
    memory.join_or_create_family("sym_a", sig_a, spread, 10)
    
    sig_edge = {"axis_a": 0.7, "axis_b": 0.7, "axis_c": 0.7, "axis_d": 0.7}
    for i in range(3):
        memory.join_or_create_family("sym_test_id", sig_edge, spread, 1)
    
    assert memory.get_boundary_status("sym_test_id") == "FAMILY_EDGE"
    assert memory.get_family_for_symbol("sym_test_id") is None
    # ID is preserved as caller intended
    assert "sym_test_id" not in memory._symbol_to_family
