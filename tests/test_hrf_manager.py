import sys
import os
import unittest
import json

# Add workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nulka_agent.hrf_manager import HRFManager, HRF_CONFIG_PATH

class TestHRFManager(unittest.TestCase):
    def setUp(self):
        """Setup a clean state for testing by removing the config file if it exists."""
        if os.path.exists(HRF_CONFIG_PATH):
            os.remove(HRF_CONFIG_PATH)
        self.manager = HRFManager()

    def tearDown(self):
        """Clean up the config file after tests."""
        if os.path.exists(HRF_CONFIG_PATH):
            os.remove(HRF_CONFIG_PATH)

    def test_initial_state(self):
        """Verify baseline initialization."""
        self.assertEqual(self.manager.get_baseline("test_model"), 7.0)
        self.assertEqual(self.manager.get_threshold("test_model"), 7.0)

    def test_trust_increases_threshold(self):
        """Verify that trust increases the threshold up to a max of 10.0."""
        val = self.manager.trust("test_model")
        self.assertEqual(val, 8.0)
        # Max out at 10.0
        self.manager.trust("test_model")
        self.manager.trust("test_model")
        val = self.manager.trust("test_model")
        self.assertEqual(val, 10.0)

    def test_doubt_decreases_threshold(self):
        """Verify that doubt decreases the threshold down to a min of 1.0."""
        val = self.manager.doubt("test_model")
        self.assertEqual(val, 6.0)

    def test_bs_heavy_penalty(self):
        """Verify that the bs command drops the threshold heavily."""
        val = self.manager.bs("test_model", weight=5.0)
        self.assertEqual(val, 2.0)
        # Verify min bounds
        val = self.manager.bs("test_model", weight=10.0)
        self.assertEqual(val, 1.0)

    def test_reset(self):
        """Verify reset restores the baseline."""
        self.manager.doubt("test_model")
        self.manager.doubt("test_model")
        self.assertNotEqual(self.manager.get_threshold("test_model"), 7.0)
        
        val = self.manager.reset("test_model")
        self.assertEqual(val, 7.0)
        self.assertEqual(self.manager.get_threshold("test_model"), 7.0)

if __name__ == "__main__":
    unittest.main()
