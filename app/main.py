import os
import sys

# Add project root and app directory to sys.path so imports resolve correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
app_dir = os.path.abspath(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

import streamlit as st
from dotenv import load_dotenv
from src.utils.logger import log_environment_snapshot, cleanup_temp_files
from src.services.knowledge_base.kb_manager import KnowledgeBaseManager

# Import UI modular components
from ui import init_page, render_header, render_footer, render_status_panel

load_dotenv()

# Initialize Page (Sets config, session states, styles, and renders sidebar)
init_page(title="CropGuardian AI", icon="🌿")

# Log Environment on startup and cleanup temp files
log_environment_snapshot()
cleanup_temp_files(max_age_hours=24)

# Initialize and validate Knowledge Base on application startup
if "kb_manager" not in st.session_state:
    try:
        st.session_state["kb_manager"] = KnowledgeBaseManager(validate_on_startup=True)
    except Exception as e:
        st.error(f"Critical Error: Failed to initialize Knowledge Base. {e}")
        st.stop()

# ─── Hero Section & Dynamic Metrics Status Cards & Telemetry Expanders ──────
render_header(title="🌱 CropGuardian AI", subtitle="Instant Crop Disease Diagnosis & Farmer Advisory System", show_metrics=True)

# ─── How It Works ─────────────────────────────────────────────────────────────
st.markdown("### How It Works")

steps = [
    ("📷", "Upload Image", "Upload a crop leaf image (JPG or PNG) to begin diagnostic inference."),
    ("🤖", "AI Detection", "MobileNetV2 classifies the disease across 38 crop-disease classes with confidence scoring."),
    ("🌤", "Weather Metrics", "Real-time weather parameters are fetched dynamically for your farm via Open-Meteo."),
    ("⚠️", "Risk Evaluation", "Fungal, bacterial, and heat-stress likelihood is assessed under environment conditions."),
    ("💊", "Gemini Advisory", "Gemini generates custom treatment schedules, nutrition, and recovery indicators."),
]

cols = st.columns(5, gap="medium")
for col, (icon, title, desc) in zip(cols, steps):
    with col:
        with st.container(border=True):
            st.markdown(f'<div class="cg-step-icon">{icon}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="cg-step-title">**{title}**</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="cg-step-desc">{desc}</div>', unsafe_allow_html=True)

st.divider()

# ─── Key Stats ────────────────────────────────────────────────────────────────
st.markdown("### Platform Capabilities")

sc1, sc2, sc3, sc4 = st.columns(4)
with sc1:
    with st.container(border=True):
        st.markdown('<div class="cg-stat-num">38</div><div class="cg-stat-lbl">Disease Classes</div>', unsafe_allow_html=True)
with sc2:
    with st.container(border=True):
        st.markdown('<div class="cg-stat-num">14</div><div class="cg-stat-lbl">Crop Species</div>', unsafe_allow_html=True)
with sc3:
    with st.container(border=True):
        st.markdown('<div class="cg-stat-num">5</div><div class="cg-stat-lbl">AI Agents</div>', unsafe_allow_html=True)
with sc4:
    with st.container(border=True):
        st.markdown('<div class="cg-stat-num">2</div><div class="cg-stat-lbl">Orchestrators</div>', unsafe_allow_html=True)

st.divider()

# ─── Architecture & Status Panel ──────────────────────────────────────────────
col_arch1, col_arch2 = st.columns([2, 1], gap="large")
with col_arch1:
    st.markdown("### Multi-Agent Pipeline Orchestration")
    st.markdown("""
    The system runs a **sequential multi-agent pipeline** orchestrated by either the
    **Google ADK Workflow** (Gemini-powered agents) or the **Legacy Coordinator** (deterministic Python).

    Both engines produce identical output schemas. The ADK engine automatically falls back to
    the Legacy Coordinator if the Gemini API is unavailable — ensuring zero downtime.
    """)
    st.page_link("pages/1_Disease_Detection.py", label="→ Go to Disease Detection", icon="🔍")

with col_arch2:
    with st.container(border=True):
        st.markdown("**Pipeline Trace Order**")
        for step in ["DiseaseDetectionAgent", "WeatherAgent", "SeverityAgent", "EnvironmentalRiskAgent", "AdvisoryAgent"]:
            st.markdown(f"- `{step}`")

# ─── Footer ───────────────────────────────────────────────────────────────────
render_footer()
