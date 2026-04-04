from qd_perception.delta_frame import DeltaFrame
from qd_perception.feature_frame import FeatureExtractor

def test_intensity_classification():
    """
    Tests that magnitude is correctly translated into low, medium, or high intensity.
    """
    extractor = FeatureExtractor()
    
    # Low Intensity (below 0.5)
    df_low = DeltaFrame("s", "c", 10.0, 10.1, 0.1, "rising", 0.1, 0.0, False)
    assert extractor.from_delta(df_low).intensity == "low"
    
    # Medium Intensity (between 0.5 and 2.0)
    df_med = DeltaFrame("s", "c", 10.0, 11.0, 1.0, "rising", 1.0, 0.0, False)
    assert extractor.from_delta(df_med).intensity == "medium"
    
    # High Intensity (above 2.0)
    df_high = DeltaFrame("s", "c", 10.0, 13.0, 3.0, "rising", 3.0, 0.0, False)
    assert extractor.from_delta(df_high).intensity == "high"

def test_pattern_classification():
    """
    Tests pattern classification (spike vs drift vs steady).
    """
    extractor = FeatureExtractor()
    
    # Steady Pattern
    df_steady = DeltaFrame("s", "c", 10.0, 10.0, 0.0, "steady", 0.0, 0.0, False)
    assert extractor.from_delta(df_steady).pattern == "steady"
    
    # Drift Pattern (moderate change)
    df_drift = DeltaFrame("s", "c", 10.0, 11.0, 1.0, "rising", 1.0, 0.0, False)
    assert extractor.from_delta(df_drift).pattern == "drift"
    
    # Spike Pattern (high magnitude change)
    df_spike = DeltaFrame("s", "c", 10.0, 15.0, 5.0, "rising", 5.0, 0.0, False)
    assert extractor.from_delta(df_spike).pattern == "spike"

def test_novelty_labeling():
    """
    Verifies that the is_novel flag is correctly mapped to a string label.
    """
    extractor = FeatureExtractor()
    
    # Novel
    df_novel = DeltaFrame("s", "c", 0.0, 10.0, 10.0, "rising", 10.0, 0.0, True)
    assert extractor.from_delta(df_novel).novelty == "novel"
    
    # Familiar
    df_fam = DeltaFrame("s", "c", 10.0, 10.1, 0.1, "rising", 0.1, 0.0, False)
    assert extractor.from_delta(df_fam).novelty == "familiar"
