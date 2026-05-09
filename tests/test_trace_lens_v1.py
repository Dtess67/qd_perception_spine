import unittest
from qd_perception.neutral_family_memory_v1 import (
    NeutralFamilyMemoryV1,
    family_hold_directions,
    family_diag_confidence,
    family_drift_streak,
    family_last_tested,
    family_diag_last_outcome,
    family_action_eligible,
    family_intervention_type,
    family_diag_conf_history,
    CAUSES
)

class TestTraceLensV1(unittest.TestCase):
    def setUp(self):
        # Reset global state
        family_hold_directions.clear()
        family_diag_confidence.clear()
        family_drift_streak.clear()
        family_last_tested.clear()
        family_diag_last_outcome.clear()
        family_action_eligible.clear()
        family_intervention_type.clear()
        family_diag_conf_history.clear()
        self.memory = NeutralFamilyMemoryV1()

    def test_trace_structure_and_fields(self):
        fid = "F_TEST"
        # Populate some data
        family_diag_confidence[fid] = {"EDGE_BAND_PROXIMITY": 0.5}
        family_diag_conf_history[fid] = {"EDGE_BAND_PROXIMITY": [0.4, 0.5]}
        family_drift_streak[fid] = 2
        family_last_tested[fid] = {"EDGE_BAND_PROXIMITY": 10}
        family_diag_last_outcome[fid] = "PASS"
        family_action_eligible[fid] = True
        family_intervention_type[fid] = "STABILIZE"

        trace = self.memory.get_family_trace(fid)
        
        self.assertIn("TRACE:", trace)
        self.assertIn(f"Family={fid}", trace)
        self.assertIn("Hypotheses={EDGE_BAND_PROXIMITY=0.50↑ [0.40,0.50]", trace)
        self.assertIn("Drift={streak=2, attention=1.33}", trace)
        self.assertIn("Last={cause=EDGE_BAND_PROXIMITY, outcome=PASS}", trace)
        self.assertIn("Decision={eligible=True, intervention=STABILIZE}", trace)

    def test_trace_no_data_no_crash(self):
        # Fresh family with no data
        fid = "F_NEW"
        trace = self.memory.get_family_trace(fid)
        
        self.assertIn("TRACE:", trace)
        self.assertIn(f"Family={fid}", trace)
        # Should show defaults/zeros
        self.assertIn("Drift={streak=0, attention=1.0}", trace)
        self.assertIn("Last={cause=NONE, outcome=NONE}", trace)
        self.assertIn("Decision={eligible=False, intervention=NONE}", trace)

    def test_trend_arrows(self):
        fid = "F_TREND"
        # Up trend
        family_diag_conf_history[fid] = {"EDGE_BAND_PROXIMITY": [0.3, 0.4]}
        family_diag_confidence[fid] = {"EDGE_BAND_PROXIMITY": 0.4}
        trace = self.memory.get_family_trace(fid)
        self.assertIn("EDGE_BAND_PROXIMITY=0.40↑", trace)

        # Down trend
        family_diag_conf_history[fid]["EDGE_BAND_PROXIMITY"] = [0.4, 0.3]
        family_diag_confidence[fid]["EDGE_BAND_PROXIMITY"] = 0.3
        trace = self.memory.get_family_trace(fid)
        self.assertIn("EDGE_BAND_PROXIMITY=0.30↓", trace)

        # No change
        family_diag_conf_history[fid]["EDGE_BAND_PROXIMITY"] = [0.3, 0.3]
        family_diag_confidence[fid]["EDGE_BAND_PROXIMITY"] = 0.3
        trace = self.memory.get_family_trace(fid)
        self.assertIn("EDGE_BAND_PROXIMITY=0.30→", trace)

    def test_history_limit_in_trace(self):
        fid = "F_HIST"
        # History has 5 values, should show last 3
        family_diag_conf_history[fid] = {"JOIN_PERSISTENCE": [0.1, 0.2, 0.3, 0.4, 0.5]}
        family_diag_confidence[fid] = {"JOIN_PERSISTENCE": 0.5}
        trace = self.memory.get_family_trace(fid)
        self.assertIn("[0.30,0.40,0.50]", trace)

if __name__ == "__main__":
    unittest.main()
