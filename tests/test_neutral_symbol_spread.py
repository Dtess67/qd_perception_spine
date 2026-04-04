import pytest
from qd_perception.neutral_symbol_memory_v1 import NeutralSymbolMemoryV1
from qd_perception.neutral_symbol_identity_v1 import IdentityContractV1

def test_spread_calculation_at_mint():
    """Verify that spread (AAD) is correctly calculated when a symbol is minted."""
    memory = NeutralSymbolMemoryV1()
    region = "region_test"
    
    # 3 observations for the same region
    # Axis A: 0.5, 0.4, 0.6 -> Mean 0.5. AAD = (|0.5-0.5| + |0.4-0.5| + |0.6-0.5|) / 3 = (0+0.1+0.1)/3 = 0.0666...
    obs1 = {"axis_a": 0.5, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    obs2 = {"axis_a": 0.4, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    obs3 = {"axis_a": 0.6, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    
    memory.process_observation(region, 1.0, obs1, 1)
    memory.process_observation(region, 1.0, obs2, 2)
    decision = memory.process_observation(region, 1.0, obs3, 3)
    
    assert decision.status == "NEW"
    symbol_id = decision.symbol_id
    record = memory._records[symbol_id]
    
    # Check centroid (mint_signature)
    assert record.mint_signature["axis_a"] == pytest.approx(0.5)
    
    # Check spread (mint_spread) - Average Absolute Deviation
    # AAD for axis_a should be approx 0.0667
    assert record.mint_spread["axis_a"] == pytest.approx(0.06666, abs=1e-4)
    # Other axes should be 0.0 spread as they were all 0.1
    assert record.mint_spread["axis_b"] == pytest.approx(0.0)

def test_spread_distinction_similar_centroids():
    """Verify that two symbols with same centroid but different spread are distinguishable."""
    memory = NeutralSymbolMemoryV1()
    
    # Symbol 1: Tight spread
    reg1 = "reg_tight"
    obs_tight = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    for i in range(3):
        memory.process_observation(reg1, 1.0, obs_tight, i)
    
    sym1_id = memory._region_to_symbol[reg1]
    rec1 = memory._records[sym1_id]
    
    # Symbol 2: Loose spread
    reg2 = "reg_loose"
    obs_loose_1 = {"axis_a": 0.3, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    obs_loose_2 = {"axis_a": 0.7, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    obs_loose_3 = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    
    memory.process_observation(reg2, 1.0, obs_loose_1, 10)
    memory.process_observation(reg2, 1.0, obs_loose_2, 11)
    memory.process_observation(reg2, 1.0, obs_loose_3, 12)
    
    sym2_id = memory._region_to_symbol[reg2]
    rec2 = memory._records[sym2_id]
    
    # Both should have centroid 0.5 for axis_a
    assert rec1.mint_signature["axis_a"] == pytest.approx(0.5)
    assert rec2.mint_signature["axis_a"] == pytest.approx(0.5)
    
    # But spreads should differ significantly
    assert rec1.mint_spread["axis_a"] == pytest.approx(0.0)
    assert rec2.mint_spread["axis_a"] == pytest.approx(0.13333, abs=1e-4) # (|0.3-0.5| + |0.7-0.5| + |0.5-0.5|)/3 = (0.2+0.2+0)/3 = 0.1333

def test_current_spread_updates():
    """Verify that current_spread updates toward new observations."""
    memory = NeutralSymbolMemoryV1()
    reg = "reg_update"
    obs = {"axis_a": 0.5, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    
    # Mint with 0 spread
    for i in range(3):
        memory.process_observation(reg, 1.0, obs, i)
        
    sym_id = memory._region_to_symbol[reg]
    rec = memory._records[sym_id]
    assert rec.current_spread["axis_a"] == pytest.approx(0.0)
    
    # Observe a distant point
    obs_far = {"axis_a": 0.7, "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
    memory.process_observation(reg, 1.0, obs_far, 4)
    
    # current_signature moves: 0.5 * 0.9 + 0.7 * 0.1 = 0.52
    # deviation = |0.7 - 0.52| = 0.18
    # current_spread moves: 0.0 * 0.9 + 0.18 * 0.1 = 0.018
    assert rec.current_spread["axis_a"] == pytest.approx(0.018)
    assert rec.current_signature["axis_a"] == pytest.approx(0.52)
