import pytest
from qd_perception.pattern_family_analyzer import (
    PatternFamilyAnalyzer, 
    PatternPlacement
)

def test_stable_family_earns_glyph():
    """
    Verify that a repeated consistent pattern earns a glyph ID.
    """
    analyzer = PatternFamilyAnalyzer()
    family_id = "family_gradual_rise"
    
    # Record 3 identical placements (meets both thresholds)
    for i in range(3):
        placement = PatternPlacement(
            f"run_{i}", i, "region_shift_mid", 0.5, 0.5, 0.5, 0.5
        )
        analyzer.record_placement(family_id, placement)
        
    summary = analyzer.summarize_family(family_id)
    
    assert summary.placement_count == 3
    assert summary.stability_score == 1.0
    assert summary.dominant_region_id == "region_shift_mid"
    assert summary.glyph_id == "glyph_01"  # Deterministic mapping for this ID
    assert "assigned glyph_01" in summary.rationale

def test_insufficient_placements_no_glyph():
    """
    Verify that even a 100% stable pattern does not earn a glyph if count is too low.
    """
    analyzer = PatternFamilyAnalyzer()
    family_id = "family_spike"
    
    # Record only 2 placements (threshold is 3)
    for i in range(2):
        placement = PatternPlacement(
            f"run_{i}", i, "region_spike_high", 0.9, 0.9, 0.1, 0.9
        )
        analyzer.record_placement(family_id, placement)
        
    summary = analyzer.summarize_family(family_id)
    
    assert summary.placement_count == 2
    assert summary.stability_score == 1.0
    assert summary.glyph_id is None
    assert "Not enough data for glyph" in summary.rationale

def test_low_stability_no_glyph():
    """
    Verify that scattered patterns do not earn a glyph even if count is high.
    """
    analyzer = PatternFamilyAnalyzer()
    family_id = "family_mixed_noise"
    
    # Record 4 different regions (stability 0.25, threshold 0.7)
    regions = ["region_a", "region_b", "region_c", "region_d"]
    for i, region in enumerate(regions):
        placement = PatternPlacement(
            f"run_{i}", 0, region, 0.0, 0.0, 0.0, 0.0
        )
        analyzer.record_placement(family_id, placement)
        
    summary = analyzer.summarize_family(family_id)
    
    assert summary.placement_count == 4
    assert summary.stability_score == 0.25
    assert summary.glyph_id is None
    assert "Stability too low for glyph" in summary.rationale

def test_stability_clamping():
    """
    Ensure stability score stays in [0.0, 1.0].
    """
    analyzer = PatternFamilyAnalyzer()
    family_id = "test_family"
    
    # 0 placements
    summary = analyzer.summarize_family(family_id)
    assert summary.stability_score == 0.0
    
    # Mixed placements
    analyzer.record_placement(family_id, PatternPlacement("r1", 0, "a", 0, 0, 0, 0))
    analyzer.record_placement(family_id, PatternPlacement("r2", 0, "b", 0, 0, 0, 0))
    
    summary = analyzer.summarize_family(family_id)
    assert 0.0 <= summary.stability_score <= 1.0

def test_marginal_stability_earns_glyph():
    """
    Verify stability just at the threshold (e.g. 3/4 = 0.75 >= 0.7) earns a glyph.
    """
    analyzer = PatternFamilyAnalyzer()
    family_id = "family_stable"
    
    # 3 matching, 1 different = 0.75 stability
    for i in range(3):
        analyzer.record_placement(family_id, PatternPlacement(f"match_{i}", 0, "region_steady_low", 0, 0, 0, 0))
    analyzer.record_placement(family_id, PatternPlacement("mismatch", 0, "region_other", 0, 0, 0, 0))
    
    summary = analyzer.summarize_family(family_id)
    assert summary.placement_count == 4
    assert summary.stability_score == 0.75
    assert summary.glyph_id == "glyph_03"
