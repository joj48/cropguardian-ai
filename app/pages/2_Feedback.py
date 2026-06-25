import os
import sys
import datetime
import streamlit as st

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents.feedback_agent.feedback_agent import FeedbackAgent
from agents.disease_detection_agent.disease_detection_agent import DiseaseDetectionAgent

st.set_page_config(page_title="Feedback Submission", page_icon="📝")

@st.cache_resource
def get_agents():
    return FeedbackAgent(), DiseaseDetectionAgent()

feedback_agent, disease_agent = get_agents()

st.title("📝 Feedback Submission")
st.markdown("Manually submit a correction to improve the model.")

uploaded_file = st.file_uploader("Upload misclassified image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Image to correct", width=300)
    
    # Save temporarily
    temp_img_path = f"temp_feedback_{uploaded_file.name}"
    with open(temp_img_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    predicted_class = st.selectbox("What did the model predict? (If known)", ["Unknown"] + list(disease_agent.class_names))
    actual_class = st.selectbox("What is the Actual Disease Class?", disease_agent.class_names)
    
    confidence = st.number_input("Confidence (If known)", min_value=0.0, max_value=100.0, value=0.0)
    
    if st.button("Submit Feedback", type="primary"):
        success = feedback_agent.log_feedback(
            original_image_path=temp_img_path,
            predicted_class=predicted_class,
            actual_class=actual_class,
            confidence=confidence,
            timestamp=datetime.datetime.now().replace(microsecond=0).isoformat(),
            model_version=disease_agent.model_version
        )
        if success:
            st.success("Feedback submitted! Image preserved for retraining.")
        else:
            st.error("This image has already been submitted.")
