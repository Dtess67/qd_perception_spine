import pytest
from qd_perception.symbol_memory import SymbolMemory

def test_symbol_earning_after_hits():
    # Use thresholds 2 hits, 0.7 stability
    mem = SymbolMemory(hit_threshold=2, stability_threshold=0.7)
    
    # 1. First sight
    entry = mem.observe("region_a", stability_score=0.8, event_index=0)
    assert entry.symbol_id.startswith("provisional_")
    assert entry.hit_count == 1
    assert mem.get_symbol_for_region("region_a") is None
    
    # 2. Second sight (passes threshold)
    entry = mem.observe("region_a", stability_score=0.8, event_index=1)
    assert entry.symbol_id == "sym_01"
    assert entry.hit_count == 2
    assert mem.get_symbol_for_region("region_a") == "sym_01"

def test_symbol_not_earned_due_to_low_stability():
    mem = SymbolMemory(hit_threshold=2, stability_threshold=0.9)
    
    # Sight 1
    mem.observe("region_a", stability_score=0.5, event_index=0)
    # Sight 2
    entry = mem.observe("region_a", stability_score=0.5, event_index=1)
    
    # Should not have earned a stable symbol yet
    assert entry.symbol_id.startswith("provisional_")
    assert mem.get_symbol_for_region("region_a") is None

def test_symbol_reuse():
    mem = SymbolMemory(hit_threshold=1, stability_threshold=0.5)
    
    # 1. Earn symbol
    mem.observe("region_a", stability_score=0.8, event_index=0)
    sid1 = mem.get_symbol_for_region("region_a")
    assert sid1 is not None
    
    # 2. Re-observe, same symbol should persist
    mem.observe("region_a", stability_score=0.8, event_index=1)
    sid2 = mem.get_symbol_for_region("region_a")
    assert sid1 == sid2

def test_different_regions_get_different_symbols():
    mem = SymbolMemory(hit_threshold=1, stability_threshold=0.1)
    
    mem.observe("region_a", stability_score=0.5, event_index=0)
    sid_a = mem.get_symbol_for_region("region_a")
    
    mem.observe("region_b", stability_score=0.5, event_index=1)
    sid_b = mem.get_symbol_for_region("region_b")
    
    assert sid_a.startswith("sym_")
    assert sid_b.startswith("sym_")
    assert sid_a != sid_b

def test_stability_averaging():
    mem = SymbolMemory(hit_threshold=3, stability_threshold=0.7)
    
    # Start high
    mem.observe("region_a", stability_score=1.0, event_index=0)
    # Dip low
    mem.observe("region_a", stability_score=0.4, event_index=1)
    # Average is 0.7
    entry = mem.observe("region_a", stability_score=0.7, event_index=2)
    # Simple averaging ( ( (1.0 + 0.4)/2 + 0.7 ) / 2 ) = ( 0.7 + 0.7 ) / 2 = 0.7
    
    assert entry.stability_score == pytest.approx(0.7)
    assert entry.symbol_id == "sym_01"
