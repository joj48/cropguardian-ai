import os
import sys
import json
import datetime
import streamlit as st
from dotenv import load_dotenv

# Ensure root and app directories are in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

load_dotenv()

# Imports from project
from agents.advisory_agent.advisory_agent import AdvisoryAgent
from ui import init_page, render_header, render_footer

# Initialize Page (Page Config, Sidebar Navigation, Theme CSS)
init_page(title="CropGuardian AI Assistant", icon="🌿")

@st.cache_resource
def get_advisory_agent():
    return AdvisoryAgent()

# Guard: Ensure active diagnosis context exists
if "chat_context" not in st.session_state or not st.session_state["chat_context"]:
    st.markdown("")
    st.warning("🌿 No active diagnosis found in the session. Please upload and analyze a crop image first.")
    if st.button("Go to Disease Detection", type="primary"):
        st.switch_page("pages/1_Disease_Detection.py")
    render_footer()
    st.stop()

# Retrieve active context
context = st.session_state["chat_context"]
crop = context.get("crop", "Unknown")
disease = context.get("disease", "Unknown")
if not crop or crop == "Unknown":
    from app.utils.crop_utils import infer_crop_from_disease
    crop = infer_crop_from_disease(disease)

from src.utils.logger import get_logger
logger = get_logger("chat_assistant", "chat_assistant.log")
logger.debug(f"Chat context crop: {st.session_state['chat_context'].get('crop')}")

disease_id = context.get("disease_id", "Unknown")
severity = context.get("severity", "Unknown")
weather = context.get("weather", {})
kb_summary = context.get("knowledge_summary", {})

# Initialize message history list
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

# Sidebar Chat Settings
with st.sidebar:
    st.markdown("**⚙️ Chat Settings**")
    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = "gemini-2.5-flash"

    model_options = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"]
    selected_model = st.sidebar.selectbox(
        "Select AI Model",
        model_options,
        index=model_options.index(st.session_state["selected_model"])
    )
    st.session_state["selected_model"] = selected_model

    # Quick action button: Reset chat
    if st.sidebar.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state["chat_messages"] = []
        st.toast("🗑️ Chat history cleared!")
        st.rerun()

    st.divider()
    st.markdown(
        "💬 **Context Awareness:** The chatbot automatically knows your crop "
        "type, weather conditions, severity score, and treatment options from the "
        "active diagnosis."
    )

# Page Header
render_header("💬 CropGuardian Assistant", "Ask follow-up questions about disease recovery, chemical dosages, organic remedies, or weather-aware spraying.")

# ─── Current Diagnosis Summary Card ───────────────────────────────────────────
st.markdown("<div class='cg-section-label'>Active Diagnosis Context</div>", unsafe_allow_html=True)
model_display_names = {
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini-1.5-flash": "Gemini 1.5 Flash"
}

with st.container(border=True):
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"**Crop**  \n`{crop}`")
    with col2:
        formatted_disease = disease.replace("_", " ").title()
        st.markdown(f"**Disease**  \n`{formatted_disease}`")
    with col3:
        st.markdown(f"**Severity**  \n`{severity}`")
    with col4:
        model_display = model_display_names.get(selected_model, selected_model)
        st.markdown(f"**Model**  \n`{model_display}`")
    with col5:
        if weather:
            w_text = f"{weather.get('temperature', '—')}°C, {weather.get('humidity', '—')}% RH"
        else:
            w_text = "Unavailable"
        st.markdown(f"**Weather**  \n`{w_text}`")

st.divider()

# ─── Chat History ─────────────────────────────────────────────────────────────
for message in st.session_state["chat_messages"]:
    role = message["role"]
    avatar = "🤖" if role == "model" else "🧑‍🌾"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

# Formulate system instruction based on compact context
weather_summary = f"{weather.get('temperature')}°C, {weather.get('humidity')}% Humidity, {weather.get('precipitation')}mm precipitation" if weather else "Unavailable"
compact_kb_str = json.dumps(kb_summary, indent=2) if kb_summary else "No additional scientific info loaded."

system_instruction_text = f"""
You are CropGuardian AI, a context-aware agricultural AI advisory assistant.
You are helping a farmer with the following active diagnosis:
- Crop: {crop}
- Disease: {disease} (ID: {disease_id})
- Severity: {severity}
- Weather: {weather_summary}

Knowledge Base Reference Details:
{compact_kb_str}

Farmer Advisory Guidelines:
1. Provide concise, practical, and highly actionable advice tailored specifically to the diagnosed crop, disease, severity, and current weather.
2. If weather conditions are bad (e.g. rain forecasted, high humidity, extreme temperatures), warn the farmer if they should delay chemical spraying or take protective actions.
3. Offer treatment options including chemical, biological, and organic methods based on the knowledge base.
4. Keep a helpful, empathetic, and professional tone suitable for supporting farmers.
5. Answer follow-up questions directly using this context. Do not offer advice unrelated to agriculture or this crop/disease context unless asked to compare with similar crop issues.
"""

# ─── Chat Input ───────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about crop diseases, treatments, or weather risks..."):
    # Display user input bubble
    with st.chat_message("user", avatar="🧑‍🌾"):
        st.markdown(prompt)
    
    # Save user message to history
    st.session_state["chat_messages"].append({"role": "user", "content": prompt})

    # Prepare client and contents for Gemini
    advisory_agent = get_advisory_agent()
    
    if not advisory_agent or not advisory_agent.client:
        st.error("Gemini client is not initialized. Please verify your GEMINI_API_KEY environment variable.")
        st.stop()
        
    client = advisory_agent.client

    # Formulate contents array (sliding window: last 10 messages)
    contents = []
    recent_messages = st.session_state["chat_messages"][-10:]
    
    for msg in recent_messages:
        role = "user" if msg["role"] == "user" else "model"
        try:
            from google.genai import types
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )
        except ImportError:
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

    # Query Gemini model
    with st.spinner("CropGuardian AI is thinking..."):
        try:
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=system_instruction_text,
                temperature=0.4
            )
            
            response = client.models.generate_content(
                model=selected_model,
                contents=contents,
                config=config
            )
            
            assistant_response = response.text
            
            # Save assistant message to history
            st.session_state["chat_messages"].append({"role": "model", "content": assistant_response})
            st.rerun()

        except Exception as e:
            st.error(f"⚠️ CropGuardian AI encountered an error: {e}")
            st.info("Your message and chat history have been preserved. You can try sending your question again.")

render_footer()
