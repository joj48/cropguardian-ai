import os
import sys
import unittest
import numpy as np
from PIL import Image

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.disease_detection_agent.disease_detection_agent import DiseaseDetectionAgent

class TestDiseaseDetectionAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Set up the test environment by initializing the agent and creating a dummy image.
        """
        # Ensure models exist before running tests
        model_path = os.path.join("models", "crop_disease_mobilenetv2.keras")
        class_names_path = os.path.join("models", "class_names.npy")
        
        if not os.path.exists(model_path) or not os.path.exists(class_names_path):
            raise unittest.SkipTest("Model or class names file not found. Skipping tests.")
            
        cls.agent = DiseaseDetectionAgent(model_path=model_path, class_names_path=class_names_path)
        
        # Create a dummy image for testing
        cls.test_image_path = "test_dummy_leaf.jpg"
        dummy_img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        dummy_img.save(cls.test_image_path)

    @classmethod
    def tearDownClass(cls):
        """
        Clean up created files.
        """
        if os.path.exists(cls.test_image_path):
            os.remove(cls.test_image_path)

    def test_initialization(self):
        """Test if the agent initializes correctly with the model and class names."""
        self.assertIsNotNone(self.agent.model)
        self.assertTrue(len(self.agent.class_names) > 0)
        self.assertEqual(self.agent.target_size, (224, 224))
        self.assertEqual(self.agent.model_version, "crop_disease_mobilenetv2_v1")

    def test_preprocess_image(self):
        """Test if the image preprocessing returns the expected shape and values."""
        processed_img = self.agent.preprocess_image(self.test_image_path)
        # Expected shape: (1, 224, 224, 3)
        self.assertEqual(processed_img.shape, (1, 224, 224, 3))
        # Expected value range after mobilenet preprocessing: [-1, 1]
        self.assertTrue(np.min(processed_img) >= -1.0)
        self.assertTrue(np.max(processed_img) <= 1.0)

    def test_predict_format(self):
        """Test if the predict function returns the correct JSON format."""
        result = self.agent.predict(self.test_image_path)
        
        # Check basic keys
        self.assertIn("disease", result)
        self.assertIn("confidence", result)
        self.assertIn("confidence_level", result)
        self.assertIn("top_predictions", result)
        self.assertIn("timestamp", result)
        self.assertIn("model_version", result)
        
        # Check top_predictions structure
        self.assertEqual(len(result["top_predictions"]), 3)
        for pred in result["top_predictions"]:
            self.assertIn("class", pred)
            self.assertIn("confidence", pred)
            self.assertIsInstance(pred["confidence"], float)
            
        # Check sorting order of top predictions
        confidences = [pred["confidence"] for pred in result["top_predictions"]]
        self.assertEqual(confidences, sorted(confidences, reverse=True))

        # Check confidence level logic
        if result["confidence"] >= 90.0:
            self.assertEqual(result["confidence_level"], "High")
        elif result["confidence"] >= 70.0:
            self.assertEqual(result["confidence_level"], "Medium")
        else:
            self.assertEqual(result["confidence_level"], "Low")
            self.assertIn("warning", result)

if __name__ == "__main__":
    unittest.main()
