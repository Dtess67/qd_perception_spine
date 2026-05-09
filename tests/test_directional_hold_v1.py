import unittest
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1, family_hold_directions, HOLD_THRESHOLD, ASYMMETRY_THRESHOLD, FamilyDecision,
    family_hold_history, family_hold_trend, family_drift_score
)
from qd_perception_spine.entrenchment_v1 import family_suspect

class TestDirectionalSuspectFlagging(unittest.TestCase):
    def setUp(self):
        # Reset global state before each test
        family_hold_directions.clear()
        family_hold_history.clear()
        family_hold_trend.clear()
        family_drift_score.clear()
        family_suspect.clear()
        self.mem = NeutralFamilyMemoryV1()

    def _sig(self, v: float) -> dict[str, float]:
        return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}

    def _spr(self, v: float) -> dict[str, float]:
        return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}

    def test_symmetric_hold_does_not_trigger_suspicion_below_threshold(self):
        """1. Symmetric HOLD does NOT trigger suspicion (below total threshold)"""
        # Create a family
        self.mem.join_or_create_family("sym_init", self._sig(0.1), self._spr(0.05), 10)
        fam_id = "fam_01"
        
        # Distance for JOIN_PERSISTENCE: (0.10, 0.15) -> sig 0.1 + 0.12 = 0.22 (dist 0.12)
        # Distance for EDGE_BAND_PROXIMITY: [0.15, 0.25) -> sig 0.1 + 0.20 = 0.30 (dist 0.20)
        
        for i in range(2):
            self.mem.join_or_create_family(f"sym_h1_unique_{i}", self._sig(0.22), self._spr(0.05), 1)
            self.mem.join_or_create_family(f"sym_h2_unique_{i}", self._sig(0.30), self._spr(0.05), 1)
            
        self.assertFalse(family_suspect.get(fam_id, False))
        self.assertEqual(family_hold_directions[fam_id].get("JOIN_PERSISTENCE"), 2)
        self.assertEqual(family_hold_directions[fam_id].get("EDGE_BAND_PROXIMITY"), 2)

    def test_strong_imbalance_does_trigger_suspicion(self):
        """2. Strong imbalance DOES trigger suspicion"""
        # Create a family
        self.mem.join_or_create_family("sym_init", self._sig(0.1), self._spr(0.05), 10)
        fam_id = "fam_01"
        
        # ASYMMETRY_THRESHOLD = 3
        # 3 hits in one direction, 0 in others -> 3-0 = 3.
        # Use UNIQUE symbols to stay in FAMILY_HOLD
        
        for i in range(3):
            self.mem.join_or_create_family(f"sym_h_unique_{i}", self._sig(0.30), self._spr(0.05), 1)
            
        self.assertTrue(family_suspect.get(fam_id, False))
        self.assertEqual(family_hold_directions[fam_id].get("EDGE_BAND_PROXIMITY"), 3)

    def test_decay_reduces_asymmetry(self):
        """3. Decay reduces asymmetry"""
        # Create a family
        self.mem.join_or_create_family("sym_init", self._sig(0.1), self._spr(0.05), 10)
        fam_id = "fam_01"
        
        # Trigger suspicion via asymmetry using UNIQUE symbols
        for i in range(3):
            self.mem.join_or_create_family(f"sym_h_unique_{i}", self._sig(0.30), self._spr(0.05), 1)
        self.assertTrue(family_suspect.get(fam_id, False))
        
        # Trigger decay via successful JOIN
        # sym_init is already in fam_01, sending it again at close distance triggers JOIN
        self.mem.join_or_create_family("sym_init", self._sig(0.12), self._spr(0.05), 1)
        
        # Count should be 2, asymmetry 2-0 = 2 < 3. Suspect should clear.
        self.assertFalse(family_suspect.get(fam_id, False))
        self.assertEqual(family_hold_directions[fam_id].get("EDGE_BAND_PROXIMITY"), 2)

    def test_multi_family_isolation_works(self):
        """4. Multi-family isolation works"""
        self.mem.join_or_create_family("sym_a", self._sig(0.1), self._spr(0.05), 10) # fam_01
        self.mem.join_or_create_family("sym_b", self._sig(0.8), self._spr(0.05), 10) # fam_02
        
        # Imbalance for fam_01 using UNIQUE symbols
        for i in range(3):
            self.mem.join_or_create_family(f"sym_h1_unique_{i}", self._sig(0.30), self._spr(0.05), 1)
        
        # Symmetric for fam_02 using UNIQUE symbols
        self.mem.join_or_create_family("sym_h2_unique_a", self._sig(0.92), self._spr(0.05), 1) # dist 0.12 -> JOIN_PERSISTENCE
        self.mem.join_or_create_family("sym_h2_unique_b", self._sig(1.00), self._spr(0.05), 1) # dist 0.20 -> EDGE_BAND_PROXIMITY
        
        self.assertTrue(family_suspect.get("fam_01", False))
        self.assertFalse(family_suspect.get("fam_02", False))

if __name__ == '__main__':
    unittest.main()
