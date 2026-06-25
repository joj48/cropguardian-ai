import os
import datetime
import numpy as np
import tensorflow as tf
from typing import Dict, Any

class DiseaseDetectionAgent:
    def __init__(self, model_path: str = "models/crop_disease_mobilenetv2.keras", class_names_path: str = "models/class_names.npy"):
        """
        Initializes the Disease Detection Agent by loading the pre-trained model and class names.
        """
        self.model_version = "crop_disease_mobilenetv2_v1"
        # Load the model
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
        self.model = tf.keras.models.load_model(model_path)
        
        # Load class names
        if not os.path.exists(class_names_path):
            raise FileNotFoundError(f"Class names file not found at {class_names_path}")
        self.class_names = np.load(class_names_path, allow_pickle=True)
        
        # MobileNetV2 standard input size
        self.target_size = (224, 224)

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocesses an image for MobileNetV2 prediction.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")
            
        # Load image with target size
        img = tf.keras.preprocessing.image.load_img(image_path, target_size=self.target_size)
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        
        # Expand dimensions to match expected (batch_size, height, width, channels)
        img_array = np.expand_dims(img_array, axis=0)
        
        # MobileNetV2 preprocessing: scale pixels between -1 and 1
        img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
        
        return img_array

    def predict(self, image_path: str) -> Dict[str, Any]:
        """
        Predicts the disease for the given image path and returns formatted results.
        """
        processed_img = self.preprocess_image(image_path)
        
        # Get raw probabilities (the model outputs softmax probabilities)
        predictions = self.model.predict(processed_img, verbose=0)[0]
        
        # Get top 3 indices in descending order
        top_3_indices = np.argsort(predictions)[-3:][::-1]
        
        top_predictions = []
        for idx in top_3_indices:
            confidence_pct = round(float(predictions[idx]) * 100, 2)
            top_predictions.append({
                "class": str(self.class_names[idx]),
                "confidence": confidence_pct
            })
            
        top_disease = top_predictions[0]["class"]
        top_confidence = top_predictions[0]["confidence"]
        
        # Determine confidence level
        if top_confidence >= 90.0:
            confidence_level = "High"
        elif top_confidence >= 70.0:
            confidence_level = "Medium"
        else:
            confidence_level = "Low"
            
        result = {
            "disease": top_disease,
            "confidence": top_confidence,
            "confidence_level": confidence_level,
            "top_predictions": top_predictions,
            "timestamp": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "model_version": self.model_version
        }
        
        # Add a warning if confidence is low
        if confidence_level == "Low":
            result["warning"] = "Low confidence prediction. Please verify visually or retake the image."
            
        return result
