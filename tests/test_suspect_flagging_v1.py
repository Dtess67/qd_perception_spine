import unittest
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1, family_hold_directions, HOLD_THRESHOLD, ASYMMETRY_THRESHOLD,
    family_hold_history, family_hold_trend, family_drift_score
)
from qd_perception_spine.entrenchment_v1 import family_suspect

class TestSuspectFlaggingV1(unittest.TestCase):
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

    def test_hold_accumulation_triggers_suspect_flag(self):
        """1. HOLD accumulation triggers suspect flag"""
        # Create a family
        self.mem.join_or_create_family("sym_init", self._sig(0.1), self._spr(0.05), 10)
        fam_id = "fam_01"
        
        # Trigger HOLD events
        hold_sig = self._sig(0.30)
        
        for i in range(HOLD_THRESHOLD):
            self.mem.join_or_create_family(f"sym_hold_{i}", hold_sig, self._spr(0.05), 1)
            # ASYMMETRY_THRESHOLD is 3. Since we only use ONE direction, 
            # suspect will be True at i=2 (3rd hit).
            if i < ASYMMETRY_THRESHOLD - 1:
                self.assertFalse(family_suspect.get(fam_id, False), f"Failed at i={i}")
            else:
                self.assertTrue(family_suspect.get(fam_id, False), f"Failed at i={i}")
        
        total_hold = sum(family_hold_directions[fam_id].values())
        self.assertEqual(total_hold, HOLD_THRESHOLD)

    def test_non_hold_events_reduce_count(self):
        """2. Non-HOLD events reduce count"""
        # Create a family
        self.mem.join_or_create_family("sym_init", self._sig(0.1), self._spr(0.05), 10)
        fam_id = "fam_01"
        
        # Accumulate some holds
        hold_sig = self._sig(0.30)
        for i in range(3):
            self.mem.join_or_create_family(f"sym_hold_{i}", hold_sig, self._spr(0.05), 1)
        
        total_hold = sum(family_hold_directions[fam_id].values())
        self.assertEqual(total_hold, 3)
        
        # Trigger JOIN event (NON-HOLD)
        join_sig = self._sig(0.12) # dist 0.02 < 0.15
        self.mem.join_or_create_family("sym_init", join_sig, self._spr(0.05), 1)
        
        total_hold = sum(family_hold_directions[fam_id].values())
        self.assertEqual(total_hold, 2)
        self.assertEqual(family_hold_directions[fam_id]["EDGE_BAND_PROXIMITY"], 2)

    def test_flag_clears_when_count_drops_below_threshold(self):
        """3. Flag clears when count drops below threshold"""
        # Create a family
        self.mem.join_or_create_family("sym_init", self._sig(0.1), self._spr(0.05), 10)
        fam_id = "fam_01"
        
        # Reach asymmetry threshold (3)
        hold_sig = self._sig(0.30)
        for i in range(3):
            self.mem.join_or_create_family(f"sym_hold_{i}", hold_sig, self._spr(0.05), 1)
        
        self.assertTrue(family_suspect.get(fam_id, False))
        
        # One non-hold event should clear it (count 3 -> 2, asymmetry 3 -> 2 < 3)
        join_sig = self._sig(0.12)
        self.mem.join_or_create_family("sym_init", join_sig, self._spr(0.05), 1)
        
        self.assertFalse(family_suspect.get(fam_id, False))
        total_hold = sum(family_hold_directions[fam_id].values())
        self.assertEqual(total_hold, 2)

    def test_multiple_families_tracked_independently(self):
        """4. Multiple families tracked independently"""
        self.mem.join_or_create_family("sym_a", self._sig(0.1), self._spr(0.05), 10) # fam_01
        self.mem.join_or_create_family("sym_b", self._sig(0.8), self._spr(0.05), 10) # fam_02
        
        # HOLD for fam_01
        self.mem.join_or_create_family("sym_hold_a", self._sig(0.30), self._spr(0.05), 1)
        # HOLD for fam_02
        self.mem.join_or_create_family("sym_hold_b", self._sig(0.60), self._spr(0.05), 1)
        
        total_hold_1 = sum(family_hold_directions["fam_01"].values())
        total_hold_2 = sum(family_hold_directions["fam_02"].values())
        self.assertEqual(total_hold_1, 1)
        self.assertEqual(total_hold_2, 1)

if __name__ == '__main__':
    unittest.main()
