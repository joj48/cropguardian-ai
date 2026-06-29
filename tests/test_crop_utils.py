import os
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.crop_utils import infer_crop_from_disease

def test_infer_crop_from_disease():
    assert infer_crop_from_disease("Tomato___Late_blight") == "Tomato"
    assert infer_crop_from_disease("Pepper,_bell___Bacterial_spot") == "Pepper Bell"
    assert infer_crop_from_disease("Potato___Early_blight") == "Potato"
    assert infer_crop_from_disease("Tomato — Late Blight") == "Tomato"
    assert infer_crop_from_disease("Corn — Common Rust") == "Corn"
    assert infer_crop_from_disease("Unknown_disease") == "Unknown Disease"
    assert infer_crop_from_disease("") == "Unknown"
