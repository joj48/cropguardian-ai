import os
import time
import datetime
from typing import Dict, Any

try:
    from google.adk import Agent
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False

from agents.adk_workflow.tools import detect_disease_tool, analyze_severity_tool, generate_advice_tool, get_weather_tool, assess_risk_tool
from agents.coordinator_agent.coordinator_agent import CoordinatorAgent

class ADKCoordinatorAgent:
    def __init__(self):
        self.legacy_coordinator = CoordinatorAgent()
        self.workflow_version = "v2.1-adk"
        
        # Define ADK Agents matching the architecture requirements
        if ADK_AVAILABLE:
            self.disease_agent = Agent(
                name="disease_agent",
                model="gemini-2.5-flash",
                instruction="You are a Disease Detection Agent. You must invoke the detect_disease_tool.",
                tools=[detect_disease_tool]
            )
            
            self.weather_agent = Agent(
                name="weather_agent",
                model="gemini-2.5-flash",
                instruction="You are a Weather Agent. You retrieve weather data for farm locations.",
                tools=[get_weather_tool]
            )
            
            self.severity_agent = Agent(
                name="severity_agent",
                model="gemini-2.5-flash",
                instruction="You are a Severity Agent. You assess disease severity based on the disease_class and confidence.",
                tools=[analyze_severity_tool]
            )
            
            self.risk_agent = Agent(
                name="risk_agent",
                model="gemini-2.5-flash",
                instruction="You are an Environmental Risk Agent. You assess the likelihood of disease spread based on weather data.",
                tools=[assess_risk_tool]
            )
            
            self.advisory_agent = Agent(
                name="advisory_agent",
                model="gemini-2.5-flash",
                instruction="You are an Advisory Agent. You generate agricultural advice based on disease_class and severity.",
                tools=[generate_advice_tool]
            )

    def process_image(self, image_path: str, location_input: str = None, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """
        Executes the ADK multi-agent workflow.
        If ADK is unavailable or fails, implements a mandatory fallback to the legacy CoordinatorAgent.
        """
        start_time = time.time()
        
        response = {
            "timestamp": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "workflow_version": self.workflow_version,
            "workflow_engine": "google_adk",
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

        # Mandatory Fallback 1: ADK or Gemini unavailable
        if not ADK_AVAILABLE or not os.getenv("GEMINI_API_KEY"):
            print("ADK Workflow unavailable. Executing mandatory fallback to Legacy Coordinator.")
            legacy_resp = self.legacy_coordinator.process_image(image_path, location_input, lat, lon)
            legacy_resp["warnings"].append("ADK Workflow unavailable. Fallback to Legacy Coordinator executed.")
            return legacy_resp

        try:
            # 1. Disease Agent Execution
            response["agent_trace"].append("DiseaseAgent")
            prediction_result = detect_disease_tool(image_path)
            if "error" in prediction_result:
                raise Exception(f"Disease detection failed: {prediction_result['error']}")
            
            response["prediction"] = prediction_result
            disease_class = prediction_result["disease"]
            confidence = prediction_result["confidence"]

            # 2. Weather Agent Execution
            weather_data = None
            if location_input or (lat and lon):
                response["agent_trace"].append("WeatherAgent")
                weather_data = get_weather_tool(location_input, lat, lon)
                if "error" in weather_data:
                    response["warnings"].append(f"Weather retrieval failed: {weather_data['error']}")
                else:
                    response["weather"] = weather_data

            # 3. Severity Agent Execution
            response["agent_trace"].append("SeverityAgent")
            severity_result = analyze_severity_tool(image_path, disease_class, confidence)
            if "error" in severity_result:
                response["status"] = "partial_success"
                response["warnings"].append(f"Severity analysis failed: {severity_result['error']}")
            else:
                response["severity"] = severity_result

            # 4. Environmental Risk Agent Execution
            risk_data = None
            if weather_data and "error" not in weather_data:
                response["agent_trace"].append("EnvironmentalRiskAgent")
                risk_data = assess_risk_tool(disease_class, weather_data)
                if "error" in risk_data:
                    response["warnings"].append(f"Risk assessment failed: {risk_data['error']}")
                else:
                    response["environmental_risk"] = risk_data

            # 5. Advisory Agent Execution
            response["agent_trace"].append("AdvisoryAgent")
            severity_str = severity_result.get("severity", "Unknown") if severity_result and "error" not in severity_result else "Unknown"
            advice_result = generate_advice_tool(disease_class, severity_str, weather_data, risk_data)
            if "error" in advice_result:
                response["status"] = "partial_success"
                response["warnings"].append(f"Advisory generation failed: {advice_result['error']}")
            else:
                response["advice"] = advice_result
                
            response["execution_time_ms"] = int((time.time() - start_time) * 1000)
            return response
            
        except Exception as e:
            # Mandatory Fallback 2: Pipeline execution failure
            print(f"ADK Workflow execution failed: {e}. Executing mandatory fallback.")
            legacy_resp = self.legacy_coordinator.process_image(image_path, location_input, lat, lon)
            legacy_resp["warnings"].append(f"ADK Workflow failed ({e}). Fallback to Legacy Coordinator executed.")
            return legacy_resp
