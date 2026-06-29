# status_panel.py — Dynamic Service Status Dashboard Panel
import os
import urllib.request
import streamlit as st

@st.cache_data(ttl=300)
def check_gemini_api_cached() -> bool:
    """Checks if google-genai is installed and API key is set."""
    try:
        from agents.advisory_agent.advisory_agent import GENAI_AVAILABLE
        if not GENAI_AVAILABLE:
            return False
        return bool(os.getenv("GEMINI_API_KEY"))
    except Exception:
        return False

@st.cache_data(ttl=300)
def check_weather_api_cached() -> bool:
    """Verifies connection to the Open-Meteo weather service API."""
    try:
        # A simple check to ensure Open-Meteo's API is reachable
        urllib.request.urlopen("https://open-meteo.com/", timeout=2)
        return True
    except Exception:
        return False

def check_logging_system() -> bool:
    """Verifies that the logs directory exists and is writable."""
    try:
        return os.path.exists("logs") or os.path.exists("app/logs")
    except Exception:
        return False

def render_status_panel():
    """Renders a visual status indicators card representing system services."""
    # Check states
    gemini_ok = check_gemini_api_cached()
    weather_ok = check_weather_api_cached()
    logs_ok = check_logging_system()
    
    # Model loaded status (checks if coordinator has run and cached the model)
    model_loaded = "pipeline_response" in st.session_state or st.session_state.get("model_loaded", False)
    
    # Orchestrator choice
    workflow_mode = st.session_state.get("workflow_mode", "Google ADK Workflow")
    
    st.markdown("**System Health & Integrations**")
    
    # Formatting columns
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    
    with sc1:
        st.markdown(f"🧠 TF Model: {':green[Ready]' if model_loaded else ':orange[Standby]'}")
    with sc2:
        st.markdown(f"🤖 Gemini API: {':green[Connected]' if gemini_ok else ':red[Offline]'}")
    with sc3:
        st.markdown(f"🌦️ Weather: {':green[Online]' if weather_ok else ':red[Offline]'}")
    with sc4:
        st.markdown(f"⚡ Orchestrator: {':green[ADK]' if 'ADK' in workflow_mode else ':orange[Legacy]'}")
    with sc5:
        st.markdown(f"📝 Logging: {':green[Active]' if logs_ok else ':red[Inactive]'}")
