import unittest
import numpy as np
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.knowledge_base.kb_manager import KnowledgeBaseManager
from src.services.knowledge_base.class_mapper import ClassMapper

class TestClassMapperAndCoverage(unittest.TestCase):
    def setUp(self):
        self.manager = KnowledgeBaseManager(validate_on_startup=True)
        self.mapper = self.manager.class_mapper
        
        # Path to class_names.npy
        self.class_names_path = "models/class_names.npy"
        self.assertTrue(os.path.exists(self.class_names_path), "class_names.npy not found")
        self.cnn_classes = list(np.load(self.class_names_path, allow_pickle=True))

    def test_class_mapper_resolution_stages(self):
        # 1. EXACT Match
        res = self.mapper.resolve("Tomato___Target_Spot")
        self.assertEqual(res.resolution_type, "EXACT")
        self.assertEqual(res.canonical_class, "Tomato___Target_Spot")

        # 2. CASE_INSENSITIVE Match
        res = self.mapper.resolve("Tomato___early_blight")
        self.assertEqual(res.resolution_type, "CASE_INSENSITIVE")
        self.assertEqual(res.canonical_class, "Tomato___Early_Blight")

        # 3. EXPLICIT_MAPPING Match
        res = self.mapper.resolve("Apple___Black_rot")
        self.assertEqual(res.resolution_type, "EXPLICIT_MAPPING")
        self.assertEqual(res.canonical_class, "Apple___Black_Rot_Frogeye_Leaf_Spot")

        # 4. NOT_FOUND
        res = self.mapper.resolve("Apple___unknown_disease")
        self.assertEqual(res.resolution_type, "NOT_FOUND")
        self.assertIsNone(res.canonical_class)

    def test_all_cnn_classes_coverage(self):
        print("\n=== CNN CLASS COVERAGE AND RESOLUTION REPORT ===")
        print(f"{'CNN Output Class':<50} | {'Resolution Type':<20} | {'Canonical KB Class':<50} | {'Status':<10}")
        print("-" * 140)

        failures = []
        for cnn_class in self.cnn_classes:
            cnn_class_str = str(cnn_class)
            # Skip healthy classes
            if "healthy" in cnn_class_str.lower():
                print(f"{cnn_class_str:<50} | {'HEALTHY BYPASS':<20} | {'N/A':<50} | {'SKIPPED':<10}")
                continue

            res = self.mapper.resolve(cnn_class_str)
            canonical = res.canonical_class
            res_type = res.resolution_type

            if not canonical:
                print(f"{cnn_class_str:<50} | {res_type:<20} | {'None':<50} | {'FAILED':<10}")
                failures.append(cnn_class_str)
                continue

            # Verify retrieval
            try:
                record = self.manager.get_disease(cnn_class_str)
                status = "PASSED"
            except Exception as e:
                status = f"ERROR: {e}"
                failures.append(cnn_class_str)

            print(f"{cnn_class_str:<50} | {res_type:<20} | {canonical:<50} | {status:<10}")

        print(f"\nTotal CNN classes: {len(self.cnn_classes)}")
        print(f"Failed resolutions: {len(failures)}")
        self.assertEqual(len(failures), 0, f"The following classes failed to resolve or retrieve: {failures}")

if __name__ == "__main__":
    unittest.main()
