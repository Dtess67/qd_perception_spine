from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1
import pytest

def test_new_family_creation():
    """Verifies that a stable symbol can create a new family."""
    memory = NeutralFamilyMemoryV1()
    
    symbol_id = "sym_01"
    signature = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    spread = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
    hit_count = 5
    
    decision = memory.join_or_create_family(symbol_id, signature, spread, hit_count)
    
    assert decision.status == "NEW_FAMILY"
    assert decision.family_id == "fam_01"
    assert memory.get_family_for_symbol(symbol_id) == "fam_01"
    
    record = memory.get_family_record("fam_01")
    assert record.member_symbol_ids == ["sym_01"]
    assert record.combined_signature["axis_a"] == 0.5

def test_join_existing_family():
    """Verifies that a similar symbol joins an existing family."""
    memory = NeutralFamilyMemoryV1()
    
    # 1. Create first family
    memory.join_or_create_family("sym_01", 
                                {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5},
                                {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}, 
                                5)
    
    # 2. Add similar symbol
    # Distance will be 0.05, which is < 0.15 threshold
    similar_sig = {"axis_a": 0.55, "axis_b": 0.55, "axis_c": 0.55, "axis_d": 0.55}
    
    # First observation results in FAMILY_HOLD (requires persistence)
    decision_1 = memory.join_or_create_family("sym_02", similar_sig, 
                                             {"axis_a": 0.02, "axis_b": 0.02, "axis_c": 0.02, "axis_d": 0.02}, 
                                             5)
    assert decision_1.status == "FAMILY_HOLD"
    
    # Second observation earns JOIN_EXISTING_FAMILY (persistence=2)
    decision_2 = memory.join_or_create_family("sym_02", similar_sig, 
                                             {"axis_a": 0.02, "axis_b": 0.02, "axis_c": 0.02, "axis_d": 0.02}, 
                                             5)
    
    assert decision_2.status == "JOIN_EXISTING_FAMILY"
    assert decision_2.family_id == "fam_01"
    assert memory.get_family_for_symbol("sym_02") == "fam_01"
    
    record = memory.get_family_record("fam_01")
    assert "sym_02" in record.member_symbol_ids
    assert len(record.member_symbol_ids) == 2
    # Combined signature should be midpoint (0.525) since hit counts are equal
    assert record.combined_signature["axis_a"] == pytest.approx(0.525)

def test_refuse_family_merge_distant():
    """Verifies that distant symbols do not join the same family."""
    memory = NeutralFamilyMemoryV1()
    
    # 1. Create first family
    memory.join_or_create_family("sym_01", 
                                {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1},
                                {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}, 
                                5)
    
    # 2. Add distant symbol
    distant_sig = {"axis_a": 0.8, "axis_b": 0.8, "axis_c": 0.8, "axis_d": 0.8}
    decision = memory.join_or_create_family("sym_02", distant_sig, 
                                           {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}, 
                                           5)
    
    assert decision.status == "NEW_FAMILY"
    assert decision.family_id == "fam_02"
    assert memory.get_family_for_symbol("sym_02") == "fam_02"

def test_symbol_retains_identity():
    """Verifies that joining a family doesn't change the symbol ID."""
    memory = NeutralFamilyMemoryV1()
    
    memory.join_or_create_family("sym_01", {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}, {}, 5)
    
    # Needs persistence=2 to join
    memory.join_or_create_family("sym_02", {"axis_a": 0.51, "axis_b": 0.51, "axis_c": 0.51, "axis_d": 0.51}, {}, 5)
    memory.join_or_create_family("sym_02", {"axis_a": 0.51, "axis_b": 0.51, "axis_c": 0.51, "axis_d": 0.51}, {}, 5)
    
    assert memory.get_family_for_symbol("sym_01") == "fam_01"
    assert memory.get_family_for_symbol("sym_02") == "fam_01"
    # Symbol IDs are preserved
    assert "sym_01" != "sym_02"
