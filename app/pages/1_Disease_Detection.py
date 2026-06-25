import os
import sys
import csv
import datetime
import streamlit as st
from PIL import Image

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents.coordinator_agent.coordinator_agent import CoordinatorAgent
from agents.adk_workflow.adk_coordinator import ADKCoordinatorAgent
from agents.feedback_agent.feedback_agent import FeedbackAgent

st.set_page_config(page_title="Disease Detection", page_icon="🔍")

@st.cache_resource
def get_coordinator_agent():
    return CoordinatorAgent()

@st.cache_resource
def get_adk_coordinator_agent():
    return ADKCoordinatorAgent()

@st.cache_resource
def get_feedback_agent():
    return FeedbackAgent()

def log_prediction_history(result, img_name):
    history_dir = "data/history"
    os.makedirs(history_dir, exist_ok=True)
    csv_path = os.path.join(history_dir, "prediction_log.csv")
    
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["timestamp", "image_name", "predicted_class", "confidence", "confidence_level", "model_version"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": result["timestamp"],
            "image_name": img_name,
            "predicted_class": result["disease"],
            "confidence": result["confidence"],
            "confidence_level": result["confidence_level"],
            "model_version": result["model_version"]
        })

st.title("🔍 Disease Detection")

# Initialize agents
coordinator_agent = get_coordinator_agent()
adk_coordinator_agent = get_adk_coordinator_agent()
feedback_agent = get_feedback_agent()

st.sidebar.header("Workflow Settings")
workflow_mode = st.sidebar.radio(
    "Select Orchestration Engine",
    ("Google ADK Workflow", "Legacy Coordinator")
)

st.subheader("Farm Location")
location_mode = st.radio("Input Mode", ["City + State + Country", "Latitude + Longitude"], horizontal=True)

location_input = None
lat = None
lon = None

if location_mode == "City + State + Country":
    location_input = st.text_input("Enter Location (e.g., Cherthala, Kerala, India)")
else:
    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat_input = st.text_input("Latitude")
    with col_lon:
        lon_input = st.text_input("Longitude")
    if lat_input and lon_input:
        try:
            lat = float(lat_input)
            lon = float(lon_input)
        except ValueError:
            st.error("Latitude and Longitude must be valid numbers.")

st.subheader("Image Upload")
uploaded_file = st.file_uploader("Upload a crop leaf image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Preview Image
    st.image(uploaded_file, caption="Image Preview", width=300)
    
    # Save uploaded file temporarily for prediction
    temp_img_path = f"temp_{uploaded_file.name}"
    with open(temp_img_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("Run Prediction", type="primary"):
        with st.spinner("Analyzing image and environmental data..."):
            if workflow_mode == "Google ADK Workflow":
                response = adk_coordinator_agent.process_image(temp_img_path, location_input, lat, lon)
            else:
                response = coordinator_agent.process_image(temp_img_path, location_input, lat, lon)
            
            if response["status"] == "error":
                st.error("Pipeline failed!")
                for warning in response["warnings"]:
                    st.error(warning)
            else:
                # Save to session state so it persists during feedback
                st.session_state["pipeline_response"] = response
                st.session_state["uploaded_img_path"] = temp_img_path
                
                log_prediction_history(response["prediction"], uploaded_file.name)

# Display results if they exist in session state
if "pipeline_response" in st.session_state:
    response = st.session_state["pipeline_response"]
    result = response.get("prediction", {})
    severity_result = response.get("severity", {}) or {}
    advice_result = response.get("advice", {}) or {}
    temp_img_path = st.session_state["uploaded_img_path"]
    
    if response["warnings"]:
        for w in response["warnings"]:
            st.warning(f"Warning: {w}")
    
    st.divider()
    st.subheader("Disease Report")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Disease:** `{result['disease']}`")
        st.markdown(f"**Confidence:** `{result['confidence']}%`")
        
        color = "green" if result["confidence_level"] == "High" else "orange" if result["confidence_level"] == "Medium" else "red"
        st.markdown(f"**Confidence Level:** :{color}[{result['confidence_level']}]")
        
        if "warning" in result:
            st.warning(result["warning"])
            
    with col2:
        st.markdown("**Top 3 Predictions:**")
        for p in result["top_predictions"]:
            st.markdown(f"- {p['class']} ({p['confidence']}%)")

    st.markdown(f"*Prediction Timestamp:* `{result['timestamp']}`")
    
    st.divider()
    st.subheader("Pipeline Diagnostics")
    engine_badge = f"🚀 **{response.get('workflow_engine', 'legacy_coordinator').upper()}**"
    st.caption(f"{engine_badge} | **Status:** {response['status']} | **Time:** {response['execution_time_ms']}ms | **Agents:** {' -> '.join(response.get('agent_trace', []))}")
    
    st.divider()
    st.subheader("Advisory Information")
    
    st.markdown("**Disease Severity**")
    sev_color = "red" if severity_result.get("severity") == "High" else "orange" if severity_result.get("severity") == "Medium" else "green" if severity_result.get("severity") == "Low" else "blue"
    st.markdown(f"- **Severity Level:** :{sev_color}[{severity_result.get('severity', 'Unknown')}]")
    st.markdown(f"- **Assessment Method:** `{severity_result.get('assessment_method', 'Unknown')}`")
    if severity_result.get("details"):
        st.info(severity_result["details"])

    weather_data = response.get("weather")
    risk_data = response.get("environmental_risk")
    
    if weather_data and "error" not in weather_data:
        st.divider()
        st.subheader("Environmental Intelligence")
        w = weather_data.get("weather", {})
        
        st.markdown(f"📍 **Farm Location:** `{weather_data.get('location', 'Unknown')}`")
        w_col1, w_col2, w_col3, w_col4 = st.columns(4)
        w_col1.metric("🌡 Temperature", f"{w.get('temperature', '--')}°C")
        w_col2.metric("💧 Humidity", f"{w.get('humidity', '--')}%")
        w_col3.metric("🌧 Precipitation", f"{w.get('precipitation', '--')}mm")
        w_col4.metric("💨 Wind", f"{w.get('wind_speed', '--')} km/h")

        if risk_data and "error" not in risk_data:
            st.markdown("**Environmental Risk Assessment**")
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                ov_color = "red" if risk_data.get("overall_risk") == "High" else "orange" if risk_data.get("overall_risk") == "Medium" else "green"
                st.markdown(f"- **Overall Risk Level:** :{ov_color}[{risk_data.get('overall_risk', 'Unknown')}]")
                st.markdown(f"- **Fungal Risk:** `{risk_data.get('fungal_risk', 'Unknown')}`")
                st.markdown(f"- **Bacterial Risk:** `{risk_data.get('bacterial_risk', 'Unknown')}`")
            with r_col2:
                st.markdown(f"- **Heat Stress Risk:** `{risk_data.get('heat_stress_risk', 'Unknown')}`")
                st.markdown(f"- **Spread Probability:** `{risk_data.get('spread_probability', 0)}%`")
                st.progress(risk_data.get("spread_probability", 0) / 100)
                
            for reason in risk_data.get("reasons", []):
                st.caption(f"• {reason}")
        
        if advice_result:
            st.divider()
            st.markdown("### Agricultural Recommendations")
            st.caption(f"Source: {advice_result.get('source', 'Unknown')}")
            
            st.markdown("**Description:**")
            st.write(advice_result.get("disease_description", ""))
            
            if advice_result.get("weather_based_warnings"):
                st.warning(f"**Weather Warning:** {advice_result.get('weather_based_warnings')}")
            if advice_result.get("immediate_actions"):
                st.error(f"**Immediate Action Required:** {advice_result.get('immediate_actions')}")
            
            col_adv1, col_adv2 = st.columns(2)
            with col_adv1:
                st.markdown("**Symptoms:**")
                for item in advice_result.get("symptoms", []):
                    st.markdown(f"- {item}")
                
                st.markdown("**Treatment:**")
                for item in advice_result.get("treatment", []):
                    st.markdown(f"- {item}")
                    
            with col_adv2:
                st.markdown("**Prevention:**")
                for item in advice_result.get("prevention", []):
                    st.markdown(f"- {item}")
                    
                st.markdown("**Fertilizer Recommendations:**")
                for item in advice_result.get("fertilizer_recommendations", []):
                    st.markdown(f"- {item}")
                    
            st.markdown("**Expert Consultation:**")
            st.info(advice_result.get("expert_consultation", ""))
    
    st.divider()
    # Inline Feedback Workflow
    st.write("### Was this prediction correct?")
    f_col1, f_col2 = st.columns([1, 10])
    
    with f_col1:
        if st.button("Yes", key="fb_yes"):
            st.success("Thank you for confirming!")
            # Could log positive feedback if needed
            
    with f_col2:
        if st.button("No", key="fb_no"):
            st.session_state["show_feedback_form"] = True

    if st.session_state.get("show_feedback_form"):
        st.warning("Please help us improve the model by selecting the correct disease class.")
        # We need the class names list. Since coordinator abstracts the disease agent,
        # we can fetch it directly from the coordinator's internal agent for the UI.
        class_names = coordinator_agent.disease_agent.class_names
        actual_class = st.selectbox("Actual Disease Class", class_names)
        if st.button("Submit Correction"):
            success = feedback_agent.log_feedback(
                original_image_path=temp_img_path,
                predicted_class=result["disease"],
                actual_class=actual_class,
                confidence=result["confidence"],
                timestamp=datetime.datetime.now().replace(microsecond=0).isoformat(),
                model_version=result["model_version"]
            )
            if success:
                st.success("Feedback submitted successfully! Image preserved for retraining.")
                st.session_state["show_feedback_form"] = False
            else:
                st.error("This image has already been submitted for feedback.")
