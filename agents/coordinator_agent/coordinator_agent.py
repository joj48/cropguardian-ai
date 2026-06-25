import os
import time
import datetime
from typing import Dict, Any

from agents.disease_detection_agent.disease_detection_agent import DiseaseDetectionAgent
from agents.severity_agent.severity_agent import SeverityAgent
from agents.weather_agent.weather_agent import WeatherAgent
from agents.environmental_risk_agent.environmental_risk_agent import EnvironmentalRiskAgent
from agents.advisory_agent.advisory_agent import AdvisoryAgent

class CoordinatorAgent:
    def __init__(self):
        self.disease_agent = DiseaseDetectionAgent()
        self.severity_agent = SeverityAgent()
        self.weather_agent = WeatherAgent()
        self.risk_agent = EnvironmentalRiskAgent()
        self.advisory_agent = AdvisoryAgent()
        self.workflow_version = "v1.1"

    def process_image(self, image_path: str, location_input: str = None, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """
        Orchestrates the entire inference pipeline: Disease -> Weather -> Severity -> EnvRisk -> Advisory.
        Handles errors gracefully to ensure partial success.
        """
        start_time = time.time()
        
        response = {
            "timestamp": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "workflow_version": self.workflow_version,
            "status": "success",
            "warnings": [],
            "agent_trace": [],
            "execution_time_ms": 0,
            "prediction": None,
            "weather": None,
            "severity": None,
            "environmental_risk": None,
            "advice": None
        }

        # Validate image
        if not os.path.exists(image_path):
            response["status"] = "error"
            response["warnings"].append(f"Image not found at path: {image_path}")
            response["execution_time_ms"] = int((time.time() - start_time) * 1000)
            return response

        # Step 1: Disease Detection
        try:
            prediction = self.disease_agent.predict(image_path)
            response["prediction"] = prediction
            response["agent_trace"].append("DiseaseDetectionAgent")
            disease_class = prediction["disease"]
        except Exception as e:
            response["status"] = "error"
            response["warnings"].append(f"Disease detection failed: {e}")
            response["execution_time_ms"] = int((time.time() - start_time) * 1000)
            return response
            
        # Step 2: Weather Retrieval
        weather_data = None
        if location_input or (lat and lon):
            try:
                weather_data = self.weather_agent.get_weather(location_input, lat, lon)
                if "error" in weather_data:
                    response["warnings"].append(f"Weather retrieval failed: {weather_data['error']}")
                else:
                    response["weather"] = weather_data
                    response["agent_trace"].append("WeatherAgent")
            except Exception as e:
                response["warnings"].append(f"Weather retrieval failed: {e}")

        # Step 3: Severity Analysis
        severity = None
        try:
            severity = self.severity_agent.analyze_severity(
                image_path=image_path,
                disease_class=disease_class,
                confidence=prediction["confidence"]
            )
            response["severity"] = severity
            response["agent_trace"].append("SeverityAgent")
        except Exception as e:
            response["status"] = "partial_success"
            response["warnings"].append(f"Severity analysis failed: {e}")

        # Step 4: Environmental Risk Analysis
        risk_data = None
        if weather_data and "error" not in weather_data:
            try:
                risk_data = self.risk_agent.assess_risk(disease_class, weather_data)
                response["environmental_risk"] = risk_data
                response["agent_trace"].append("EnvironmentalRiskAgent")
            except Exception as e:
                response["warnings"].append(f"Environmental risk assessment failed: {e}")

        # Step 5: Advisory Generation
        try:
            severity_str = severity["severity"] if severity else "Unknown"
            advice = self.advisory_agent.generate_advice(
                disease_class=disease_class,
                severity=severity_str,
                weather_data=weather_data,
                risk_data=risk_data
            )
            response["advice"] = advice
            response["agent_trace"].append("AdvisoryAgent")
        except Exception as e:
            response["status"] = "partial_success"
            response["warnings"].append(f"Advisory generation failed: {e}")

        response["execution_time_ms"] = int((time.time() - start_time) * 1000)
        return response
