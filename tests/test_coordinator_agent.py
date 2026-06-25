import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.coordinator_agent.coordinator_agent import CoordinatorAgent

class TestCoordinatorAgent(unittest.TestCase):
    def setUp(self):
        self.agent = CoordinatorAgent()
        
    def test_invalid_image_path(self):
        """Test handling of an invalid image path."""
        result = self.agent.process_image("non_existent_image_123.jpg")
        
        self.assertEqual(result["status"], "error")
        self.assertTrue(len(result["warnings"]) > 0)
        self.assertIn("Image not found", result["warnings"][0])
        self.assertEqual(result["agent_trace"], [])
        
    @patch('agents.disease_detection_agent.disease_detection_agent.DiseaseDetectionAgent.predict')
    @patch('agents.severity_agent.severity_agent.SeverityAgent.analyze_severity')
    @patch('agents.advisory_agent.advisory_agent.AdvisoryAgent.generate_advice')
    @patch('os.path.exists', return_value=True)
    def test_full_success_path(self, mock_exists, mock_advisory, mock_severity, mock_disease):
        """Test a complete successful pipeline run."""
        
        mock_disease.return_value = {
            "disease": "Tomato___Late_blight",
            "confidence": 95.0,
            "confidence_level": "High"
        }
        
        mock_severity.return_value = {
            "severity": "High",
            "severity_score": 3,
            "details": "Mocked details"
        }
        
        mock_advisory.return_value = {
            "source": "Mocked",
            "treatment": ["T1"]
        }
        
        result = self.agent.process_image("dummy_path.jpg")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["agent_trace"], ["DiseaseDetectionAgent", "SeverityAgent", "AdvisoryAgent"])
        self.assertEqual(result["warnings"], [])
        self.assertEqual(result["prediction"]["disease"], "Tomato___Late_blight")
        self.assertEqual(result["severity"]["severity"], "High")
        self.assertEqual(result["advice"]["source"], "Mocked")
        self.assertTrue(result["execution_time_ms"] >= 0)

    @patch('agents.disease_detection_agent.disease_detection_agent.DiseaseDetectionAgent.predict')
    @patch('agents.severity_agent.severity_agent.SeverityAgent.analyze_severity')
    @patch('agents.advisory_agent.advisory_agent.AdvisoryAgent.generate_advice')
    @patch('os.path.exists', return_value=True)
    def test_advisory_failure_path(self, mock_exists, mock_advisory, mock_severity, mock_disease):
        """Test partial success when Advisory Agent fails."""
        
        mock_disease.return_value = {
            "disease": "Tomato___Late_blight",
            "confidence": 95.0
        }
        mock_severity.return_value = {
            "severity": "High"
        }
        # Simulate an exception in advisory agent
        mock_advisory.side_effect = Exception("API Timeout")
        
        result = self.agent.process_image("dummy_path.jpg")
        
        self.assertEqual(result["status"], "partial_success")
        self.assertEqual(result["agent_trace"], ["DiseaseDetectionAgent", "SeverityAgent"])
        self.assertEqual(len(result["warnings"]), 1)
        self.assertIn("Advisory generation failed", result["warnings"][0])
        self.assertIsNone(result["advice"])

if __name__ == "__main__":
    unittest.main()
