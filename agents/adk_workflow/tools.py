from agents.disease_detection_agent.disease_detection_agent import DiseaseDetectionAgent
from agents.severity_agent.severity_agent import SeverityAgent
from agents.advisory_agent.advisory_agent import AdvisoryAgent
from agents.weather_agent.weather_agent import WeatherAgent
from agents.environmental_risk_agent.environmental_risk_agent import EnvironmentalRiskAgent

# Instantiate legacy agents to be reused across tools
_disease_agent = DiseaseDetectionAgent()
_severity_agent = SeverityAgent()
_advisory_agent = AdvisoryAgent()
_weather_agent = WeatherAgent()
_risk_agent = EnvironmentalRiskAgent()

def detect_disease_tool(image_path: str) -> dict:
    """
    Detects crop disease from an image.
    
    Args:
        image_path (str): The absolute path to the crop image file.
        
    Returns:
        dict: A dictionary containing 'disease', 'confidence', and 'confidence_level'.
    """
    try:
        return _disease_agent.predict(image_path)
    except Exception as e:
        return {"error": str(e)}

def analyze_severity_tool(image_path: str, disease_class: str, confidence: float) -> dict:
    """
    Analyzes the severity of a detected crop disease.
    
    Args:
        image_path (str): The absolute path to the crop image file.
        disease_class (str): The name of the detected disease (e.g. 'Tomato___Late_blight').
        confidence (float): The confidence percentage of the disease prediction.
        
    Returns:
        dict: A dictionary containing 'severity', 'severity_score', 'details', and 'assessment_method'.
    """
    try:
        return _severity_agent.analyze_severity(
            image_path=image_path,
            disease_class=disease_class,
            confidence=confidence
        )
    except Exception as e:
        return {"error": str(e)}

def generate_advice_tool(disease_class: str, severity: str, weather_data: dict, risk_data: dict) -> dict:
    """
    Generates agricultural advice based on disease class, severity, weather, and environmental risk.
    
    Args:
        disease_class (str): The name of the detected disease.
        severity (str): The severity level ('Low', 'Medium', 'High', 'None').
        weather_data (dict): The current weather data.
        risk_data (dict): The environmental risk assessment.
        
    Returns:
        dict: Agricultural recommendations.
    """
    try:
        # We need to update AdvisoryAgent to accept weather and risk, but for now we pass it in.
        return _advisory_agent.generate_advice(
            disease_class=disease_class,
            severity=severity,
            weather_data=weather_data,
            risk_data=risk_data
        )
    except Exception as e:
        return {"error": str(e)}

def get_weather_tool(location_input: str = None, lat: float = None, lon: float = None) -> dict:
    """
    Retrieves weather data based on location string OR coordinates.
    """
    try:
        return _weather_agent.get_weather(location_input=location_input, lat=lat, lon=lon)
    except Exception as e:
        return {"error": str(e)}

def assess_risk_tool(disease_class: str, weather_data: dict) -> dict:
    """
    Calculates environmental disease risk based on weather data.
    """
    try:
        return _risk_agent.assess_risk(disease_class, weather_data)
    except Exception as e:
        return {"error": str(e)}
