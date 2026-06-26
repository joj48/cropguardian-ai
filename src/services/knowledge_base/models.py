"""
models.py — CropGuardian Knowledge Base Pydantic Models

DiseaseRecord represents the canonical Knowledge Base JSON schema exactly.
Nested Pydantic models are used wherever the JSON structure is consistent
and can be modeled cleanly. Dict[str, Any] is used only for genuinely
dynamic structures (risk_factors, weather_thresholds) whose keys vary per disease.

The JSON schema is the source of truth. This file must follow the JSON,
not the other way around.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


# ─── Sub-models: model_mapping ────────────────────────────────────────────────

class ModelMapping(BaseModel):
    cnn_class: str
    aliases: List[str] = Field(default_factory=list)


# ─── Sub-models: overview ─────────────────────────────────────────────────────

class Overview(BaseModel):
    description: str
    importance: Optional[str] = None
    affected_parts: Optional[List[str]] = None
    host_plants: Optional[List[str]] = None


# ─── Sub-models: symptoms ─────────────────────────────────────────────────────

class Symptoms(BaseModel):
    early: Optional[List[str]] = None
    moderate: Optional[List[str]] = None
    severe: Optional[List[str]] = None
    leaf: Optional[List[str]] = None
    stem: Optional[List[str]] = None
    fruit: Optional[List[str]] = None
    root: Optional[List[str]] = None

    class Config:
        extra = "allow"   # allow additional symptom stages without breaking validation


# ─── Sub-models: causes ──────────────────────────────────────────────────────

class Causes(BaseModel):
    primary_cause: Optional[str] = None
    pathogen: Optional[str] = None
    survival_mechanism: Optional[str] = None
    infection_process: Optional[str] = None

    class Config:
        extra = "allow"


# ─── Sub-models: infection_cycle ─────────────────────────────────────────────

class InfectionCycle(BaseModel):
    stages: Optional[List[str]] = None
    spread_cycle: Optional[str] = None

    class Config:
        extra = "allow"


# ─── Sub-models: transmission ────────────────────────────────────────────────

class Transmission(BaseModel):
    methods: Optional[List[str]] = None
    vectors: Optional[List[str]] = None
    common_sources: Optional[List[str]] = None

    class Config:
        extra = "allow"


# ─── Sub-models: environmental_conditions ────────────────────────────────────

class EnvironmentConditionRange(BaseModel):
    optimal_range: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        extra = "allow"


class EnvironmentalConditions(BaseModel):
    temperature: Optional[Union[EnvironmentConditionRange, str]] = None
    humidity: Optional[Union[EnvironmentConditionRange, str]] = None
    rainfall: Optional[str] = None
    wind: Optional[str] = None
    soil_conditions: Optional[str] = None

    class Config:
        extra = "allow"


# ─── Sub-models: weather_influence ───────────────────────────────────────────

class WeatherInfluence(BaseModel):
    high_humidity: Optional[str] = None
    rain: Optional[str] = None
    high_temperature: Optional[str] = None
    low_temperature: Optional[str] = None
    wind: Optional[str] = None
    dry_conditions: Optional[str] = None

    class Config:
        extra = "allow"


# ─── Sub-models: severity_score ──────────────────────────────────────────────

class SeverityScore(BaseModel):
    low: Optional[int] = None
    medium: Optional[int] = None
    high: Optional[int] = None
    critical: Optional[int] = None


# ─── Sub-models: immediate_actions ───────────────────────────────────────────

class ImmediateActions(BaseModel):
    today: Optional[List[str]] = None
    within_24_hours: Optional[List[str]] = None
    within_one_week: Optional[List[str]] = None

    class Config:
        extra = "allow"


# ─── Sub-models: treatment ───────────────────────────────────────────────────

class Treatment(BaseModel):
    chemical: Optional[List[str]] = None
    biological: Optional[List[str]] = None
    organic: Optional[List[str]] = None
    integrated_management: Optional[List[str]] = None

    class Config:
        extra = "allow"


# ─── Sub-models: prevention ──────────────────────────────────────────────────

class Prevention(BaseModel):
    farm_hygiene: Optional[List[str]] = None
    irrigation: Optional[List[str]] = None
    crop_rotation: Optional[List[str]] = None
    air_circulation: Optional[List[str]] = None
    resistant_varieties: Optional[List[str]] = None
    seasonal_practices: Optional[List[str]] = None

    class Config:
        extra = "allow"


# ─── Sub-models: nutrient_management ─────────────────────────────────────────

class NutrientManagement(BaseModel):
    nitrogen: Optional[str] = None
    phosphorus: Optional[str] = None
    potassium: Optional[str] = None
    calcium: Optional[str] = None
    magnesium: Optional[str] = None
    micronutrients: Optional[Union[List[str], str]] = None

    class Config:
        extra = "allow"


# ─── Sub-models: disease_progression ─────────────────────────────────────────

class DiseaseProgression(BaseModel):
    untreated: Optional[List[str]] = None
    treated: Optional[List[str]] = None

    class Config:
        extra = "allow"


# ─── Sub-models: recovery ────────────────────────────────────────────────────

class Recovery(BaseModel):
    estimated_days: Optional[str] = None
    success_rate: Optional[str] = None
    depends_on: Optional[List[str]] = None

    class Config:
        extra = "allow"


# ─── Sub-models: economic_impact ─────────────────────────────────────────────

class EconomicImpact(BaseModel):
    yield_loss: Optional[str] = None
    quality_loss: Optional[str] = None
    financial_impact: Optional[str] = None

    class Config:
        extra = "allow"


# ─── Sub-models: monitoring ──────────────────────────────────────────────────

class Monitoring(BaseModel):
    inspection_frequency: Optional[str] = None
    warning_signs: Optional[List[str]] = None
    recovery_signs: Optional[List[str]] = None

    class Config:
        extra = "allow"


# ─── Sub-models: educational_information ─────────────────────────────────────

class EducationalInformation(BaseModel):
    interesting_facts: Optional[List[str]] = None
    similar_diseases: Optional[List[str]] = None
    differential_diagnosis: Optional[List[str]] = None
    long_term_management: Optional[List[str]] = None

    class Config:
        extra = "allow"


# ─── Root model: DiseaseRecord ────────────────────────────────────────────────

class DiseaseRecord(BaseModel):
    """
    Canonical representation of a Knowledge Base disease record.
    Maps exactly to the JSON schema in knowledge_base/*.json.
    Nested Pydantic models are used for structured fields.
    Dict[str, Any] is used only for genuinely dynamic structures
    (risk_factors, weather_thresholds, severity_levels, ai_context,
    prompt_templates, metadata) whose keys vary per disease.
    """
    # Identity
    metadata: Dict[str, Any] = Field(default_factory=dict)
    disease_id: str
    disease_name: str
    common_name: str
    scientific_name: str
    crop: str
    disease_type: str
    pathogen_type: str
    model_mapping: ModelMapping

    # Scientific knowledge — nested models
    overview: Overview
    symptoms: Symptoms
    causes: Causes
    infection_cycle: InfectionCycle
    transmission: Transmission
    risk_factors: Dict[str, Any]                    # keys vary per disease
    environmental_conditions: EnvironmentalConditions
    weather_thresholds: Dict[str, Any]              # numeric thresholds, dynamic
    weather_influence: WeatherInfluence
    severity_levels: Dict[str, Any] = Field(default_factory=dict)
    severity_score: SeverityScore
    immediate_actions: ImmediateActions

    # Management
    treatment: Treatment
    prevention: Prevention
    nutrient_management: NutrientManagement
    disease_progression: DiseaseProgression
    recovery_indicators: List[str] = Field(default_factory=list)
    recovery: Recovery
    economic_impact: EconomicImpact
    monitoring: Monitoring

    # Additional
    faq: List[Dict[str, str]] = Field(default_factory=list)
    educational_information: EducationalInformation
    ai_context: Dict[str, Any] = Field(default_factory=dict)
    prompt_templates: Dict[str, str] = Field(default_factory=dict)
    references: List[str] = Field(default_factory=list)


# ─── Advisory pipeline models ─────────────────────────────────────────────────

class PredictionData(BaseModel):
    disease: str
    confidence: float
    status: str
    error: Optional[str] = None


class AdvisoryContext(BaseModel):
    """
    Unified payload passed to the Advisory Agent.
    knowledge_context is the full DiseaseRecord Pydantic model —
    it must NOT be converted to a dict before passing here.
    """
    disease_data: Dict[str, Any] = Field(default_factory=dict)
    weather_data: Dict[str, Any] = Field(default_factory=dict)
    severity_data: Dict[str, Any] = Field(default_factory=dict)
    risk_data: Dict[str, Any] = Field(default_factory=dict)
    knowledge_context: Optional[DiseaseRecord] = None
