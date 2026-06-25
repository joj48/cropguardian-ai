import os
import sys
import unittest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.severity_agent.severity_agent import SeverityAgent

class TestSeverityAgent(unittest.TestCase):
    def setUp(self):
        self.agent = SeverityAgent()
        self.dummy_path = "dummy.jpg"

    def test_healthy_class(self):
        """Test healthy -> None"""
        result = self.agent.analyze_severity(self.dummy_path, "Tomato___healthy", 95.0)
        self.assertEqual(result["severity"], "None")
        self.assertEqual(result["severity_score"], 0)

    def test_high_confidence(self):
        """Test Confidence 95 -> High"""
        result = self.agent.analyze_severity(self.dummy_path, "Tomato___Late_blight", 95.0)
        self.assertEqual(result["severity"], "High")
        self.assertEqual(result["severity_score"], 3)

    def test_medium_confidence(self):
        """Test Confidence 80 -> Medium"""
        result = self.agent.analyze_severity(self.dummy_path, "Tomato___Late_blight", 80.0)
        self.assertEqual(result["severity"], "Medium")
        self.assertEqual(result["severity_score"], 2)

    def test_low_confidence(self):
        """Test Confidence 50 -> Low"""
        result = self.agent.analyze_severity(self.dummy_path, "Tomato___Late_blight", 50.0)
        self.assertEqual(result["severity"], "Low")
        self.assertEqual(result["severity_score"], 1)

if __name__ == "__main__":
    unittest.main()
