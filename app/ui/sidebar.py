# sidebar.py — Unified CropGuardian AI Sidebar Navigation
import streamlit as st
from config.constants import APP_VERSION

def render_sidebar():
    """Renders the common sidebar layout across all pages."""
    with st.sidebar:
        # Branding
        st.markdown(f"### 🌿 CropGuardian AI")
        st.caption(f"Agricultural Intelligence · {APP_VERSION}")
        st.divider()

        # Navigation Links
        st.markdown("**Navigation**")
        st.page_link("main.py", label="Home", icon="🏠")
        st.page_link("pages/1_Disease_Detection.py", label="Disease Detection", icon="🔍")
        st.page_link("pages/2_Feedback.py", label="Submit Feedback", icon="📝")
        st.page_link("pages/3_History.py", label="Prediction History", icon="📜")
        st.page_link("pages/4_Model_Insights.py", label="Model Insights", icon="📊")

        st.divider()

        # Developer Mode Toggle
        st.markdown("**🛠️ Controls**")
        st.session_state["dev_mode"] = st.toggle(
            "Enable Developer Mode", 
            value=st.session_state.get("dev_mode", False)
        )
