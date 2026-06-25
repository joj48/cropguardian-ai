import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

# Try to import google-genai
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

load_dotenv()

class AdvisoryAgent:
    def __init__(self):
        """
        Initializes the Advisory Agent.
        Uses google-genai to generate tailored advice based on disease and severity.
        Contains a fallback knowledge base if the API is unavailable.
        """
        self.api_key = os.getenv("GEMINI_API_KEY")
        if GENAI_AVAILABLE and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate_advice(self, disease_class: str, severity: str, weather_data: dict = None, risk_data: dict = None) -> Dict[str, Any]:
        """
        Generates agricultural advice based on the disease, severity, weather, and environmental risk using Gemini.
        """
        try:
            if "healthy" in disease_class.lower():
                return {
                    "disease_description": "The plant appears healthy.",
                    "symptoms": [],
                    "treatment": [],
                    "prevention": ["Maintain current watering and fertilization schedules.", "Monitor plants regularly."],
                    "fertilizer_recommendations": ["Use standard balanced fertilizer based on crop type."],
                    "weather_based_warnings": "None.",
                    "immediate_actions": "None required.",
                    "expert_consultation": "Not necessary at this time.",
                    "source": "Fallback Knowledge Base"
                }

            if not self.api_key:
                print("AdvisoryAgent: GEMINI_API_KEY not found. Using fallback knowledge base.")
                return self._get_fallback_advice(disease_class, severity)

            # Define the desired JSON schema for structured output
            response_schema = {
                "type": "OBJECT",
                "properties": {
                    "disease_description": {"type": "STRING"},
                    "symptoms": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "treatment": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "prevention": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "fertilizer_recommendations": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "weather_based_warnings": {"type": "STRING"},
                    "immediate_actions": {"type": "STRING"},
                    "expert_consultation": {"type": "STRING"},
                    "source": {"type": "STRING"}
                },
                "required": ["disease_description", "symptoms", "treatment", "prevention", "fertilizer_recommendations", "weather_based_warnings", "immediate_actions", "expert_consultation", "source"]
            }

            weather_context = ""
            if weather_data and "weather" in weather_data:
                w = weather_data["weather"]
                weather_context = f"\nCurrent Weather at {weather_data.get('location', 'Unknown')}: {w.get('temperature')}°C, {w.get('humidity')}% Humidity, {w.get('precipitation')}mm precipitation."
            
            risk_context = ""
            if risk_data:
                risk_context = f"\nEnvironmental Risk: {risk_data.get('overall_risk')} (Spread Probability: {risk_data.get('spread_probability')}%)"

            prompt = f"""
            You are an expert agricultural AI. 
            A farmer has uploaded an image of a plant. The system detected:
            - Disease: {disease_class}
            - Current Severity: {severity}
            {weather_context}
            {risk_context}

            Provide a concise, practical, and farmer-focused advisory report. 
            Explain how the current weather impacts the disease (in weather_based_warnings) and what the farmer must do right now (in immediate_actions).
            Return the output in strict JSON format. Set the "source" field to "Gemini 2.5 Flash".
            """
            
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema
                ),
            )
            
            return json.loads(response.text)
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._get_fallback_advice(disease_class, severity)

    def _get_fallback_advice(self, disease_class: str, severity: str) -> Dict[str, Any]:
        """
        Returns hardcoded fallback advice if Gemini is unavailable.
        """
        advice = {
            "disease_description": f"A general fungal or bacterial infection commonly known as {disease_class}.",
            "symptoms": ["Leaf spotting", "Discoloration", "Wilting"],
            "treatment": ["Remove infected leaves immediately.", "Apply appropriate broad-spectrum fungicide."],
            "prevention": ["Ensure proper spacing for air circulation.", "Avoid overhead watering to keep leaves dry."],
            "fertilizer_recommendations": ["Avoid excessive nitrogen which promotes lush, susceptible growth."],
            "weather_based_warnings": "Consider adjusting watering if humidity or rain is high.",
            "immediate_actions": "Monitor crop closely.",
            "expert_consultation": "Consult a local agronomist if symptoms persist after 2 weeks.",
            "source": "Fallback Knowledge Base"
        }
        
        if severity == "High":
            advice["treatment"].append("Consider destroying the heavily infected plant to save the rest of the crop.")
            advice["immediate_actions"] = "Isolate infected area immediately."
            advice["expert_consultation"] = "Consult a professional immediately due to high severity."
            
        return advice
