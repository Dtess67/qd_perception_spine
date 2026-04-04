import unittest
from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

class TestNeutralFamilyFracture(unittest.TestCase):
    def setUp(self):
        self.mem = NeutralFamilyMemoryV1()
        # Tight signature
        self.sig_a = {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
        self.spread_a = {"axis_a": 0.05, "axis_b": 0.05, "axis_c": 0.05, "axis_d": 0.05}

    def test_coherent_family_no_fracture(self):
        """A family with tight members should not trigger fracture."""
        self.mem.join_or_create_family("sym_01", self.sig_a, self.spread_a, 10)
        # Add another very similar symbol
        sig_b = {"axis_a": 0.11, "axis_b": 0.11, "axis_c": 0.11, "axis_d": 0.11}
        self.mem.join_or_create_family("sym_02", sig_b, self.spread_a, 10)
        
        fam_id = self.mem.get_family_for_symbol("sym_01")
        record = self.mem.get_family_record(fam_id)
        
        self.assertIsNone(record.fracture_status)
        self.assertEqual(record.fracture_counter, 0)

    def test_overbroad_family_triggers_fracture_hold(self):
        """A family that becomes too broad should trigger FAMILY_FRACTURE_HOLD."""
        # Symbol 1
        self.mem.join_or_create_family("sym_01", self.sig_a, self.spread_a, 10)
        fam_id = self.mem.get_family_for_symbol("sym_01")
        
        # Symbol 2 is far enough to increase the combined spread significantly
        # but close enough to join (DISTANCE_THRESHOLD = 0.15)
        # sig_a is [0.1, 0.1, 0.1, 0.1]
        # if we add sig_c at [0.24, 0.24, 0.24, 0.24], dist is 0.14
        sig_c = {"axis_a": 0.24, "axis_b": 0.24, "axis_c": 0.24, "axis_d": 0.24}
        
        # We need to bypass persistence to join immediately for the test
        # or just repeat it. JOIN_PERSISTENCE_THRESHOLD is 2.
        self.mem.join_or_create_family("sym_02", sig_c, self.spread_a, 10)
        self.mem.join_or_create_family("sym_02", sig_c, self.spread_a, 10)
        
        record = self.mem.get_family_record(fam_id)
        # The weighted spread will increase. 
        # (0.05 * 10 + 0.05 * 10) / 20 = 0.05? 
        # Wait, the current_spread calculation in join_or_create_family 
        # only averages the input 'spread' parameter, not the distance between members.
        # AH! I should have used the spread to represent internal variation.
        # In my _check_for_fracture, I used record.current_spread.
        
        # Let's use a VERY broad spread for the second symbol to trigger over_broad.
        # MAX_COHERENCE_SPREAD is 0.35
        broad_spread = {"axis_a": 0.8, "axis_b": 0.8, "axis_c": 0.8, "axis_d": 0.8}
        
        # Reset memory for a clean start
        self.mem = NeutralFamilyMemoryV1()
        self.mem.join_or_create_family("sym_01", self.sig_a, broad_spread, 10)
        # Adding a second member to trigger _check_for_fracture (requires len >= 2)
        self.mem.join_or_create_family("sym_02", self.sig_a, broad_spread, 10)
        self.mem.join_or_create_family("sym_02", self.sig_a, broad_spread, 10)
        
        fam_id = self.mem.get_family_for_symbol("sym_01")
        record = self.mem.get_family_record(fam_id)
        
        self.assertEqual(record.fracture_status, "FAMILY_FRACTURE_HOLD")
        self.assertEqual(record.fracture_counter, 1)

    def test_fracture_persistence_reaches_split_ready(self):
        """Repeated over-broad observations should eventually reach FAMILY_SPLIT_READY."""
        broad_spread = {"axis_a": 0.8, "axis_b": 0.8, "axis_c": 0.8, "axis_d": 0.8}
        self.mem.join_or_create_family("sym_01", self.sig_a, broad_spread, 10)
        # FRACTURE_PERSISTENCE_THRESHOLD is 3
        
        # Observation 1
        self.mem.join_or_create_family("sym_02", self.sig_a, broad_spread, 10)
        self.mem.join_or_create_family("sym_02", self.sig_a, broad_spread, 10)
        fam_id = self.mem.get_family_for_symbol("sym_01")
        record = self.mem.get_family_record(fam_id)
        self.assertEqual(record.fracture_status, "FAMILY_FRACTURE_HOLD")
        
        # Observation 2
        # sym_03 joins
        sig_similar = {"axis_a": 0.101, "axis_b": 0.101, "axis_c": 0.101, "axis_d": 0.101}
        self.mem.join_or_create_family("sym_03", sig_similar, broad_spread, 10)
        self.mem.join_or_create_family("sym_03", sig_similar, broad_spread, 10)
        self.assertEqual(record.fracture_status, "FAMILY_FRACTURE_HOLD")
        self.assertEqual(record.fracture_counter, 2)
        
        # Observation 3
        # sym_04 joins
        self.mem.join_or_create_family("sym_04", sig_similar, broad_spread, 10)
        self.mem.join_or_create_family("sym_04", sig_similar, broad_spread, 10)
        self.assertEqual(record.fracture_status, "FAMILY_SPLIT_READY")
        self.assertEqual(record.fracture_counter, 3)

    def test_fracture_recovery(self):
        """If family becomes tight again, fracture counter should decrease."""
        broad_spread = {"axis_a": 0.8, "axis_b": 0.8, "axis_c": 0.8, "axis_d": 0.8}
        self.mem.join_or_create_family("sym_01", self.sig_a, broad_spread, 10)
        self.mem.join_or_create_family("sym_02", self.sig_a, broad_spread, 10)
        self.mem.join_or_create_family("sym_02", self.sig_a, broad_spread, 10)
        
        fam_id = self.mem.get_family_for_symbol("sym_01")
        record = self.mem.get_family_record(fam_id)
        self.assertEqual(record.fracture_counter, 1)
        
        # Add a very tight symbol with high hit_count to bring down the average spread
        tight_spread = {"axis_a": 0.01, "axis_b": 0.01, "axis_c": 0.01, "axis_d": 0.01}
        # current avg spread is 0.8. We need it below 0.35.
        # (0.8 * 20 + 0.01 * 100) / 120 = (16 + 1) / 120 = 17/120 approx 0.14
        self.mem.join_or_create_family("sym_03", self.sig_a, tight_spread, 100)
        self.mem.join_or_create_family("sym_03", self.sig_a, tight_spread, 100)
        
        self.assertEqual(record.fracture_counter, 0)
        self.assertIsNone(record.fracture_status)

if __name__ == "__main__":
    unittest.main()
