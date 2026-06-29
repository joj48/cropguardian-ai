import os
import sys
import csv
import datetime
import uuid
import json
import streamlit as st
from PIL import Image

# Ensure project root and app directory are in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Backend Imports
from agents.coordinator_agent.coordinator_agent import CoordinatorAgent
from agents.adk_workflow.adk_coordinator import ADKCoordinatorAgent
from agents.feedback_agent.feedback_agent import FeedbackAgent
from src.utils.logger import (
    pipeline_run_id_var, 
    correlation_id_var, 
    RESPONSES_DIR, 
    append_to_manifest, 
    get_logger,
    log_config_snapshot
)

ui_logger = get_logger("ui", "uploaded_images.log")

# Import modular UI elements
from ui import (
    init_page,
    render_header,
    render_footer,
    render_prediction_card,
    render_top_predictions_chart,
    render_weather_card,
    render_advisory_section,
    format_disease_name,
    is_healthy
)

# Initialize Page (Page Config, Navigation Sidebar, CSS)
init_page(title="Disease Detection", icon="🔍")

# ─── Cached Agent Initialisation ──────────────────────────────────────────────
@st.cache_resource
def get_coordinator_agent():
    return CoordinatorAgent()

@st.cache_resource
def get_adk_coordinator_agent():
    return ADKCoordinatorAgent()

@st.cache_resource
def get_feedback_agent():
    return FeedbackAgent()

@st.cache_data
def get_class_names() -> list:
    import numpy as np
    return list(np.load("models/class_names.npy", allow_pickle=True))

# ─── History Logger ───────────────────────────────────────────────────────────
def log_prediction_history(result: dict, img_name: str):
    history_dir = "data/history"
    os.makedirs(history_dir, exist_ok=True)
    csv_path = os.path.join(history_dir, "prediction_log.csv")
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["timestamp", "image_name", "predicted_class",
                      "confidence", "confidence_level", "model_version"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": result["timestamp"],
            "image_name": img_name,
            "predicted_class": result["disease"],
            "confidence": result["confidence"],
            "confidence_level": result["confidence_level"],
            "model_version": result["model_version"],
        })

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Page-Specific Settings
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("**⚙️ Settings**")
    workflow_mode = st.radio(
        "Orchestration Engine",
        ("Google ADK Workflow", "Legacy Coordinator"),
        help="ADK uses Gemini-powered agents. Falls back to Legacy Coordinator automatically if Gemini API is unavailable.",
    )
    st.session_state["workflow_mode"] = workflow_mode
    st.caption(
        "**ADK:** Gemini 2.5 Flash agents with tool calling.\n\n"
        "**Legacy:** Deterministic Python orchestration."
    )

    st.divider()
    st.markdown("**📍 Location Tips**")
    st.caption(
        "Providing your farm location unlocks:\n"
        "- Real-time weather data\n"
        "- Environmental disease risk\n"
        "- Weather-aware Gemini advice"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ═══════════════════════════════════════════════════════════════════════════════
render_header(title="🔍 Disease Detection", subtitle="Upload a crop image and specify your farm location to execute a complete multi-agent advisory run.")

# ═══════════════════════════════════════════════════════════════════════════════
# TOP ROW — INPUTS, PREVIEW & PREDICTION SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
input_col, summary_col = st.columns([5, 5], gap="large")

with input_col:
    st.markdown("<div class='cg-section-label'>Crop Image Upload</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload crop leaf image",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
    )
    
    # Render Image Preview (Persist or file upload)
    preview_img_path = None
    if uploaded_file:
        st.image(uploaded_file, width=280, caption=f"Uploaded: {uploaded_file.name}")
    elif st.session_state.get("uploaded_img_path") and os.path.exists(st.session_state["uploaded_img_path"]):
        preview_img_path = st.session_state["uploaded_img_path"]
        st.image(preview_img_path, width=280, caption=f"Loaded from active session")

    # Farm Location Form
    st.markdown("<div class='cg-section-label' style='margin-top:16px;'>Farm Location (Optional)</div>", unsafe_allow_html=True)
    location_mode = st.radio(
        "Input method",
        ["City / State / Country", "Latitude + Longitude"],
        horizontal=True,
        label_visibility="collapsed",
    )

    location_input = None
    lat = lon = None

    if location_mode == "City / State / Country":
        location_input = st.text_input(
            "Location",
            placeholder="e.g. Cherthala, Kerala, India",
            label_visibility="collapsed",
        )
    else:
        la_col, lo_col = st.columns(2)
        with la_col:
            lat_raw = st.text_input("Latitude", placeholder="e.g. 9.68")
        with lo_col:
            lon_raw = st.text_input("Longitude", placeholder="e.g. 76.33")
        if lat_raw and lon_raw:
            try:
                lat = float(lat_raw)
                lon = float(lon_raw)
            except ValueError:
                st.error("Latitude and Longitude must be valid numbers.")

# Run button triggering execution
analyze_btn = False
if uploaded_file:
    st.markdown("")
    analyze_btn = st.button("🔬 Analyze Crop Disease", type="primary", use_container_width=True)

with summary_col:
    # If prediction exists, render the Prediction summary card
    if not analyze_btn and st.session_state.get("pipeline_response"):
        response = st.session_state["pipeline_response"]
        result = response.get("prediction") or {}
        _env = response.get("environment") or {}
        severity_res = _env.get("severity") or {}
        risk_data = _env.get("risk") or {}
        
        st.markdown("<div class='cg-section-label'>Active Prediction Summary</div>", unsafe_allow_html=True)
        render_prediction_card(result, severity_res, risk_data)
    elif not analyze_btn:
        # Show Rich Empty State card
        st.markdown("<div class='cg-section-label'>Diagnosis Status</div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### 🌿 Begin Diagnosis")
            st.markdown("""
            Provide a photograph of the affected crop leaf to execute multi-agent diagnostics.
            
            **Supported formats:**
            - • JPG
            - • JPEG
            - • PNG
            
            **Maximum size:**
            - 10 MB
            """)

# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE EXECUTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
if analyze_btn and uploaded_file:
    # Generate correlation IDs
    run_id = str(uuid.uuid4())
    corr_id = str(uuid.uuid4())
    
    # Store image file
    uploads_dir = os.path.join("temp", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_img_path = os.path.join(uploads_dir, f"{timestamp_str}_{run_id[:8]}_{uploaded_file.name}")
    
    with open(temp_img_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    file_size_kb = os.path.getsize(temp_img_path) / 1024
    try:
        with Image.open(temp_img_path) as img:
            width, height = img.size
    except Exception:
        width, height = 0, 0
        
    abs_path = os.path.abspath(temp_img_path)
    ui_logger.info(
        f"Image Uploaded - {uploaded_file.name} | Size: {file_size_kb:.1f}KB | RunID: {run_id}"
    )

    token1 = pipeline_run_id_var.set(run_id)
    token2 = correlation_id_var.set(corr_id)

    log_config_snapshot(
        workflow_mode=workflow_mode,
        adk_enabled=(workflow_mode == "Google ADK Workflow")
    )

    # Instantiate agents
    _coordinator = get_coordinator_agent()
    _adk_coordinator = get_adk_coordinator_agent()

    # Step-by-Step Multi-agent Timeline inside st.status()
    with st.status("Running CropGuardian Pipeline...", expanded=True) as status_box:
        st.write("🖼️ Image successfully uploaded and stored.")
        
        status_box.update(label="🧠 Classifying Disease Class...", state="running")
        if workflow_mode == "Google ADK Workflow":
            response = _adk_coordinator.process_image(temp_img_path, location_input, lat, lon)
        else:
            response = _coordinator.process_image(temp_img_path, location_input, lat, lon)
        
        # Display executing log timestamps
        diag = response.get("diagnostics") or response
        trace = diag.get("execution_summary", [])
        if trace:
            for item in trace:
                agent = item.get("agent", "UnknownAgent")
                status = item.get("status", "success")
                time_ms = item.get("execution_time_ms", 0)
                st.write(f"⚙️ `{agent}` execution completed: `{status.upper()}` ({time_ms}ms)")
        else:
            st.write("🧠 Disease classified.")
            st.write("🌦️ Environmental conditions evaluated.")
            st.write("⚠️ Threat risks scored.")
            st.write("💊 Recommendations generated.")
            
        status_box.update(label="Analysis Complete", state="complete")
        st.session_state["model_loaded"] = True

    if response.get("diagnostics", {}).get("status") == "error":
        st.error("The analysis pipeline encountered a critical error.")
        for w in response.get("diagnostics", {}).get("warnings", []):
            st.error(f"  ↳ {w}")
    else:
        st.toast("🎉 Prediction completed successfully!")
        st.session_state["pipeline_response"] = response
        st.session_state["uploaded_img_path"] = temp_img_path
        log_prediction_history(response["prediction"], uploaded_file.name)
        
        # Configure Chatbot context
        prediction_data = response.get("prediction", {})
        weather_data = response.get("environment", {}).get("weather", {})
        kb_context = response.get("knowledge", {}).get("context") or {}
        
        kb_summary = {}
        if kb_context:
            overview = kb_context.get("overview", {})
            overview_desc = overview.get("description", "") if isinstance(overview, dict) else str(overview)
            kb_summary = {
                "overview": overview_desc,
                "symptoms": kb_context.get("symptoms", {}),
                "treatment": kb_context.get("treatment", {}),
                "prevention": kb_context.get("prevention", {}),
                "immediate_actions": kb_context.get("immediate_actions", {}),
                "weather_influence": kb_context.get("weather_influence", {})
            }
        
        old_context = st.session_state.get("chat_context", {})
        old_run_id = old_context.get("run_id")
        
        st.session_state["chat_context"] = {
            "run_id": run_id,
            "crop": prediction_data.get("crop", "Unknown"),
            "disease": prediction_data.get("disease", "Unknown"),
            "disease_id": kb_context.get("disease_id", "Unknown") if kb_context else "Unknown",
            "severity": response.get("environment", {}).get("severity", {}).get("severity", "Unknown"),
            "weather": weather_data.get("weather", {}) if weather_data else {},
            "knowledge_summary": kb_summary
        }
        ui_logger.debug(f"Chat context crop: {st.session_state['chat_context'].get('crop')}")
        
        if old_run_id != run_id:
            st.session_state["chat_messages"] = []
        
        resp_filename = f"{run_id}_response.json"
        resp_path = os.path.join(RESPONSES_DIR, resp_filename)
        with open(resp_path, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2)
            
        append_to_manifest(
            run_id=run_id,
            session_id=st.session_state.get("session_id", "unknown"),
            workflow=workflow_mode,
            start_time=response.get("timestamp"),
            end_time=datetime.datetime.now().replace(microsecond=0).isoformat(),
            status=response.get("status"),
            original_image=uploaded_file.name,
            stored_image=temp_img_path
        )
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# BOTTOM ROW — TABS
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.get("pipeline_response"):
    response = st.session_state["pipeline_response"]
    result = response.get("prediction") or {}
    _env = response.get("environment") or {}
    _knowledge = response.get("knowledge") or {}
    _ai = response.get("ai") or {}
    _diag = response.get("diagnostics") or response

    knowledge_ctx = _knowledge.get("context")
    advice_res = _ai.get("advice") or response.get("advice") or {}
    weather_data = _env.get("weather") or response.get("weather")
    risk_data = _env.get("risk") or response.get("environmental_risk")
    severity_res = _env.get("severity") or {}

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    
    # Standard Native tab items
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Prediction Metrics", 
        "🌦️ Weather & Environment", 
        "💊 Treatment & Prevention", 
        "🛠️ Technical Diagnostics"
    ])

    with tab1:
        # Chart and predictions
        render_top_predictions_chart(result)

    with tab2:
        # Weather parameters & Risk Assessment
        render_weather_card(weather_data, risk_data)

    with tab3:
        # Advisory scientific knowledge + Gemini advices
        render_advisory_section(knowledge_ctx, advice_res)
        
        # Follow-up Chatbot redirection
        st.markdown("")
        st.divider()
        c_ask1, c_ask2 = st.columns([3, 1])
        with c_ask1:
            st.markdown("##### 🌿 Have follow-up questions about this diagnosis?")
            st.caption("Ask our context-aware chatbot about chemical dosages, organic remedies, or weather risks.")
        with c_ask2:
            if st.button("💬 Chat with CropGuardian", type="primary", use_container_width=True):
                st.switch_page("pages/5_CropGuardian_AI_Assistant.py")

    with tab4:
        # Diagnostics details
        st.markdown("#### Execution Summary Diagnostics")
        
        dc1, dc2, dc3 = st.columns(3)
        dc1.metric("Status", _diag.get("status", "Success").upper())
        dc2.metric("Execution Time", f"{_diag.get('execution_time_ms', 0)} ms")
        dc3.metric("Engine Version", _diag.get("workflow_version", "1.0"))
        
        st.markdown("**Full JSON Telemetry**")
        st.json(response)

        # Feedback loop
        st.divider()
        st.markdown("#### Feedback loop")
        with st.expander("Submit correction if prediction is inaccurate"):
            st.markdown("Your feedback retrains the MobileNetV2 model to avoid misclassifications.")
            fb_yes, fb_no = st.columns(2)
            with fb_yes:
                if st.button("✅ Prediction was Correct", key="fb_yes"):
                    st.success("Feedback saved. Thank you!")
            with fb_no:
                if st.button("❌ Needs Correction", key="fb_no"):
                    st.session_state["show_feedback_form"] = True
                    
            if st.session_state.get("show_feedback_form"):
                class_names = get_class_names()
                actual_class = st.selectbox("Select correct classification label", class_names)
                if st.button("Submit correction report", type="primary"):
                    f_agent = get_feedback_agent()
                    logged = f_agent.log_feedback(
                        original_image_path=st.session_state["uploaded_img_path"],
                        predicted_class=result.get("disease"),
                        actual_class=actual_class,
                        confidence=result.get("confidence", 0),
                        timestamp=datetime.datetime.now().replace(microsecond=0).isoformat(),
                        model_version=result.get("model_version", "v1")
                    )
                    if logged:
                        st.success("Feedback submitted. Image logged for retraining.")
                        st.session_state["show_feedback_form"] = False
                    else:
                        st.warning("Duplicate feedback detected.")

render_footer()
