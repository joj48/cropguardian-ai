# page_init.py — Global Page Config & Session State Persistence Manager
import streamlit as st
from config.constants import SESSION_DEFAULTS
from ui.styles import inject_css
from ui.sidebar import render_sidebar

def init_page(title: str, icon: str):
    """
    Standardizes page configurations, themes, stylesheets, 
    sidebar layouts, and session state persistence variables.
    """
    # 1. Set Page Configuration
    st.set_page_config(
        page_title=f"{title} | CropGuardian AI",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 2. Session State Persistence
    for key, value in SESSION_DEFAULTS.items():
        st.session_state.setdefault(key, value)

    # 3. Inject CSS Theme styling overrides
    inject_css()

    # 4. Draw Navigation Sidebar
    render_sidebar()
