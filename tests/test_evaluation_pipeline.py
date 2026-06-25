import os
import sys
import unittest
import shutil
import json
import numpy as np
from PIL import Image

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.evaluation.evaluate import evaluate_dataset
from src.evaluation.metrics import calculate_basic_metrics, get_top_confused_pairs

class TestEvaluationPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up dummy data for evaluation."""
        cls.test_dir = "data/dummy_test"
        cls.output_dir = "reports_dummy"
        
        # Load class names to know what directories to create
        class_names_path = "models/class_names.npy"
        if not os.path.exists(class_names_path):
            raise unittest.SkipTest("class_names.npy not found")
            
        cls.class_names = np.load(class_names_path, allow_pickle=True)
        
        # Create a few dummy class directories
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        os.makedirs(cls.test_dir)
        
        # We pick the first 2 classes
        for class_name in cls.class_names[:2]:
            class_dir = os.path.join(cls.test_dir, class_name)
            os.makedirs(class_dir)
            
            # Create a dummy image
            dummy_img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
            dummy_img.save(os.path.join(class_dir, "dummy1.jpg"))

    @classmethod
    def tearDownClass(cls):
        """Clean up dummy data."""
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        if os.path.exists(cls.output_dir):
            shutil.rmtree(cls.output_dir)

    def test_metrics_logic(self):
        y_true = [0, 0, 1, 1, 2]
        y_pred = [0, 1, 1, 1, 0]
        
        basic = calculate_basic_metrics(y_true, y_pred)
        self.assertIn("accuracy", basic)
        self.assertIn("f1_score", basic)
        
        target_names = ["A", "B", "C"]
        top_confused = get_top_confused_pairs(y_true, y_pred, target_names, top_n=5)
        
        # 0 predicted as 1 (once)
        # 2 predicted as 0 (once)
        self.assertEqual(len(top_confused), 2)

    def test_evaluate_dataset(self):
        """Test full pipeline execution."""
        prefix = "dummy"
        
        evaluate_dataset(self.test_dir, prefix, output_dir=self.output_dir)
        
        # Check if all files are created
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, f"{prefix}_metrics.json")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, f"{prefix}_classification_report.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, f"{prefix}_confusion_matrix.png")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, f"{prefix}_misclassified_images.csv")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, f"{prefix}_model_health_report.md")))
        
        # Verify JSON content
        with open(os.path.join(self.output_dir, f"{prefix}_metrics.json"), 'r') as f:
            data = json.load(f)
            self.assertIn("accuracy", data)
            self.assertIn("f1_score", data)

if __name__ == "__main__":
    unittest.main()
