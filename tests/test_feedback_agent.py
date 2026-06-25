import os
import sys
import unittest
import shutil
import csv
import numpy as np
from PIL import Image

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.feedback_agent.feedback_agent import FeedbackAgent

class TestFeedbackAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up dummy environment for feedback agent testing."""
        cls.test_feedback_dir = "data/test_feedback"
        cls.test_retraining_dir = "data/test_retraining"
        cls.dummy_img_path = "test_dummy_feedback.jpg"
        
        # Clean up if exists
        if os.path.exists(cls.test_feedback_dir):
            shutil.rmtree(cls.test_feedback_dir)
        if os.path.exists(cls.test_retraining_dir):
            shutil.rmtree(cls.test_retraining_dir)
            
        # Create a dummy image
        dummy_img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        dummy_img.save(cls.dummy_img_path)
        
        cls.agent = FeedbackAgent(feedback_dir=cls.test_feedback_dir)

    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        if os.path.exists(cls.test_feedback_dir):
            shutil.rmtree(cls.test_feedback_dir)
        if os.path.exists(cls.test_retraining_dir):
            shutil.rmtree(cls.test_retraining_dir)
        if os.path.exists(cls.dummy_img_path):
            os.remove(cls.dummy_img_path)

    def test_feedback_lifecycle(self):
        """Test logging feedback, copying image, duplicate detection, stats, and export."""
        # 1. Log the first time
        success = self.agent.log_feedback(
            original_image_path=self.dummy_img_path,
            predicted_class="Tomato___Late_blight",
            actual_class="Potato___Late_blight",
            confidence=85.0,
            timestamp="2026-06-24T12:00:00",
            model_version="test_v1"
        )
        self.assertTrue(success, "Failed to log original feedback.")
        
        # 2. Check CSV creation and content
        self.assertTrue(os.path.exists(self.agent.csv_path))
        with open(self.agent.csv_path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 1)
            self.assertEqual(reader[0]["predicted_class"], "Tomato___Late_blight")
            self.assertEqual(reader[0]["actual_class"], "Potato___Late_blight")
            
        # 3. Check Image copied
        csv_filename = reader[0]["image_path"]
        self.assertTrue(os.path.exists(os.path.join(self.agent.images_dir, csv_filename)))
        
        # 4. Try logging duplicate
        success_dup = self.agent.log_feedback(
            original_image_path=self.dummy_img_path,
            predicted_class="Tomato___Late_blight",
            actual_class="Potato___Late_blight",
            confidence=85.0,
            timestamp="2026-06-24T12:01:00",
            model_version="test_v1"
        )
        self.assertFalse(success_dup, "Duplicate detection failed, logged same image again.")

        # 5. Test stats
        stats = self.agent.get_feedback_stats()
        self.assertEqual(stats["total_feedback"], 1)
        self.assertEqual(stats["most_confused_class"], "Potato___Late_blight")
        self.assertEqual(stats["average_wrong_confidence"], 85.0)

        # 6. Test export retraining dataset
        exported = self.agent.export_retraining_dataset(output_dir=self.test_retraining_dir)
        self.assertEqual(exported, 1)
        
        # Verify the structure: output_dir / actual_class / image.jpg
        actual_class_dir = os.path.join(self.test_retraining_dir, "Potato___Late_blight")
        self.assertTrue(os.path.exists(actual_class_dir))
        
        images_in_dir = os.listdir(actual_class_dir)
        self.assertEqual(len(images_in_dir), 1)

if __name__ == "__main__":
    unittest.main()
