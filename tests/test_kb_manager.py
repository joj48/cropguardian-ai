import pytest
import os
from unittest.mock import patch, MagicMock

from src.services.knowledge_base.kb_manager import KnowledgeBaseManager
from src.services.knowledge_base.exceptions import DiseaseNotFound, InvalidKnowledgeBase
from src.services.knowledge_base.models import DiseaseRecord

@pytest.fixture
def mock_config():
    return {
        "supported_crops": ["Tomato", "Potato"]
    }

@pytest.fixture
def mock_tomato_data():
    return [
        {
            "metadata": {
                "review_status": "approved",
                "last_scientific_review": "2026-06-26",
                "content_quality": "High",
                "difficulty_level": "Intermediate"
            },
            "disease_id": "TOM-001",
            "disease_name": "Tomato Late Blight",
            "common_name": "Late Blight",
            "scientific_name": "Phytophthora infestans",
            "crop": "Tomato",
            "disease_type": "Fungal",
            "pathogen_type": "Oomycete",
            "model_mapping": {
                "cnn_class": "Tomato___Late_blight",
                "aliases": ["late blight"]
            },
            "overview": {
                "description": "A devastating disease of tomatoes.",
                "importance": "High",
                "affected_parts": ["leaves"],
                "host_plants": ["Tomato"]
            },
            "symptoms": {
                "early": ["Dark lesions on leaves"],
                "moderate": [],
                "severe": [],
                "leaf": [],
                "stem": [],
                "fruit": [],
                "root": []
            },
            "causes": {
                "primary_cause": "Phytophthora infestans",
                "pathogen": "Oomycete",
                "survival_mechanism": "spores",
                "infection_process": "germination"
            },
            "infection_cycle": {
                "stages": ["Spores germinate in water"],
                "spread_cycle": "Polycyclic"
            },
            "transmission": {
                "methods": ["Wind", "Water splash"],
                "vectors": [],
                "common_sources": ["Soil"]
            },
            "risk_factors": {
                "humidity": "High"
            },
            "environmental_conditions": {
                "temperature": {"optimal_range": "15-20C", "notes": "cool"},
                "humidity": {"optimal_range": ">90%", "notes": "wet"},
                "rainfall": "moderate",
                "wind": "gentle",
                "soil_conditions": "wet"
            },
            "weather_thresholds": {
                "humidity": 90
            },
            "weather_influence": {
                "high_humidity": "Thrives in cool, wet weather."
            },
            "severity_levels": {
                "low": "First spots",
                "medium": "Spreading",
                "high": "Complete defoliation",
                "critical": "Ruined"
            },
            "severity_score": {
                "low": 1,
                "medium": 2,
                "high": 3,
                "critical": 4
            },
            "immediate_actions": {
                "today": ["Apply fungicide"],
                "within_24_hours": [],
                "within_one_week": []
            },
            "treatment": {
                "chemical": ["Copper-based fungicides"],
                "biological": [],
                "organic": [],
                "integrated_management": []
            },
            "prevention": {
                "farm_hygiene": [],
                "irrigation": [],
                "crop_rotation": ["Crop rotation"],
                "air_circulation": [],
                "resistant_varieties": ["Resistant varieties"],
                "seasonal_practices": []
            },
            "nutrient_management": {
                "nitrogen": "Avoid excess nitrogen",
                "phosphorus": "standard",
                "potassium": "standard",
                "calcium": "standard",
                "magnesium": "standard",
                "micronutrients": []
            },
            "disease_progression": {
                "untreated": ["Rapid"],
                "treated": ["Controlled"]
            },
            "recovery_indicators": ["New healthy growth"],
            "recovery": {
                "estimated_days": "14",
                "success_rate": "high",
                "depends_on": ["weather"]
            },
            "economic_impact": {
                "yield_loss": "Severe",
                "quality_loss": "High",
                "financial_impact": "High"
            },
            "monitoring": {
                "inspection_frequency": "weekly",
                "warning_signs": ["Check lower leaves frequently"],
                "recovery_signs": []
            },
            "faq": [
                {"question": "Is it safe to eat?", "answer": "Yes, if unaffected."}
            ],
            "educational_information": {
                "interesting_facts": ["First identified in 1840s."],
                "similar_diseases": [],
                "differential_diagnosis": [],
                "long_term_management": []
            },
            "ai_context": {
                "summary": "Late blight"
            },
            "prompt_templates": {
                "default": "Advise on late blight"
            },
            "references": ["Ag Ext 101"]
        }
    ]

class TestKnowledgeBaseManager:
    @patch("src.services.knowledge_base.kb_loader.KnowledgeBaseLoader.load_config")
    @patch("src.services.knowledge_base.kb_loader.KnowledgeBaseLoader.load_crop_data")
    @patch("src.services.knowledge_base.kb_validator.KnowledgeBaseValidator.validate_crop_data")
    def test_initialization_and_cache_warmup(self, mock_validate, mock_load_data, mock_load_config, mock_config, mock_tomato_data):
        mock_load_config.return_value = mock_config
        mock_load_data.side_effect = lambda crop: mock_tomato_data if crop == "Tomato" else []
        
        manager = KnowledgeBaseManager(validate_on_startup=True)
        
        assert manager.config == mock_config
        # Should have built the disease index
        assert manager.cache.get_disease("Tomato___Late_blight") is not None
        assert manager.cache.get_disease("Tomato___Late_blight").disease_id == "TOM-001"
        assert mock_validate.called

    @patch("src.services.knowledge_base.kb_loader.KnowledgeBaseLoader.load_config")
    @patch("src.services.knowledge_base.kb_loader.KnowledgeBaseLoader.load_crop_data")
    def test_get_disease_not_found(self, mock_load_data, mock_load_config, mock_config):
        mock_load_config.return_value = mock_config
        mock_load_data.return_value = []
        
        manager = KnowledgeBaseManager(validate_on_startup=False)
        
        with pytest.raises(DiseaseNotFound):
            manager.get_disease("Unknown___Disease")

    @patch("src.services.knowledge_base.kb_loader.KnowledgeBaseLoader.load_config")
    @patch("src.services.knowledge_base.kb_loader.KnowledgeBaseLoader.load_crop_data")
    def test_get_crop(self, mock_load_data, mock_load_config, mock_config, mock_tomato_data):
        mock_load_config.return_value = mock_config
        mock_load_data.return_value = mock_tomato_data
        
        manager = KnowledgeBaseManager(validate_on_startup=False)
        crop_data = manager.get_crop("Tomato")
        
        assert len(crop_data) == 1
        assert isinstance(crop_data[0], DiseaseRecord)
        assert crop_data[0].disease_id == "TOM-001"
