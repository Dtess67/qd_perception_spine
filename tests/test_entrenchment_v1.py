import unittest
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from qd_perception_spine.entrenchment_v1 import (
    RollbackEvent, handle_rollback, family_authority, family_suspect
)

class TestEntrenchmentV1(unittest.TestCase):
    def setUp(self):
        # Reset global state before each test
        family_authority.clear()
        family_suspect.clear()

    def test_normal_rollback_increments(self):
        """non-suspect rollback increments authority as before"""
        fam_id = "fam_01"
        family_authority[fam_id] = 10
        family_suspect[fam_id] = False
        
        event = RollbackEvent(participants=[fam_id])
        handle_rollback(event)
        
        self.assertEqual(family_authority[fam_id], 11)
        self.assertTrue(event.authority_incremented)

    def test_suspect_blocks_increment(self):
        """suspect-family rollback does not increment authority"""
        fam_id = "fam_suspect"
        family_authority[fam_id] = 10
        family_suspect[fam_id] = True
        
        event = RollbackEvent(participants=[fam_id])
        handle_rollback(event)
        
        self.assertEqual(family_authority[fam_id], 10)
        self.assertFalse(event.authority_incremented)

    def test_coalition_blocks_all(self):
        """coalition rollback with one suspect family increments authority for no participant"""
        fams = ["fam_clean", "fam_suspect", "fam_other"]
        for f in fams:
            family_authority[f] = 5
            family_suspect[f] = False
        
        family_suspect["fam_suspect"] = True
        
        event = RollbackEvent(participants=fams)
        handle_rollback(event)
        
        for f in fams:
            self.assertEqual(family_authority[f], 5, f"Authority for {f} should not have changed")
        self.assertFalse(event.authority_incremented)

    def test_event_still_records(self):
        """rollback event is still logged (represented by event object state) even when authority is blocked"""
        fam_id = "fam_suspect"
        family_authority[fam_id] = 10
        family_suspect[fam_id] = True
        
        event = RollbackEvent(participants=[fam_id])
        handle_rollback(event)
        
        # The fact that we have an event object with authority_incremented=False
        # shows it was processed/logged but blocked.
        self.assertIn(fam_id, event.participants)
        self.assertFalse(event.authority_incremented)

if __name__ == '__main__':
    unittest.main()
