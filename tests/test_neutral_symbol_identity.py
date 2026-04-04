import pytest
from qd_perception.neutral_symbol_identity_v1 import IdentityContractV1
from qd_perception.neutral_symbol_memory_v1 import NeutralSymbolMemoryV1

def test_symbol_earning_from_repetition():
    """Verify that a region earns a symbol after enough stable repetitions."""
    memory = NeutralSymbolMemoryV1()
    region = "region_test"
    axes = {"axis_a": 0.1, "axis_b": 0.2, "axis_c": 0.8, "axis_d": 0.1}
    
    # First 2 observations should be NEW but with no symbol_id (pending)
    for i in range(2):
        decision = memory.process_observation(region, 0.9, axes, i)
        assert decision.status == "NEW"
        assert decision.symbol_id is None
        
    # 3rd observation should earn the symbol (THRESHOLD is 3)
    decision = memory.process_observation(region, 0.9, axes, 2)
    assert decision.status == "NEW"
    assert decision.symbol_id == "sym_01"
    assert "earned persistent identity" in decision.rationale

def test_symbol_reuse():
    """Verify that a stable recurring region reuses the same symbol."""
    memory = NeutralSymbolMemoryV1()
    region = "region_test"
    axes = {"axis_a": 0.1, "axis_b": 0.2, "axis_c": 0.8, "axis_d": 0.1}
    
    # Reach stable state
    for i in range(3):
        memory.process_observation(region, 0.9, axes, i)
        
    # 4th observation should match existing
    decision = memory.process_observation(region, 0.9, axes, 3)
    assert decision.status == "MATCH_EXISTING"
    assert decision.symbol_id == "sym_01"

def test_unstable_structure_no_symbol():
    """Verify that low stability prevents symbol earning."""
    memory = NeutralSymbolMemoryV1()
    region = "region_unstable"
    axes = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    
    # Even with many hits, if stability is low, status is UNSTABLE
    for i in range(5):
        decision = memory.process_observation(region, 0.4, axes, i)
        assert decision.status == "UNSTABLE"
        assert decision.symbol_id is None

def test_distinct_structures_different_ids():
    """Verify that different regions earn different symbol IDs."""
    memory = NeutralSymbolMemoryV1()
    
    # Region 1 earns sym_01
    for i in range(3):
        memory.process_observation("region_1", 0.9, {"axis_a": 0.1}, i)
    
    # Region 2 earns sym_02
    for i in range(3):
        decision = memory.process_observation("region_2", 0.9, {"axis_a": 0.9}, i + 3)
        
    assert decision.symbol_id == "sym_02"
    assert len(memory.get_active_records()) == 2

def test_drift_split_behavior():
    """Verify that significant persistent drift triggers a split."""
    memory = NeutralSymbolMemoryV1()
    region = "region_drift"
    
    # 1. Establish initial identity
    initial_axes = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    for i in range(3):
        memory.process_observation(region, 0.9, initial_axes, i)
    
    # 2. Introduce significant drift
    drifted_axes = {"axis_a": 0.9, "axis_b": 0.9, "axis_c": 0.9, "axis_d": 0.9}
    
    # First and second drifted observations should NOT trigger SPLIT (persistence threshold is 3)
    for i in range(3, 5):
        decision = memory.process_observation(region, 0.9, drifted_axes, i)
        assert decision.status == "MATCH_EXISTING"
        assert "observed structural drift counter" in decision.rationale
    
    # Third drifted observation should trigger SPLIT
    decision = memory.process_observation(region, 0.9, drifted_axes, 5)
    
    assert decision.status == "SPLIT"
    assert decision.symbol_id == "sym_02"
    assert "Split from sym_01" in decision.rationale

def test_original_identity_anchor_preservation():
    """Verify that repeated updates do not smear the original identity anchor."""
    memory = NeutralSymbolMemoryV1()
    region = "region_test"
    initial_axes = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    
    # Establish identity
    for i in range(3):
        memory.process_observation(region, 0.9, initial_axes, i)
        
    record = memory._records["sym_01"]
    original_mint = record.mint_signature.copy()
    
    # Slightly drift observations (within threshold)
    drifted_axes = {"axis_a": 0.2, "axis_b": 0.2, "axis_c": 0.2, "axis_d": 0.2}
    for i in range(3, 10):
        memory.process_observation(region, 0.9, drifted_axes, i)
        
    # mint_signature should remain EXACTLY as it was
    assert record.mint_signature == original_mint
    # current_signature should have moved
    assert record.current_signature != original_mint

def test_retired_is_reserved():
    """Verify that RETIRED is marked as reserved/unimplemented."""
    from qd_perception.neutral_symbol_identity_v1 import IdentityDecision
    # Check that docstrings mention it is reserved
    assert "RETIRED_RESERVED" in IdentityDecision.__doc__
