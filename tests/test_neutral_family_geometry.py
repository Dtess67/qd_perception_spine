import pytest
from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

def test_family_geometry_mint_and_current():
    """Verifies that a family stores its own center and spread, and preserves anchors."""
    memory = NeutralFamilyMemoryV1()
    
    symbol_id = "sym_01"
    signature = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    spread = {"axis_a": 0.05, "axis_b": 0.05, "axis_c": 0.05, "axis_d": 0.05}
    hit_count = 10
    
    # Mint family
    decision = memory.join_or_create_family(symbol_id, signature, spread, hit_count)
    assert decision.status == "NEW_FAMILY"
    fam_id = decision.family_id
    
    record = memory.get_family_record(fam_id)
    assert record.mint_signature == signature
    assert record.current_signature == signature
    assert record.mint_spread == spread
    assert record.current_spread == spread
    assert record.observation_count == 10
    
    # Join second symbol with different signature and spread
    symbol_2 = "sym_02"
    sig_2 = {"axis_a": 0.6, "axis_b": 0.6, "axis_c": 0.6, "axis_d": 0.6}
    spread_2 = {"axis_a": 0.15, "axis_b": 0.15, "axis_c": 0.15, "axis_d": 0.15}
    hits_2 = 10
    
    # We need persistence for joining
    for _ in range(memory.JOIN_PERSISTENCE_THRESHOLD):
        decision = memory.join_or_create_family(symbol_2, sig_2, spread_2, hits_2)
        
    assert decision.status == "JOIN_EXISTING_FAMILY"
    assert decision.family_id == fam_id
    
    # Verify current geometry updated, but mint (anchor) remained same
    record = memory.get_family_record(fam_id)
    assert record.mint_signature == signature # Unchanged
    assert record.mint_spread == spread       # Unchanged
    
    # current_signature should be (0.5*10 + 0.6*10) / 20 = 0.55
    assert record.current_signature["axis_a"] == pytest.approx(0.55)
    # current_spread should be (0.05*10 + 0.15*10) / 20 = 0.10
    assert record.current_spread["axis_a"] == pytest.approx(0.10)
    assert record.observation_count == 20

def test_family_geometry_distinguishes_distributions():
    """Verifies that families with different member distributions produce different spreads."""
    memory = NeutralFamilyMemoryV1()
    
    # Family 1: Tight (full axes to avoid accidental proximity on missing keys)
    d1 = memory.join_or_create_family(
        "s1",
        {"axis_a": 0.2, "axis_b": 0.2, "axis_c": 0.2, "axis_d": 0.2},
        {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01},
        10,
    )
    assert d1.status == "NEW_FAMILY"
    fam1 = d1.family_id

    # Family 2: Broad and far (ensures NEW_FAMILY, not HOLD)
    d2 = memory.join_or_create_family(
        "s2",
        {"axis_a": 0.8, "axis_b": 0.8, "axis_c": 0.8, "axis_d": 0.8},
        {"axis_a": 0.20, "axis_b": 0.20, "axis_c": 0.20, "axis_d": 0.20},
        10,
    )
    assert d2.status == "NEW_FAMILY"
    fam2 = d2.family_id
    
    rec1 = memory.get_family_record(fam1)
    rec2 = memory.get_family_record(fam2)
    
    assert rec1.current_spread["axis_a"] < rec2.current_spread["axis_a"]

def test_symbol_ids_distinct_from_family_geometry():
    """Ensures symbol IDs remain distinct while family geometry is tracked above them."""
    memory = NeutralFamilyMemoryV1()
    
    sig = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    spread = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    
    memory.join_or_create_family("sym_01", sig, spread, 5)
    
    # sym_02 joins
    for _ in range(memory.JOIN_PERSISTENCE_THRESHOLD):
        memory.join_or_create_family("sym_02", sig, spread, 5)
        
    record = memory.get_family_record("fam_01")
    assert "sym_01" in record.member_symbol_ids
    assert "sym_02" in record.member_symbol_ids
    assert len(record.member_symbol_ids) == 2
    
    assert memory.get_family_for_symbol("sym_01") == "fam_01"
    assert memory.get_family_for_symbol("sym_02") == "fam_01"
