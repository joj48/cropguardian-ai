import os
import sys
import unittest
from unittest.mock import patch

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.coordinator_agent.coordinator_agent import CoordinatorAgent

class TestPredictionResponse(unittest.TestCase):
    def setUp(self):
        self.agent = CoordinatorAgent()

    @patch('agents.disease_detection_agent.disease_detection_agent.DiseaseDetectionAgent.predict')
    @patch('agents.severity_agent.severity_agent.SeverityAgent.analyze_severity')
    @patch('agents.advisory_agent.advisory_agent.AdvisoryAgent.generate_advice')
    @patch('os.path.exists', return_value=True)
    def test_prediction_response_crop_field(self, mock_exists, mock_advisory, mock_severity, mock_disease):
        """Test that the prediction response dictionary always includes a correctly resolved crop field."""
        mock_disease.return_value = {
            "disease": "Tomato___Late_blight",
            "confidence": 95.0,
            "confidence_level": "High",
            "model_version": "v1",
            "timestamp": "2026-06-26"
        }
        mock_severity.return_value = {
            "severity": "High"
        }
        mock_advisory.return_value = {
            "source": "Mocked",
            "treatment": []
        }

        # Case 1: KB record lookup should return correctly
        result = self.agent.process_image("dummy_path.jpg")
        self.assertIn("crop", result["prediction"])
        self.assertEqual(result["prediction"]["crop"], "Tomato")

        # Case 2: Resolves from KB as "Pepper"
        mock_disease.return_value = {
            "disease": "Pepper,_bell___Bacterial_spot",
            "confidence": 90.0,
            "confidence_level": "High",
            "model_version": "v1",
            "timestamp": "2026-06-26"
        }
        result = self.agent.process_image("dummy_path.jpg")
        self.assertIn("crop", result["prediction"])
        self.assertEqual(result["prediction"]["crop"], "Pepper")

        # Case 3: Falls back to inference when KB lookup fails (e.g. unknown class not in database)
        mock_disease.return_value = {
            "disease": "Pepper,_bell___Unknown_Mock_Disease",
            "confidence": 90.0,
            "confidence_level": "High",
            "model_version": "v1",
            "timestamp": "2026-06-26"
        }
        result = self.agent.process_image("dummy_path.jpg")
        self.assertIn("crop", result["prediction"])
        self.assertEqual(result["prediction"]["crop"], "Pepper Bell")

if __name__ == "__main__":
    unittest.main()
