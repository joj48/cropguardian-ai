# header.py — CropGuardian AI Hero Header & Telemetry Panels
import os
import sys
import platform
import psutil
import streamlit as st
from ui.status_panel import check_gemini_api_cached, check_weather_api_cached
from config.constants import APP_VERSION, MODEL_VERSION

@st.cache_data(ttl=3600)
def get_dataset_size() -> int:
    """Calculates the total number of images stored recursively under data/."""
    count = 0
    data_dir = "data"
    if os.path.exists(data_dir):
        for _, _, files in os.walk(data_dir):
            count += len(files)
    return count

def render_header(title: str = "CropGuardian AI", subtitle: str = "AI-Powered Crop Disease Detection & Farmer Advisory System", show_metrics: bool = False):
    """Renders the main layout headers, dynamic status cards, and the system telemetry panel."""
    st.markdown(f"""
    <div style="padding: 1rem 0 0.5rem 0;">
        <div style="font-size:0.75rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:var(--primary-color, #2E8B57);margin-bottom:8px;">
            AI-Powered Agricultural Intelligence
        </div>
        <div style="font-size:2.2rem;font-weight:800;letter-spacing:-0.02em;line-height:1.2;margin-bottom:12px;">
            {title}
        </div>
        <div style="font-size:1.0rem;opacity:0.75;max-width:700px;line-height:1.6;margin-bottom:16px;">
            {subtitle}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if show_metrics:
        # Dynamic telemetry status cards
        st.divider()
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        
        # Check services
        model_loaded = "pipeline_response" in st.session_state or st.session_state.get("model_loaded", False)
        gemini_ok = check_gemini_api_cached()
        weather_ok = check_weather_api_cached()
        workflow_mode = st.session_state.get("workflow_mode", "Google ADK Workflow")
        
        with mc1:
            st.metric("Model Status", "✅ Ready" if model_loaded else "💤 Standby")
        with mc2:
            st.metric("Weather API", "Online" if weather_ok else "Offline")
        with mc3:
            st.metric("Gemini API", "Active" if gemini_ok else "Offline")
        with mc4:
            st.metric("Orchestrator", "ADK Engine" if "ADK" in workflow_mode else "Legacy")
        with mc5:
            st.metric("Dataset Size", f"{get_dataset_size():,} images")
            
        st.divider()
        
        # Renders the System Health Telemetry Panel
        with st.expander("🖥️ System Health Telemetry"):
            col_sys1, col_sys2 = st.columns(2)
            with col_sys1:
                st.markdown("**🖥️ Machine Platform Details**")
                st.write(f"- **OS**: `{platform.platform()}`")
                st.write(f"- **Architecture**: `{platform.machine()} ({platform.architecture()[0]})`")
                st.write(f"- **Processor**: `{platform.processor()}`")
                
                # RAM metrics
                ram = psutil.virtual_memory()
                st.write(f"- **RAM (Available/Total)**: `{ram.available / (1024**3):.1f} GB / {ram.total / (1024**3):.1f} GB` ({ram.percent}% used)")
            with col_sys2:
                st.markdown("**📦 Engine & Model Configuration**")
                st.write(f"- **Python Version**: `{sys.version.split()[0]}`")
                
                # Check TensorFlow details
                import tensorflow as tf
                st.write(f"- **TensorFlow Version**: `{tf.__version__}`")
                
                gpus = tf.config.list_physical_devices('GPU')
                st.write(f"- **GPU Hardware**: `{gpus if gpus else 'None (Running on CPU)'}`")
                st.write(f"- **Model Version**: `{MODEL_VERSION}`")
                st.write(f"- **App Version**: `{APP_VERSION}`")
