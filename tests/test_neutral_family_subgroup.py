import unittest
from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

class TestNeutralFamilySubgroup(unittest.TestCase):
    def setUp(self):
        self.mem = NeutralFamilyMemoryV1()
        # Keep subgroup tests focused on detection/persistence; fission behavior is covered separately.
        self.mem.MIN_MEMBERS_FOR_FISSION = 999
        self.mem.FISSION_PERSISTENCE_THRESHOLD = 999
        self.spread = {"axis_a": 0.05, "axis_b": 0.05, "axis_c": 0.05, "axis_d": 0.05}

    def test_broad_single_cloud_no_subgroups(self):
        """A broad family without distinct clusters should NOT trigger subgroup detection."""
        # Create a single broad family by using a chain of symbols
        # Each symbol is within DISTANCE_THRESHOLD (0.15) of the previous one
        chain = [0.1, 0.2, 0.3, 0.4, 0.5]
        for val in chain:
            sig = {"axis_a": val, "axis_b": val, "axis_c": val, "axis_d": val}
            # Repeat to earn join (JOIN_PERSISTENCE_THRESHOLD=2)
            for _ in range(2):
                self.mem.join_or_create_family(f"sym_{val}", sig, self.spread, 10)
        
        record = self.mem.get_family_record("fam_01")
        # Subgroup detection is heuristic, but for a uniform chain, 
        # the max_dist (0.4) is not 2x (SUBGROUP_TIGHTNESS_RATIO) the average 
        # internal distance to nearest center.
        # Let's verify.
        self.assertEqual(record.subgroup_count, 1)

    def test_dual_center_subgroup_detection(self):
        """A family with two distinct clusters SHOULD trigger subgroup detection after persistence."""
        # We'll use a larger DISTANCE_THRESHOLD to ensure everything joins one family
        self.mem.DISTANCE_THRESHOLD = 0.5
        self.mem.HOLD_THRESHOLD = 1.0
        
        # Bridge at 0.5
        # Cluster 1 at 0.1
        # Cluster 2 at 0.9
        
        vals = [0.5, 0.4, 0.3, 0.2, 0.1, 0.6, 0.7, 0.8, 0.9]
        for val in vals:
            sig = {"axis_a": val, "axis_b": val, "axis_c": val, "axis_d": val}
            for _ in range(2):
                self.mem.join_or_create_family(f"sym_{val}", sig, self.spread, 10)
        
        record = self.mem.get_family_record("fam_01")
        # Subgroup persistence requires 3 hits
        # Each hit on the symbols will trigger _check_for_fracture.
        # However, it only counts symbols that have actually JOINED.
        # Since sym_0.1 and sym_0.9 are already joined, we just hit them again.
        for _ in range(5):
            self.mem.join_or_create_family("sym_0.1", {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}, self.spread, 10)
            self.mem.join_or_create_family("sym_0.9", {"axis_a": 0.9, "axis_b": 0.9, "axis_c": 0.9, "axis_d": 0.9}, self.spread, 10)
            
        self.assertEqual(record.subgroup_count, 2)
        self.assertEqual(record.fracture_status, "FAMILY_SPLIT_READY")

    def test_no_auto_split_on_subgroup_detection(self):
        """Subgroup evidence alone (without SPLIT_READY) should NOT cause actual fission."""
        self.mem.FRACTURE_PERSISTENCE_THRESHOLD = 999
        # Setup dual center
        vals = [0.5, 0.4, 0.3, 0.2, 0.1, 0.6, 0.7, 0.8, 0.9]
        # Increase distance threshold briefly to make setup easier if needed, 
        # but let's see if this works.
        # Actually, let's just use the same logic as the demo.
        
        # We'll use a hack to ensure they are in one family: 
        # all symbols are initially close to 0.5
        for i in range(10):
            sig = {"axis_a": 0.5 + (i*0.01), "axis_b": 0.5, "axis_c": 0.5, "axis_d": 0.5}
            for _ in range(2):
                self.mem.join_or_create_family(f"sym_init_{i}", sig, self.spread, 10)
        
        # Now move them to clusters
        for _ in range(5):
            for i in range(3):
                self.mem.join_or_create_family(f"sym_init_{i}", {"axis_a": 0.1, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}, self.spread, 10)
            for i in range(7, 10):
                self.mem.join_or_create_family(f"sym_init_{i}", {"axis_a": 0.9, "axis_b": 0.9, "axis_c": 0.9, "axis_d": 0.9}, self.spread, 10)
            
        record = self.mem.get_family_record("fam_01")
        self.assertEqual(record.subgroup_count, 2)
        self.assertNotEqual(record.fracture_status, "FAMILY_SPLIT_READY")
        
        # Verify all members are still in fam_01
        self.assertIn("sym_init_0", record.member_symbol_ids)
        self.assertIn("sym_init_9", record.member_symbol_ids)
        self.assertIn("sym_init_5", record.member_symbol_ids)
        
        # Verify no new families were created (other than the initial fam_01)
        # We might have fam_02 if something failed to join, but the core 
        # members of fam_01 should stay.
        self.assertEqual(self.mem.get_family_for_symbol("sym_init_0"), "fam_01")
        self.assertEqual(self.mem.get_family_for_symbol("sym_init_9"), "fam_01")

if __name__ == "__main__":
    unittest.main()
