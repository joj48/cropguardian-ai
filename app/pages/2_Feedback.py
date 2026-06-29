import os
import sys
import datetime
import streamlit as st

# Ensure path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.feedback_agent.feedback_agent import FeedbackAgent
from agents.disease_detection_agent.disease_detection_agent import DiseaseDetectionAgent
from ui import init_page, render_header, render_footer

# Initialize Page (Sets config, sidebars, styles)
init_page(title="Submit Feedback", icon="📝")

@st.cache_resource
def get_agents():
    return FeedbackAgent(), DiseaseDetectionAgent()

feedback_agent, disease_agent = get_agents()

# ─── Sidebar Page-Specific Advice ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("**📝 Feedback Submission**")
    st.caption(
        "Use this form to submit misclassification reports. "
        "Each submission preserves the image and label for model fine-tuning."
    )
    st.divider()
    st.markdown("**ℹ️ Details**")
    st.caption(
        "- Compiles a database of edge cases.\n"
        "- Protects against duplicate requests via image hashing."
    )

# Header Section
render_header("📝 Submit Feedback", "Provide manual feedback for misclassifications to train and fine-tune future model weights.")

# Main Form Layout
upload_col, form_col = st.columns([2, 3], gap="large")
temp_img_path = None

with upload_col:
    st.markdown("<div class='cg-section-label'>Misclassified Image</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload the misclassified image",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
    )
    if uploaded_file:
        st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
        temp_img_path = f"temp_feedback_{uploaded_file.name}"
        with open(temp_img_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

with form_col:
    st.markdown("<div class='cg-section-label'>Feedback Details</div>", unsafe_allow_html=True)

    if uploaded_file:
        predicted_class = st.selectbox(
            "What did the model predict? (leave as 'Unknown' if unsure)",
            ["Unknown"] + list(disease_agent.class_names),
        )
        actual_class = st.selectbox(
            "What is the correct disease class?",
            disease_agent.class_names,
        )
        confidence = st.number_input(
            "Model confidence at prediction time (% — leave at 0 if unknown)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.5,
        )
        st.markdown("")

        if st.button("Submit Correction Report", type="primary", use_container_width=True):
            if temp_img_path and os.path.exists(temp_img_path):
                success = feedback_agent.log_feedback(
                    original_image_path=temp_img_path,
                    predicted_class=predicted_class,
                    actual_class=actual_class,
                    confidence=confidence,
                    timestamp=datetime.datetime.now().replace(microsecond=0).isoformat(),
                    model_version=disease_agent.model_version,
                )
                if success:
                    st.toast("🎉 Feedback submitted successfully!")
                    st.success(
                        "Feedback logged. The image and label have been saved to the retraining dataset."
                    )
                else:
                    st.warning("This image has already been submitted (matching md5 hash).")
                
                # Cleanup temp feedback file
                try:
                    os.remove(temp_img_path)
                except Exception:
                    pass
            else:
                st.error("Could not process the uploaded file. Please try again.")
    else:
        with st.container(border=True):
            st.markdown("### 👈 Upload Image to Start")
            st.caption("Upload the crop leaf image that was misclassified to begin filling out details.")

render_footer()
